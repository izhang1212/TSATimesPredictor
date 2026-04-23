# ensemble.py - blends LightGBM and Prophet predictions into a single forecast

import os
import json

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import holidays

from config import (
    FEATURES,
    STAFFING_MODIFIERS,
    SHUTDOWN_PERIODS,
    WAIT_TIME_TIERS,
)
from models.lightgbm_model import load_model as load_lgb_model, predict as lgb_predict
from models.prophet_model import load_models as load_prophet_models, predict as prophet_predict

TRAINING_DATA_PATH = "data/exports/training_data_final.csv"
LGB_METRICS_PATH = "models/saved/lightgbm_metrics.json"
PROPHET_METRICS_PATH = "models/saved/prophet_metrics.json"
WEIGHTS_PATH = "models/saved/ensemble_weights.json"

# Weight computation
def compute_weights(lgb_mae, prophet_mae):
    """
    Weights are inverse to error — more accurate model gets more weight.
    If one model's MAE is much lower, it dominates the ensemble.
    """
    lgb_w = 1.0 / max(lgb_mae, 0.01)
    prophet_w = 1.0 / max(prophet_mae, 0.01)
    total = lgb_w + prophet_w
    return {"lightgbm": lgb_w / total, "prophet": prophet_w / total}


def load_or_compute_weights():
    """Load cached weights if they exist, otherwise compute from saved metrics."""
    if os.path.exists(WEIGHTS_PATH):
        with open(WEIGHTS_PATH) as f:
            return json.load(f)

    with open(LGB_METRICS_PATH) as f:
        lgb_metrics = json.load(f)
    with open(PROPHET_METRICS_PATH) as f:
        prophet_metrics = json.load(f)

    lgb_mae = lgb_metrics["mae"]
    prophet_mae = prophet_metrics["overall"]["mae"]
    weights = compute_weights(lgb_mae, prophet_mae)

    os.makedirs(os.path.dirname(WEIGHTS_PATH), exist_ok=True)
    with open(WEIGHTS_PATH, "w") as f:
        json.dump(weights, f, indent=2)
    return weights


# Feature row construction for a future prediction
    # Return 1 if date d falls inside any shutdown range, else 0
def check_shutdown(d, shutdown_ranges=SHUTDOWN_PERIODS):
    from datetime import date as date_type
    if isinstance(d, str):
        d = date_type.fromisoformat(d)
    for start_str, end_str in shutdown_ranges:
        start = date_type.fromisoformat(start_str)
        end = date_type.fromisoformat(end_str)
        if start <= d <= end:
            return 1
    return 0

# Signed distance in days to the nearest holiday within +/- max_window
def nearest_holiday_distance(d, holiday_dates, max_window=7):
    best = None
    for offset in range(-max_window, max_window + 1):
        check = d + timedelta(days=offset)
        if check in holiday_dates:
            if best is None or abs(offset) < abs(best):
                best = -offset
    return best if best is not None else max_window + 1

# Construct a single feature row for LightGBM prediction.
def build_feature_row(airport_code, target_date, hour, historical_df):
    target_dt = pd.to_datetime(target_date)
    dow = target_dt.dayofweek
    month = target_dt.month
    week_of_year = target_dt.isocalendar().week
    is_weekend = 1 if dow in (5, 6) else 0

    # Slice historical data for this airport
    ap_hist = historical_df[historical_df["airport_code"] == airport_code]

    # Same airport + same hour + same day of week -> use averages as proxy for unknowns
    same_context = ap_hist[
        (ap_hist["hour"] == hour)
        & (pd.to_datetime(ap_hist["date"]).dt.dayofweek == dow)
    ]

    def avg_or_zero(col):
        if col not in ap_hist.columns or same_context.empty:
            return 0.0
        val = same_context[col].mean()
        return float(val) if pd.notna(val) else 0.0

    # Lag features: wait at this airport, this hour, 7 days ago
    target_minus_7 = (target_dt - timedelta(days=7)).strftime("%Y-%m-%d")
    lag_week_row = ap_hist[
        (ap_hist["date"] == target_minus_7) & (ap_hist["hour"] == hour)
    ]
    wait_same_hour_last_week = (
        float(lag_week_row["wait_minutes"].iloc[0])
        if not lag_week_row.empty
        else avg_or_zero("wait_minutes")
    )

    # 4-week rolling average for same hour/day-of-week
    lag_dates = [(target_dt - timedelta(days=7 * w)).strftime("%Y-%m-%d") for w in (1, 2, 3, 4)]
    lag_rows = ap_hist[
        ap_hist["date"].isin(lag_dates) & (ap_hist["hour"] == hour)
    ]
    wait_avg_last_4_weeks = (
        float(lag_rows["wait_minutes"].mean())
        if not lag_rows.empty
        else avg_or_zero("wait_minutes")
    )

    # Holiday flags
    years = [target_dt.year]
    us_holidays = set(holidays.UnitedStates(years=years).keys())
    d = target_dt.date()
    is_holiday_flag = 1 if d in us_holidays else 0
    days_to_holiday = nearest_holiday_distance(d, us_holidays)

    # Shutdown + staffing
    is_shutdown_flag = check_shutdown(d)
    staffing_mod = STAFFING_MODIFIERS["reduced"] if is_shutdown_flag else STAFFING_MODIFIERS["normal"]

    # Build the row as a dict keyed by feature name
    row = {
        "hour": hour,
        "day_of_week": dow,
        "month": month,
        "week_of_year": int(week_of_year),
        "is_weekend": is_weekend,
        "throughput": avg_or_zero("throughput"),
        "num_departures": avg_or_zero("num_departures"),
        "num_cancelled": avg_or_zero("num_cancelled"),
        "avg_delay_min": avg_or_zero("avg_delay_min"),
        "pct_international": avg_or_zero("pct_international"),
        "wait_same_hour_last_week": wait_same_hour_last_week,
        "wait_avg_last_4_weeks_same_hour_dow": wait_avg_last_4_weeks,
        "is_holiday": is_holiday_flag,
        "days_to_nearest_holiday": days_to_holiday,
        "is_shutdown": is_shutdown_flag,
        "staffing_modifier": staffing_mod,
        "extreme_weather_flag": 0,  # unknown for future dates
    }

    # Return a DataFrame with columns in the exact order LightGBM expects
    return pd.DataFrame([row])[FEATURES]


# Tier classification
  # Map a numeric prediction to a human-readable tier from config
def classify_tier(minutes):
    for tier_name, (low, high) in WAIT_TIME_TIERS.items():
        if low <= minutes < high:
            return tier_name
    return "heavy"  # fallback for anything above the top bucket


# Main prediction function
    # Predict the wait time at a given airport, date, and hour.
def predict_wait_time(airport_code, date_str, hour,
                      lgb_model=None, prophet_models=None,
                      historical_df=None, weights=None):
    
    # check if hour is valid
    if not isinstance(hour, int) or not 0 <= hour <= 23:
        raise ValueError(f"hour must be an integer 0-23, got {hour!r}")
    airport_code = airport_code.upper()

    # Lazy-load resources if not supplied
    if lgb_model is None:
        lgb_model = load_lgb_model()
    if prophet_models is None:
        prophet_models = load_prophet_models()
    if historical_df is None:
        historical_df = pd.read_csv(TRAINING_DATA_PATH)
    if weights is None:
        weights = load_or_compute_weights()

    # LightGBM prediction
    feature_row = build_feature_row(airport_code, date_str, hour, historical_df)
    lgb_pred = float(lgb_predict(lgb_model, feature_row)[0])

    # Prophet prediction
    target_ts = pd.to_datetime(date_str) + pd.to_timedelta(hour, unit="h")
    prophet_arr = prophet_predict(prophet_models, airport_code, [target_ts])
    prophet_pred = float(prophet_arr[0]) if prophet_arr is not None else lgb_pred

    # Weighted blend
    blended = weights["lightgbm"] * lgb_pred + weights["prophet"] * prophet_pred
    blended = max(0.0, blended)  # wait time can't be negative

    # Confidence range: use +/- the spread between the two models as a proxy
    # for uncertainty. Wider spread = less confident.
    spread = abs(lgb_pred - prophet_pred)
    range_half = max(spread, 3.0)  # minimum +/- 3 min
    range_low = max(0.0, blended - range_half)
    range_high = blended + range_half

    return {
        "airport_code": airport_code,
        "date": date_str,
        "hour": hour,
        "prediction_minutes": round(blended, 1),
        "tier": classify_tier(blended),
        "range_low": round(range_low, 1),
        "range_high": round(range_high, 1),
        "model_predictions": {
            "lightgbm": round(lgb_pred, 1),
            "prophet": round(prophet_pred, 1),
        },
        "weights": weights,
    }