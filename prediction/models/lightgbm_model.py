# lightgbm_model.py - gradient boosted tree model for Tsa wait time prediction

import os
import json
import joblib
import numpy as np
import pandas as pd
import lightgbm as lgb 
from sklearn.metrics import mean_absolute_error, mean_squared_error

from config import (
    FEATURES, TARGET, LGB_PARAMS, LGB_NUM_BOOST_ROUND, LGB_EARLY_STOPPING_ROUNDS, LGB_TEST_SET_FRACTION
)

INPUT_PATH = "data/exports/training_data_final.csv"
MODEL_PATH = "models/saved/lightgbm_model.pkl"
METRICS_PATH = "models/saved/lightgbm_metrics.json"

# loading training data
def load_training_data(input_path = INPUT_PATH):
    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Training data not found at {input_path}. Run build_features.py first"
        )
    
    df = pd.read_csv(input_path)
    if df.empty:
        raise ValueError("Training data is emtpy")
    
    df = df.sort_values(['date', 'hour']).reset_index(drop = True)

    X = df[FEATURES]
    Y = df[TARGET]

    return X, Y, df

def time_based_split(X, Y, test_fraction = LGB_TEST_SET_FRACTION):
    split_idx = int(len(X) * (1 - test_fraction))
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    Y_train, Y_test = Y.iloc[:split_idx], Y.iloc[split_idx:]
    return X_train, X_test, Y_train, Y_test

def train(X_train, Y_train, X_test, Y_test, params = None):
    params = params or LGB_PARAMS

    train_data = lgb.Dataset(X_train, label = Y_train)
    val_data = lgb.Dataset(X_test, label = Y_test, reference = train_data)

    model = lgb.train(
        params, 
        train_data, 
        num_boost_round = LGB_NUM_BOOST_ROUND,
        valid_sets = [train_data, val_data],
        callbacks = [
            lgb.early_stopping(LGB_EARLY_STOPPING_ROUNDS),
            lgb.log_evaluation(0)
        ]
    )
    return model
def evaluate(model, X_test, Y_test):
    preds = model.predict(X_test, num_iterations = model.best_iteration)

    mae = mean_absolute_error(Y_test, preds)
    rmse = np.sqrt(mean_squared_error(Y_test, preds))

    # within-N-minutes accuracy: how often we're within X minutes of actual
    within_5 = np.mean(np.abs(preds - Y_test) <= 5)
    within_10 = np.mean(np.abs(preds - Y_test) <= 10)

    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "within_5_min": float(within_5),
        "within_10_min": float(within_10),
        "n_test_samples": int(len(Y_test)),
        "best_iteration": int(model.best_iteration)
    }

# Return a list of (feature, importance) tuples sorted descending
def feature_importance(model, feature_names, top_n=10):
    importances = model.feature_importance(importance_type="gain")
    pairs = sorted(zip(feature_names, importances), key=lambda x: -x[1])
    return pairs[:top_n]

# Persitance
def save_model(model, path=MODEL_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(model, path)

def load_model(path=MODEL_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(f"No saved model at {path}")
    return joblib.load(path)

def save_metrics(metrics, path=METRICS_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(metrics, f, indent=2)

# prediction interface
def predict(model, X):
    return model.predict(X, num_iteration=model.best_iteration)


# Full pipeline: load data -> split -> train -> evaluate -> save.
    # Returns a results dict with metrics, feature importance, and paths.
def run_training_pipeline():
    X, y, df = load_training_data()
    X_train, X_test, y_train, y_test = time_based_split(X, y)

    model = train(X_train, y_train, X_test, y_test)
    metrics = evaluate(model, X_test, y_test)
    importance = feature_importance(model, FEATURES)

    save_model(model)
    save_metrics(metrics)

    return {
        "metrics": metrics,
        "feature_importance": importance,
        "train_size": len(X_train),
        "test_size": len(X_test),
        "model_path": MODEL_PATH,
        "metrics_path": METRICS_PATH,
    }