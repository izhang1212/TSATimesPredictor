# bulid_features.py - final feature engineering

import os
from datetime import date, timedelta
import pandas as pd
import holidays

from prediction.config import STAFFING_MODIFIERS, SHUTDOWN_PERIODS

INPUT_PATH = "data/exports/training_data.csv"
OUTPUT_PATH = "data/exports/training_data_final.csv"

def build_holiday_calendar(years):
    us_holidays = holidays.UnitedStates(years = years)
    return set(us_holidays.keys())

def nearest_holiday_distance(d, holiday_dates, max_window = 7):
    best = None
    for offset in range(-max_window, max_window + 1):
        check = d + timedelta(days=offset)
        if check in holiday_dates:
            # "-offset" so negative = upcoming, positive = just happened
            if best is None or abs(offset) < abs(best):
                best = -offset
    return best if best is not None else max_window + 1

def check_shutdown(d, shutdown_ranges):
    for start_str, end_str in shutdown_ranges:
        start = date.fromisoformat(start_str)
        end = date.fromisoformat(end_str)
        if start <= d <= end:
            return 1
        return 0
    
def staffing_modifier(is_shutdown_flag):
    if is_shutdown_flag == 1:
        return STAFFING_MODIFIERS["reduced"]
    return STAFFING_MODIFIERS["normal"]

def build_features(input_path=INPUT_PATH, output_path=OUTPUT_PATH):
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Training CSV not found at {input_path}. Run build_db first.")

    df = pd.read_csv(input_path)
    if df.empty:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        return 0

    # Drop rows with no target (can't train on these)
    df = df.dropna(subset=["wait_minutes"]).reset_index(drop=True)

    # Parse dates once
    df["_date_obj"] = pd.to_datetime(df["date"]).dt.date

    # Holiday calendar covering every year in the data
    years = sorted({d.year for d in df["_date_obj"]})
    holiday_dates = build_holiday_calendar(years)

    # is_holiday
    df["is_holiday"] = df["_date_obj"].apply(
        lambda d: 1 if d in holiday_dates else 0
    )

    # days_to_nearest_holiday (signed, window +/- 7 days)
    df["days_to_nearest_holiday"] = df["_date_obj"].apply(
        lambda d: nearest_holiday_distance(d, holiday_dates, max_window=7)
    )

    # is_shutdown
    df["is_shutdown"] = df["_date_obj"].apply(
        lambda d: check_shutdown(d, SHUTDOWN_PERIODS)
    )

    # staffing_modifier
    df["staffing_modifier"] = df["is_shutdown"].apply(staffing_modifier)

    # Drop the helper column
    df = df.drop(columns=["_date_obj"])

    # Missing value handling
    # Lag features: may be NaN for early rows (no history yet). Fill with 0.
    for col in ["wait_same_hour_last_week", "wait_avg_last_4_weeks_same_hour_dow"]:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    # Flight/throughput features: NaN means "no data available" -> 0 is safe
    for col in ["throughput", "num_departures", "num_cancelled",
                "num_international", "avg_delay_min", "pct_international"]:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    # Weather flag: NaN means no weather data -> assume normal (0)
    if "extreme_weather_flag" in df.columns:
        df["extreme_weather_flag"] = df["extreme_weather_flag"].fillna(0).astype(int)

    # Write out
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    return len(df)