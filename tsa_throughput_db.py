"""
tsa_throughput_db.py
====================
Pure library for building and populating the TSA throughput SQLite database.
No CLI, no print statements — just functions to be called from main.py.

Data source: https://github.com/mikelor/TsaThroughput
"""

import sqlite3
import os
import re
import math
from datetime import datetime
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DB_PATH = "data/tsa_throughput.db"
CSV_DIR = "data/processed"


# ---------------------------------------------------------------------------
# Database Setup
# ---------------------------------------------------------------------------
def get_db(db_path=DB_PATH):
    """Create/connect to SQLite database and ensure schema exists."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS throughput (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            hour INTEGER NOT NULL,
            airport_code TEXT NOT NULL,
            checkpoint TEXT,
            throughput INTEGER NOT NULL,
            day_of_week INTEGER,
            month INTEGER,
            week_of_year INTEGER,
            is_weekend INTEGER,
            is_holiday_season INTEGER,
            UNIQUE(date, hour, airport_code, checkpoint)
        );

        CREATE TABLE IF NOT EXISTS wait_estimates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            hour INTEGER NOT NULL,
            airport_code TEXT NOT NULL,
            checkpoint TEXT,
            throughput INTEGER,
            num_lanes_estimate INTEGER,
            utilization REAL,
            estimated_wait_minutes REAL,
            UNIQUE(date, hour, airport_code, checkpoint)
        );

        CREATE INDEX IF NOT EXISTS idx_throughput_airport
            ON throughput(airport_code);
        CREATE INDEX IF NOT EXISTS idx_throughput_date
            ON throughput(date);
        CREATE INDEX IF NOT EXISTS idx_throughput_date_airport
            ON throughput(date, airport_code);
        CREATE INDEX IF NOT EXISTS idx_wait_airport
            ON wait_estimates(airport_code);
    """)
    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# CSV Import
# ---------------------------------------------------------------------------
def import_csv(csv_path, conn):
    """
    Import a single CSV file into the throughput table.

    Auto-detects two formats:
      - WIDE (mikelor): Date, Hour, then "ABC Checkpoint Name" columns
      - LONG: Date, Hour, Airport, Checkpoint, Throughput columns

    Returns number of rows inserted.
    """
    try:
        df = pd.read_csv(csv_path)
    except Exception:
        return 0

    df.columns = [str(c).strip() for c in df.columns]

    lower_cols = [c.lower() for c in df.columns]
    has_date = any("date" in c for c in lower_cols)
    has_hour = any("hour" in c for c in lower_cols)

    airport_pattern = re.compile(r'^([A-Z]{3})\s+(.+)$')
    checkpoint_cols = [c for c in df.columns if airport_pattern.match(c)]

    if has_date and has_hour and len(checkpoint_cols) > 2:
        return _import_wide(df, checkpoint_cols, conn)
    else:
        return _import_long(df, conn)


def _import_wide(df, checkpoint_cols, conn):
    """Import a wide-format CSV (mikelor processed format)."""
    date_col = next(c for c in df.columns if "date" in c.lower())
    hour_col = next(c for c in df.columns if "hour" in c.lower())

    melted = df.melt(
        id_vars=[date_col, hour_col],
        value_vars=checkpoint_cols,
        var_name="airport_checkpoint",
        value_name="throughput",
    )

    melted = melted.dropna(subset=["throughput"])
    melted = melted[melted["throughput"] > 0]

    if melted.empty:
        return 0

    parsed = melted["airport_checkpoint"].str.extract(r'^([A-Z]{3})\s+(.+)$')
    melted["airport_code"] = parsed[0]
    melted["checkpoint"] = parsed[1]
    melted["date"] = melted[date_col]
    melted["throughput"] = melted["throughput"].astype(int)

    raw_hour = melted[hour_col].astype(str)
    melted["hour"] = raw_hour.apply(
        lambda x: int(x.split(":")[0]) if ":" in x else int(float(x))
    )

    melted = melted.drop(columns=[date_col, hour_col, "airport_checkpoint"], errors="ignore")

    return _insert_rows(melted, conn)


def _import_long(df, conn):
    """Import a long-format CSV."""
    df.columns = [str(c).strip().lower().replace(" ", "_").replace("of_", "") for c in df.columns]

    col_map = {}
    for col in df.columns:
        if col in ("date",):
            col_map["date"] = col
        elif "hour" in col:
            col_map["hour"] = col
        elif col in ("airport", "airport_code", "iata"):
            col_map["airport_code"] = col
        elif "checkpoint" in col or "check" in col:
            col_map["checkpoint"] = col
        elif col in ("throughput", "total", "pax", "passengers", "count"):
            col_map["throughput"] = col

    required = {"date", "hour", "airport_code", "throughput"}
    if required - set(col_map.keys()):
        return 0

    df = df.rename(columns={v: k for k, v in col_map.items()})
    return _insert_rows(df, conn)


def _insert_rows(df, conn):
    """Insert rows into the throughput table with derived date features."""
    inserted = 0

    for _, row in df.iterrows():
        try:
            date_val = str(row.get("date", "")).strip()
            parsed_date = None
            for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%Y/%m/%d",
                        "%d-%b-%Y", "%d-%b-%y", "%B %d, %Y"):
                try:
                    parsed_date = datetime.strptime(date_val, fmt)
                    date_val = parsed_date.strftime("%Y-%m-%d")
                    break
                except ValueError:
                    continue

            if parsed_date is None:
                continue

            hour_val = int(float(str(row.get("hour", 0))))
            airport = str(row.get("airport_code", "")).strip().upper()
            checkpoint = str(row.get("checkpoint", "")).strip() if pd.notna(row.get("checkpoint")) else None
            throughput = int(float(str(row.get("throughput", 0))))

            if not airport or throughput < 0:
                continue

            day_of_week = parsed_date.weekday()
            month = parsed_date.month
            week_of_year = parsed_date.isocalendar()[1]
            is_weekend = 1 if day_of_week >= 5 else 0
            is_holiday_season = 1 if _is_holiday(parsed_date) else 0

            conn.execute("""
                INSERT OR REPLACE INTO throughput
                    (date, hour, airport_code, checkpoint, throughput,
                     day_of_week, month, week_of_year, is_weekend, is_holiday_season)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (date_val, hour_val, airport, checkpoint, throughput,
                  day_of_week, month, week_of_year, is_weekend, is_holiday_season))
            inserted += 1

        except (ValueError, TypeError):
            continue

    conn.commit()
    return inserted


def _is_holiday(dt):
    """Check if a date falls in a major US travel holiday window."""
    m, d = dt.month, dt.day
    return (
        (m == 11 and d >= 20) or        # Thanksgiving week
        (m == 12 and d >= 18) or         # Christmas
        (m == 1 and d <= 3) or           # New Year
        (m == 7 and 1 <= d <= 7) or      # July 4th
        (m == 5 and d >= 24 and d <= 31) # Memorial Day
    )


def import_all_csvs(csv_dir=CSV_DIR, conn=None):
    """
    Import all CSV files from a directory.

    Returns (total_rows_inserted, num_files_processed).
    """
    close_conn = False
    if conn is None:
        conn = get_db()
        close_conn = True

    csv_files = sorted(Path(csv_dir).glob("*.csv"))
    total = 0
    file_count = 0

    for csv_file in csv_files:
        rows = import_csv(str(csv_file), conn)
        total += rows
        file_count += 1

    if close_conn:
        conn.close()

    return total, file_count


# ---------------------------------------------------------------------------
# M/M/c Queuing Model
# ---------------------------------------------------------------------------
def erlang_c(c, rho):
    """
    Erlang-C probability that an arriving passenger must wait.

    Args:
        c: number of servers (screening lanes)
        rho: utilization = lambda / (c * mu), must be < 1
    """
    if rho >= 1.0:
        return 1.0
    if rho <= 0:
        return 0.0
    if c <= 0:
        return 1.0

    a = c * rho

    log_ac_over_cfact = c * math.log(a) - sum(math.log(i) for i in range(1, c + 1))
    ac_over_cfact = math.exp(log_ac_over_cfact)

    numerator = ac_over_cfact / (1 - rho)

    summation = 0.0
    for k in range(c):
        if k == 0:
            summation += 1.0
        else:
            log_term = k * math.log(a) - sum(math.log(i) for i in range(1, k + 1))
            summation += math.exp(log_term)

    denominator = summation + numerator
    return numerator / denominator


def estimate_wait_time(throughput_per_hour, num_lanes, service_rate_per_lane=150):
    """
    Estimate wait time in minutes using M/M/c queuing model.

    Args:
        throughput_per_hour: passengers arriving per hour (lambda)
        num_lanes: number of open screening lanes (c)
        service_rate_per_lane: passengers one lane can process per hour (mu)

    Returns:
        dict with utilization, prob_wait, wait_minutes, num_lanes
    """
    lam = throughput_per_hour
    mu = service_rate_per_lane
    c = max(1, num_lanes)
    rho = lam / (c * mu)

    if rho >= 1.0:
        return {
            "utilization": rho,
            "prob_wait": 1.0,
            "wait_minutes": min(rho * 30, 120),
            "num_lanes": c,
        }

    prob_wait = erlang_c(c, rho)
    wait_hours = prob_wait / (c * mu - lam)
    wait_minutes = wait_hours * 60

    return {
        "utilization": round(rho, 4),
        "prob_wait": round(prob_wait, 4),
        "wait_minutes": round(max(0, wait_minutes), 2),
        "num_lanes": c,
    }


def _estimate_lanes(airport_code, hour, conn):
    """Estimate open lanes from airport peak throughput and time of day."""
    row = conn.execute(
        "SELECT MAX(throughput) FROM throughput WHERE airport_code = ?",
        (airport_code,),
    ).fetchone()

    if not row or not row[0]:
        return 4

    peak = row[0]
    total_lanes = max(2, math.ceil(peak / (150 * 0.85)))

    hour_fractions = {
        range(0, 5): 0.2,
        range(5, 7): 0.5,
        range(7, 10): 0.9,
        range(10, 15): 0.7,
        range(15, 19): 0.85,
        range(19, 22): 0.6,
        range(22, 24): 0.3,
    }

    fraction = 0.5
    for r, f in hour_fractions.items():
        if hour in r:
            fraction = f
            break

    return max(1, round(total_lanes * fraction))


def compute_wait_estimates(conn=None):
    """
    Compute wait time estimates for all throughput records.

    Returns number of estimates computed.
    """
    close_conn = False
    if conn is None:
        conn = get_db()
        close_conn = True

    rows = conn.execute(
        "SELECT date, hour, airport_code, checkpoint, throughput FROM throughput"
    ).fetchall()

    batch = []
    for date, hour, airport, checkpoint, throughput in rows:
        num_lanes = _estimate_lanes(airport, hour, conn)
        result = estimate_wait_time(throughput, num_lanes, 150)

        batch.append((
            date, hour, airport, checkpoint, throughput,
            result["num_lanes"], result["utilization"], result["wait_minutes"],
        ))

        if len(batch) >= 5000:
            conn.executemany("""
                INSERT OR REPLACE INTO wait_estimates
                    (date, hour, airport_code, checkpoint, throughput,
                     num_lanes_estimate, utilization, estimated_wait_minutes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
            conn.commit()
            batch = []

    if batch:
        conn.executemany("""
            INSERT OR REPLACE INTO wait_estimates
                (date, hour, airport_code, checkpoint, throughput,
                 num_lanes_estimate, utilization, estimated_wait_minutes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, batch)
        conn.commit()

    if close_conn:
        conn.close()

    return len(rows)


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------
def export_training_data(output_path="data/training_data.csv", airport_code=None, conn=None):
    """
    Export a flat CSV joining throughput + wait estimates for ML training.

    Returns number of rows exported.
    """
    close_conn = False
    if conn is None:
        conn = get_db()
        close_conn = True

    where = ""
    params = ()
    if airport_code:
        where = "WHERE t.airport_code = ?"
        params = (airport_code.upper(),)

    query = f"""
        SELECT t.date, t.hour, t.airport_code, t.checkpoint, t.throughput,
               t.day_of_week, t.month, t.week_of_year, t.is_weekend, t.is_holiday_season,
               w.num_lanes_estimate, w.utilization, w.estimated_wait_minutes
        FROM throughput t
        LEFT JOIN wait_estimates w
            ON t.date = w.date
            AND t.hour = w.hour
            AND t.airport_code = w.airport_code
            AND t.checkpoint = w.checkpoint
        {where}
        ORDER BY t.airport_code, t.date, t.hour
    """

    df = pd.read_sql_query(query, conn, params=params)

    if not df.empty:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)

    if close_conn:
        conn.close()

    return len(df)