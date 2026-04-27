# build_db.py - loads normalized data from data/normalized/ into tsa.db

import os
import sqlite3
from pathlib import Path

import pandas as pd
from config import DB_PATH, AIRPORTS, AIRPORT_INFO

from config import EXPORTS_DIR as EXPORT_DIR, PREDICTION_DIR
NORMALIZED_DIR = os.path.join(PREDICTION_DIR, "data", "normalized")

# DB setup: create/connect and ensure all tables exist
def get_db(db_path=DB_PATH):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS airports (
            code TEXT PRIMARY KEY,
            name TEXT,
            city TEXT,
            state TEXT,
            latitude REAL,
            longitude REAL
        );

        CREATE TABLE IF NOT EXISTS wait_times (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            airport_code TEXT NOT NULL,
            date TEXT NOT NULL,
            hour INTEGER NOT NULL,
            wait_minutes REAL,
            user_reported INTEGER,
            source TEXT,
            UNIQUE(airport_code, date, hour, source)
        );

        CREATE TABLE IF NOT EXISTS throughput (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            airport_code TEXT NOT NULL,
            date TEXT NOT NULL,
            hour INTEGER NOT NULL,
            checkpoint TEXT,
            passengers INTEGER NOT NULL,
            UNIQUE(airport_code, date, hour, checkpoint)
        );

        CREATE TABLE IF NOT EXISTS flights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            airport_code TEXT NOT NULL,
            date TEXT NOT NULL,
            hour INTEGER NOT NULL,
            num_departures INTEGER,
            num_cancelled INTEGER,
            num_international INTEGER,
            avg_delay_min REAL,
            UNIQUE(airport_code, date, hour)
        );

        CREATE TABLE IF NOT EXISTS weather (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            airport_code TEXT NOT NULL,
            date TEXT NOT NULL,
            hour INTEGER NOT NULL,
            temp_f REAL,
            wind_mph REAL,
            precip_in REAL,
            conditions TEXT,
            UNIQUE(airport_code, date, hour)
        );

        CREATE INDEX IF NOT EXISTS idx_wait_airport_date ON wait_times(airport_code, date);
        CREATE INDEX IF NOT EXISTS idx_throughput_airport_date ON throughput(airport_code, date);
        CREATE INDEX IF NOT EXISTS idx_flights_airport_date ON flights(airport_code, date);
        CREATE INDEX IF NOT EXISTS idx_weather_airport_date ON weather(airport_code, date);
    """)
    conn.commit()
    return conn

# Generic loader: given a dataframe + table + columns, do a bulk insert
    # Insert rows from a normalized dataframe into the given table
def _bulk_insert(conn, df, table, columns):
    if df.empty:
        return 0

    # Keep only rows with valid airport codes
    df = df[df["airport_code"].isin(AIRPORTS)].copy()
    if df.empty:
        return 0

    # Restrict to expected columns in the right order
    df = df[columns]

    placeholders = ", ".join(["?"] * len(columns))
    col_list = ", ".join(columns)
    sql = f"INSERT OR REPLACE INTO {table} ({col_list}) VALUES ({placeholders})"

    conn.executemany(sql, df.itertuples(index=False, name=None))
    conn.commit()
    return len(df)


# Table loaders: each one reads a single normalized CSV and inserts it
    # Populate airports table from AIRPORT_INFO in config
def load_airports(conn):
    for code, (name, city, state, lat, lon) in AIRPORT_INFO.items():
        conn.execute("""
            INSERT OR REPLACE INTO airports (code, name, city, state, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (code, name, city, state, lat, lon))
    conn.commit()
    return len(AIRPORT_INFO)


def load_wait_times(conn, path=None):
    path = path or os.path.join(NORMALIZED_DIR, "wait_times.csv")
    if not os.path.exists(path):
        return 0
    df = pd.read_csv(path)
    return _bulk_insert(
        conn, df, "wait_times",
        ["airport_code", "date", "hour", "wait_minutes", "user_reported", "source"],
    )


def load_throughput(conn, path=None):
    path = path or os.path.join(NORMALIZED_DIR, "throughput.csv")
    if not os.path.exists(path):
        return 0
    df = pd.read_csv(path)
    return _bulk_insert(
        conn, df, "throughput",
        ["airport_code", "date", "hour", "checkpoint", "passengers"],
    )


def load_flights(conn, path=None):
    path = path or os.path.join(NORMALIZED_DIR, "flights.csv")
    if not os.path.exists(path):
        return 0
    df = pd.read_csv(path)
    return _bulk_insert(
        conn, df, "flights",
        ["airport_code", "date", "hour", "num_departures", "num_cancelled",
         "num_international", "avg_delay_min"],
    )


def load_weather(conn, path=None):
    path = path or os.path.join(NORMALIZED_DIR, "weather.csv")
    if not os.path.exists(path):
        return 0
    df = pd.read_csv(path)
    return _bulk_insert(
        conn, df, "weather",
        ["airport_code", "date", "hour", "temp_f", "wind_mph", "precip_in", "conditions"],
    )

# Export training data: joins all tables, derives engineered features, and writes a flat CSV ready for model training.
def export_training_data(conn, output_path=None, airport_code=None):
    if output_path is None:
        output_path = os.path.join(EXPORT_DIR, "training_data.csv")

    where = ""
    params = ()
    if airport_code:
        where = "WHERE w.airport_code = ?"
        params = (airport_code.upper(),)

    query = f"""
        SELECT
            w.airport_code,
            w.date,
            w.hour,
            w.wait_minutes,
            w.user_reported,

            t.passengers AS throughput,

            f.num_departures,
            f.num_cancelled,
            f.num_international,
            f.avg_delay_min,

            -- pct international: share of departures that are international
            CASE
                WHEN f.num_departures > 0
                THEN CAST(f.num_international AS REAL) / f.num_departures
                ELSE 0
            END AS pct_international,

            -- raw weather kept for reference; extreme_weather_flag is the model input
            wx.temp_f,
            wx.wind_mph,
            wx.precip_in,
            wx.conditions,

            CASE
                WHEN (wx.precip_in > 0.5
                      OR wx.wind_mph > 30
                      OR wx.temp_f < 20)
                THEN 1 ELSE 0
            END AS extreme_weather_flag,

            -- derived time features
            CAST(strftime('%w', w.date) AS INTEGER) AS day_of_week,
            CAST(strftime('%m', w.date) AS INTEGER) AS month,
            CAST(strftime('%W', w.date) AS INTEGER) AS week_of_year,
            CASE WHEN CAST(strftime('%w', w.date) AS INTEGER) IN (0, 6)
                 THEN 1 ELSE 0 END AS is_weekend

        FROM wait_times w
        LEFT JOIN throughput t
            ON w.airport_code = t.airport_code
            AND w.date = t.date
            AND w.hour = t.hour
        LEFT JOIN flights f
            ON w.airport_code = f.airport_code
            AND w.date = f.date
            AND w.hour = f.hour
        LEFT JOIN weather wx
            ON w.airport_code = wx.airport_code
            AND w.date = wx.date
            AND w.hour = wx.hour
        {where}
        ORDER BY w.airport_code, w.date, w.hour
    """

    df = pd.read_sql_query(query, conn, params=params)

    if df.empty:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        return 0

    # Derived lag features (computed in pandas, not SQL, for simplicity)
    df["datetime"] = pd.to_datetime(df["date"]) + pd.to_timedelta(df["hour"], unit="h")
    df = df.sort_values(["airport_code", "datetime"]).reset_index(drop=True)

    # wait_same_hour_last_week: wait at this airport, this hour, exactly 7 days ago
    lag_week = df[["airport_code", "datetime", "wait_minutes"]].copy()
    lag_week["datetime"] = lag_week["datetime"] + pd.Timedelta(days=7)
    lag_week = lag_week.rename(columns={"wait_minutes": "wait_same_hour_last_week"})
    df = df.merge(lag_week, on=["airport_code", "datetime"], how="left")

    # wait_avg_last_4_weeks_same_hour_dow: avg of 1/2/3/4 week lags
    lag_frames = []
    for weeks_back in (1, 2, 3, 4):
        tmp = df[["airport_code", "datetime", "wait_minutes"]].copy()
        tmp["datetime"] = tmp["datetime"] + pd.Timedelta(days=7 * weeks_back)
        tmp = tmp.rename(columns={"wait_minutes": f"lag_{weeks_back}w"})
        lag_frames.append(tmp)

    for lf in lag_frames:
        df = df.merge(lf, on=["airport_code", "datetime"], how="left")

    lag_cols = [f"lag_{w}w" for w in (1, 2, 3, 4)]
    df["wait_avg_last_4_weeks_same_hour_dow"] = df[lag_cols].mean(axis=1, skipna=True)
    df = df.drop(columns=lag_cols + ["datetime"])

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    return len(df)


# Summary + full build
    # Return a dict of record counts per table
def get_summary(conn):
    tables = ["airports", "wait_times", "throughput", "flights", "weather"]
    return {
        t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        for t in tables
    }


def build_all(db_path=DB_PATH):
    """Full pipeline: create DB, load all normalized data, return summary."""
    conn = get_db(db_path)
    results = {
        "airports":    load_airports(conn),
        "wait_times":  load_wait_times(conn),
        "throughput":  load_throughput(conn),
        "flights":     load_flights(conn),
        "weather":     load_weather(conn),
    }
    conn.close()
    return results