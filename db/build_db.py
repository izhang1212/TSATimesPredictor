"""
build_db.py
===========
Reads all raw data from data/raw/ and loads it into a single
unified database at data/tsa.db.

Tables: airports, wait_times, throughput, flights, weather

Everything joins on (airport_code, date, hour).
"""

import sqlite3
import os
import re
import csv
import math
from datetime import datetime
from pathlib import Path

import pandas as pd

# Config
DB_PATH = "data/tsa.db"

RAW_WAIT_TIMES_DIR = "data/raw/wait_times"
RAW_THROUGHPUT_DIR = "data/raw/throughput"
RAW_FLIGHTS_DIR = "data/raw/flights"
RAW_WEATHER_DIR = "data/raw/weather"
EXPORT_DIR = "data/exports"

AIRPORTS = [
    "JFK", "LGA", "EWR", "BOS", "PHL", "DCA", "IAD", "BWI", "BDL", "PIT",
    "ATL", "MIA", "FLL", "MCO", "CLT", "TPA", "BNA", "RDU", "JAX",
    "ORD", "MDW", "DTW", "MSP", "CLE", "MKE", "STL",
    "LAX", "SFO", "SAN", "SEA", "PDX", "LAS", "DEN", "PHX",
    "DFW", "IAH", "AUS", "DAL", "HOU", "SAT",
]


# db set up; create/connect to the unified tsa.db and ensure all tables exist
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


# airport metadata (name, city, state, longitudue, latitude)
AIRPORT_INFO = {
    "JFK": ("John F. Kennedy International", "New York", "NY", 40.6413, -73.7781),
    "LGA": ("LaGuardia", "New York", "NY", 40.7772, -73.8726),
    "EWR": ("Newark Liberty International", "Newark", "NJ", 40.6895, -74.1745),
    "BOS": ("Logan International", "Boston", "MA", 42.3656, -71.0096),
    "PHL": ("Philadelphia International", "Philadelphia", "PA", 39.8721, -75.2411),
    "DCA": ("Ronald Reagan Washington National", "Washington", "DC", 38.8512, -77.0402),
    "IAD": ("Washington Dulles International", "Dulles", "VA", 38.9531, -77.4565),
    "BWI": ("Baltimore/Washington International", "Baltimore", "MD", 39.1754, -76.6683),
    "BDL": ("Bradley International", "Hartford", "CT", 41.9389, -72.6832),
    "PIT": ("Pittsburgh International", "Pittsburgh", "PA", 40.4915, -80.2329),
    "ATL": ("Hartsfield-Jackson Atlanta International", "Atlanta", "GA", 33.6407, -84.4277),
    "MIA": ("Miami International", "Miami", "FL", 25.7959, -80.2870),
    "FLL": ("Fort Lauderdale-Hollywood International", "Fort Lauderdale", "FL", 26.0726, -80.1527),
    "MCO": ("Orlando International", "Orlando", "FL", 28.4312, -81.3081),
    "CLT": ("Charlotte Douglas International", "Charlotte", "NC", 35.2140, -80.9431),
    "TPA": ("Tampa International", "Tampa", "FL", 27.9755, -82.5332),
    "BNA": ("Nashville International", "Nashville", "TN", 36.1263, -86.6774),
    "RDU": ("Raleigh-Durham International", "Raleigh", "NC", 35.8776, -78.7875),
    "JAX": ("Jacksonville International", "Jacksonville", "FL", 30.4941, -81.6879),
    "ORD": ("O'Hare International", "Chicago", "IL", 41.9742, -87.9073),
    "MDW": ("Midway International", "Chicago", "IL", 41.7868, -87.7522),
    "DTW": ("Detroit Metropolitan Wayne County", "Detroit", "MI", 42.2124, -83.3534),
    "MSP": ("Minneapolis-Saint Paul International", "Minneapolis", "MN", 44.8848, -93.2223),
    "CLE": ("Cleveland Hopkins International", "Cleveland", "OH", 41.4117, -81.8498),
    "MKE": ("Milwaukee Mitchell International", "Milwaukee", "WI", 42.9472, -87.8966),
    "STL": ("St. Louis Lambert International", "St. Louis", "MO", 38.7487, -90.3700),
    "LAX": ("Los Angeles International", "Los Angeles", "CA", 33.9425, -118.4081),
    "SFO": ("San Francisco International", "San Francisco", "CA", 37.6213, -122.3790),
    "SAN": ("San Diego International", "San Diego", "CA", 32.7336, -117.1897),
    "SEA": ("Seattle-Tacoma International", "Seattle", "WA", 47.4502, -122.3088),
    "PDX": ("Portland International", "Portland", "OR", 45.5898, -122.5951),
    "LAS": ("Harry Reid International", "Las Vegas", "NV", 36.0840, -115.1537),
    "DEN": ("Denver International", "Denver", "CO", 39.8561, -104.6737),
    "PHX": ("Phoenix Sky Harbor International", "Phoenix", "AZ", 33.4373, -112.0078),
    "DFW": ("Dallas/Fort Worth International", "Dallas", "TX", 32.8998, -97.0403),
    "IAH": ("George Bush Intercontinental", "Houston", "TX", 29.9902, -95.3368),
    "AUS": ("Austin-Bergstrom International", "Austin", "TX", 30.1975, -97.6664),
    "DAL": ("Dallas Love Field", "Dallas", "TX", 32.8471, -96.8518),
    "HOU": ("William P. Hobby", "Houston", "TX", 29.6454, -95.2789),
    "SAT": ("San Antonio International", "San Antonio", "TX", 29.5337, -98.4698),
}

# populate the table with our 40 airports
def load_airports(conn):
    for code, (name, city, state, lat, lon) in AIRPORT_INFO.items():
        conn.execute("""
            INSERT OR REPLACE INTO airports (code, name, city, state, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (code, name, city, state, lat, lon))
    conn.commit()
    return len(AIRPORT_INFO)


# load daily CSVs from scrapers into the wait_times table
    # returns total rows inserted.
def load_wait_times(conn, raw_dir=RAW_WAIT_TIMES_DIR):
    if not os.path.exists(raw_dir):
        return 0

    csv_files = sorted(Path(raw_dir).glob("*.csv"))
    total = 0

    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
        except Exception:
            continue

        for _, row in df.iterrows():
            try:
                ts = str(row.get("timestamp", ""))
                airport = str(row.get("airport_code", "")).strip().upper()
                wait = row.get("rightnow_minutes", -1)
                user_rep = row.get("user_reported_minutes", 0)

                if not airport or airport not in AIRPORTS:
                    continue
                if pd.isna(wait) or int(wait) < 0:
                    continue

                dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                date_str = dt.strftime("%Y-%m-%d")
                hour = dt.hour

                conn.execute("""
                    INSERT OR REPLACE INTO wait_times
                        (airport_code, date, hour, wait_minutes, user_reported, source)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (airport, date_str, hour, float(wait), int(user_rep or 0), "tsawaittimes"))
                total += 1
            except (ValueError, TypeError):
                continue

    conn.commit()
    return total


# Load throughput (from mikelor CSVs)
def load_throughput(conn, raw_dir=RAW_THROUGHPUT_DIR):
    if not os.path.exists(raw_dir):
        return 0

    csv_files = sorted(Path(raw_dir).glob("*.csv"))
    total = 0
    airport_pattern = re.compile(r'^([A-Z]{3})\s+(.+)$')

    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
        except Exception:
            continue

        df.columns = [str(c).strip() for c in df.columns]

        lower_cols = [c.lower() for c in df.columns]
        has_date = any("date" in c for c in lower_cols)
        has_hour = any("hour" in c for c in lower_cols)
        checkpoint_cols = [c for c in df.columns if airport_pattern.match(c)]

        if not (has_date and has_hour and len(checkpoint_cols) > 2):
            continue

        date_col = next(c for c in df.columns if "date" in c.lower())
        hour_col = next(c for c in df.columns if "hour" in c.lower())

        melted = df.melt(
            id_vars=[date_col, hour_col],
            value_vars=checkpoint_cols,
            var_name="airport_checkpoint",
            value_name="passengers",
        )
        melted = melted.dropna(subset=["passengers"])
        melted = melted[melted["passengers"] > 0]

        if melted.empty:
            continue

        parsed = melted["airport_checkpoint"].str.extract(r'^([A-Z]{3})\s+(.+)$')
        melted["airport_code"] = parsed[0]
        melted["checkpoint"] = parsed[1]
        melted["date"] = melted[date_col]
        melted["passengers"] = melted["passengers"].astype(int)

        raw_hour = melted[hour_col].astype(str)
        melted["hour"] = raw_hour.apply(
            lambda x: int(x.split(":")[0]) if ":" in x else int(float(x))
        )

        # Filter to our 40 airports
        melted = melted[melted["airport_code"].isin(AIRPORTS)]

        for _, row in melted.iterrows():
            try:
                date_val = str(row["date"]).strip()
                for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
                    try:
                        date_val = datetime.strptime(date_val, fmt).strftime("%Y-%m-%d")
                        break
                    except ValueError:
                        continue

                conn.execute("""
                    INSERT OR REPLACE INTO throughput
                        (airport_code, date, hour, checkpoint, passengers)
                    VALUES (?, ?, ?, ?, ?)
                """, (row["airport_code"], date_val, row["hour"],
                      row["checkpoint"], row["passengers"]))
                total += 1
            except (ValueError, TypeError):
                continue

    conn.commit()
    return total


# Load flights (from BTS Transtats CSVs)
    # Aggregates individual flights into hourly counts per airport: num_departures, num_cancelled, avg_delay_min
def load_flights(conn, raw_dir=RAW_FLIGHTS_DIR):
    if not os.path.exists(raw_dir):
        return 0

    csv_files = sorted(Path(raw_dir).glob("*.csv"))
    total = 0

    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file, low_memory=False)
        except Exception:
            continue

        df.columns = [str(c).strip() for c in df.columns]

        # Identify columns (BTS uses various naming conventions)
        origin_col = None
        date_col = None
        deptime_col = None
        cancelled_col = None
        delay_col = None

        for col in df.columns:
            cl = col.lower().replace("_", "")
            if cl in ("origin",):
                origin_col = col
            elif cl in ("flightdate",):
                date_col = col
            elif cl in ("crsdeptime",):
                deptime_col = col
            elif cl in ("cancelled",):
                cancelled_col = col
            elif cl in ("depdelayminutes",):
                delay_col = col

        if not all([origin_col, date_col, deptime_col]):
            continue

        # Filter to our airports
        df = df[df[origin_col].isin(AIRPORTS)]

        # Extract hour from CRSDepTime (format: hhmm like 1430)
        df["dep_hour"] = pd.to_numeric(df[deptime_col], errors="coerce") // 100
        df["dep_hour"] = df["dep_hour"].clip(0, 23)

        # Aggregate by airport + date + hour
        grouped = df.groupby([origin_col, date_col, "dep_hour"]).agg(
            num_departures=pd.NamedAgg(column=deptime_col, aggfunc="count"),
            num_cancelled=pd.NamedAgg(column=cancelled_col, aggfunc="sum") if cancelled_col else pd.NamedAgg(column=deptime_col, aggfunc=lambda x: 0),
            avg_delay=pd.NamedAgg(column=delay_col, aggfunc="mean") if delay_col else pd.NamedAgg(column=deptime_col, aggfunc=lambda x: 0),
        ).reset_index()

        for _, row in grouped.iterrows():
            try:
                date_val = str(row[date_col]).strip()
                for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
                    try:
                        date_val = datetime.strptime(date_val, fmt).strftime("%Y-%m-%d")
                        break
                    except ValueError:
                        continue

                conn.execute("""
                    INSERT OR REPLACE INTO flights
                        (airport_code, date, hour, num_departures, num_cancelled, avg_delay_min)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    row[origin_col],
                    date_val,
                    int(row["dep_hour"]),
                    int(row["num_departures"]),
                    int(row.get("num_cancelled", 0) or 0),
                    round(float(row.get("avg_delay", 0) or 0), 1),
                ))
                total += 1
            except (ValueError, TypeError):
                continue

    conn.commit()
    return total

# Load weather (from NOAA CSVs)
    # Expected format: airport_code, date, hour, temp_f, wind_mph, precip_in, conditions
def load_weather(conn, raw_dir=RAW_WEATHER_DIR):
    if not os.path.exists(raw_dir):
        return 0

    csv_files = sorted(Path(raw_dir).glob("*.csv"))
    total = 0

    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
        except Exception:
            continue

        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

        for _, row in df.iterrows():
            try:
                airport = str(row.get("airport_code", "")).strip().upper()
                if airport not in AIRPORTS:
                    continue

                conn.execute("""
                    INSERT OR REPLACE INTO weather
                        (airport_code, date, hour, temp_f, wind_mph, precip_in, conditions)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    airport,
                    str(row.get("date", "")),
                    int(row.get("hour", 0)),
                    float(row.get("temp_f", 0) or 0),
                    float(row.get("wind_mph", 0) or 0),
                    float(row.get("precip_in", 0) or 0),
                    str(row.get("conditions", "")),
                ))
                total += 1
            except (ValueError, TypeError):
                continue

    conn.commit()
    return total


# Export training data
def export_training_data(conn, output_path=None, airport_code=None):
    """
    Join all tables and export a flat CSV for model training.

    Returns number of rows exported.
    """
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
            f.avg_delay_min,

            wx.temp_f,
            wx.wind_mph,
            wx.precip_in,
            wx.conditions,

            -- derived time features
            CAST(strftime('%w', w.date) AS INTEGER) AS day_of_week,
            CAST(strftime('%m', w.date) AS INTEGER) AS month,
            CAST(strftime('%W', w.date) AS INTEGER) AS week_of_year,
            CASE WHEN CAST(strftime('%w', w.date) AS INTEGER) IN (0, 6) THEN 1 ELSE 0 END AS is_weekend

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

    if not df.empty:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)

    return len(df)


# Summary stats
def get_summary(conn):
    """
    Return a dict of record counts for each table.
    """
    tables = ["airports", "wait_times", "throughput", "flights", "weather"]
    summary = {}
    for table in tables:
        row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
        summary[table] = row[0] if row else 0
    return summary


# Build everything
def build_all(db_path=DB_PATH):
    """
    Full pipeline: create DB, load all raw data, return summary.
    """
    conn = get_db(db_path)

    results = {
        "airports": load_airports(conn),
        "wait_times": load_wait_times(conn),
        "throughput": load_throughput(conn),
        "flights": load_flights(conn),
        "weather": load_weather(conn),
    }

    conn.close()
    return results