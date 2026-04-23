# prophet_model.py - time series forcasting model

import os
import json
import joblib
import logging

import numpy as np
import pandas as pd
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error

from config import (
    AIRPORTS,
    PROPHET_PARAMS,
    PROPHET_TEST_SET_FRACTION,
)

INPUT_PATH = "data/exports/training_data_final.csv"
MODEL_PATH = "models/saved/prophet_models.pkl"
METRICS_PATH = "models/saved/prophet_metrics.json"

# Prophet is very chatty by default — silence its per-fit output
logging.getLogger("prophet").setLevel(logging.WARNING)
logging.getLogger("cmdstanpy").setLevel(logging.WARNING)


# ---------------------------------------------------------------------------
# Data loading and formatting
# ---------------------------------------------------------------------------
def load_training_data(input_path=INPUT_PATH):
    """Load the model-ready CSV and return it sorted chronologically."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Training data not found at {input_path}. Run build_features first."
        )

    df = pd.read_csv(input_path)
    if df.empty:
        raise ValueError("Training data is empty.")

    df = df.sort_values(["airport_code", "date", "hour"]).reset_index(drop=True)
    return df


def format_for_prophet(df_airport):
    """
    Prophet requires a very specific dataframe format:
        ds: datetime column
        y:  target column

    We combine date + hour into a single timestamp.
    """
    out = pd.DataFrame({
        "ds": pd.to_datetime(df_airport["date"]) + pd.to_timedelta(df_airport["hour"], unit="h"),
        "y": df_airport["wait_minutes"],
    })
    return out


# ---------------------------------------------------------------------------
# Train/test split (time-based, per airport)
# ---------------------------------------------------------------------------
def time_based_split(df_prophet, test_fraction=PROPHET_TEST_SET_FRACTION):
    """Split a single airport's Prophet-formatted df chronologically."""
    split_idx = int(len(df_prophet) * (1 - test_fraction))
    train = df_prophet.iloc[:split_idx].reset_index(drop=True)
    test = df_prophet.iloc[split_idx:].reset_index(drop=True)
    return train, test


# ---------------------------------------------------------------------------
# Training (one airport)
# ---------------------------------------------------------------------------
def train_one_airport(train_df, params=None):
    """
    Fit a single Prophet model on one airport's training data.
    Returns the fitted model, or None if there's too little data to train.
    """
    params = params or PROPHET_PARAMS

    # Prophet needs at least 2 data points and some variance to fit
    if len(train_df) < 24 or train_df["y"].nunique() < 2:
        return None

    model = Prophet(**params)
    # add_country_holidays pulls US federal holidays automatically
    model.add_country_holidays(country_name="US")
    model.fit(train_df)
    return model


# ---------------------------------------------------------------------------
# Evaluation (one airport)
# ---------------------------------------------------------------------------
def evaluate_one_airport(model, test_df):
    """Return MAE / RMSE / within-N metrics for a single airport's test set."""
    if model is None or test_df.empty:
        return None

    future = test_df[["ds"]].copy()
    forecast = model.predict(future)

    y_true = test_df["y"].values
    y_pred = forecast["yhat"].values

    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    within_5 = np.mean(np.abs(y_pred - y_true) <= 5)
    within_10 = np.mean(np.abs(y_pred - y_true) <= 10)

    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "within_5_min": float(within_5),
        "within_10_min": float(within_10),
        "n_test_samples": int(len(test_df)),
    }


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------
def save_models(models_dict, path=MODEL_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(models_dict, path)


def load_models(path=MODEL_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(f"No saved Prophet models at {path}")
    return joblib.load(path)


def save_metrics(metrics, path=METRICS_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(metrics, f, indent=2)


# ---------------------------------------------------------------------------
# Prediction interface
# ---------------------------------------------------------------------------
def predict(models_dict, airport_code, timestamps):
    """
    Predict wait times for a given airport at one or more timestamps.

    Args:
        models_dict:  dict of {airport_code: fitted Prophet model}
        airport_code: str (e.g. 'JFK')
        timestamps:   list-like of datetime-compatible values

    Returns:
        numpy array of predicted wait_minutes, or None if no model exists
        for that airport.
    """
    model = models_dict.get(airport_code)
    if model is None:
        return None

    future = pd.DataFrame({"ds": pd.to_datetime(timestamps)})
    forecast = model.predict(future)
    return forecast["yhat"].values


# ---------------------------------------------------------------------------
# End-to-end runner
# ---------------------------------------------------------------------------
def run_training_pipeline():
    """
    Train one Prophet model per airport, evaluate, save everything.
    Returns a results dict with per-airport metrics and an overall summary.
    """
    df = load_training_data()

    models = {}
    per_airport_metrics = {}
    skipped = []

    for airport in AIRPORTS:
        df_ap = df[df["airport_code"] == airport]
        if df_ap.empty:
            skipped.append(airport)
            continue

        prophet_df = format_for_prophet(df_ap)
        train_df, test_df = time_based_split(prophet_df)

        model = train_one_airport(train_df)
        if model is None:
            skipped.append(airport)
            continue

        metrics = evaluate_one_airport(model, test_df)
        models[airport] = model
        per_airport_metrics[airport] = metrics

    # Overall metrics: simple average across airports we successfully trained
    trained = [m for m in per_airport_metrics.values() if m is not None]
    if trained:
        overall = {
            "mae": float(np.mean([m["mae"] for m in trained])),
            "rmse": float(np.mean([m["rmse"] for m in trained])),
            "within_5_min": float(np.mean([m["within_5_min"] for m in trained])),
            "within_10_min": float(np.mean([m["within_10_min"] for m in trained])),
            "n_airports_trained": len(trained),
            "n_airports_skipped": len(skipped),
        }
    else:
        overall = {"error": "no airports trained successfully"}

    save_models(models)
    save_metrics({"overall": overall, "per_airport": per_airport_metrics,
                  "skipped": skipped})

    return {
        "overall_metrics": overall,
        "per_airport_metrics": per_airport_metrics,
        "skipped": skipped,
        "model_path": MODEL_PATH,
        "metrics_path": METRICS_PATH,
    }