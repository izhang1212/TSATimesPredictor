"""
airportscraper_paid.py
======================
Pulls real-time TSA wait times from TSAWaitTimes.com API
every 30 minutes and saves them to daily CSV files.

Requires a TSAWaitTimes.com API key stored in .env:
    TSA_API_KEY=your_key_here

Usage:
    python airportscraper_paid.py              # run continuously (every 30 min)
    python airportscraper_paid.py --once       # run once and exit
    python airportscraper_paid.py --interval 15  # custom interval in minutes

Output:
    data/day/2026-04-04.csv
    data/day/2026-04-05.csv
    ...
"""

import os
import csv
import sys
import time
import json
from datetime import datetime

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
load_dotenv()
API_KEY = os.getenv("TSA_API_KEY")

BASE_URL = "https://www.tsawaittimes.com/api"
OUTPUT_DIR = "data/raw/wait_times"
INTERVAL_MINUTES = 30
DELAY_BETWEEN_CALLS = 1.0

AIRPORTS = [
    # Northeast
    "JFK", "LGA", "EWR", "BOS", "PHL", "DCA", "IAD", "BWI", "BDL", "PIT",
    # Southeast
    "ATL", "MIA", "FLL", "MCO", "CLT", "TPA", "BNA", "RDU", "JAX",
    # Midwest
    "ORD", "MDW", "DTW", "MSP", "CLE", "MKE", "STL",
    # West
    "LAX", "SFO", "SAN", "SEA", "PDX", "LAS", "DEN", "PHX",
    # Texas
    "DFW", "IAH", "AUS", "DAL", "HOU", "SAT",
]

CSV_HEADERS = [
    "timestamp",
    "airport_code",
    "rightnow_minutes",
    "user_reported_minutes",
    "has_precheck",
    "has_ground_stops",
    "has_ground_delays",
    "has_general_delays",
    "h00", "h01", "h02", "h03", "h04", "h05",
    "h06", "h07", "h08", "h09", "h10", "h11",
    "h12", "h13", "h14", "h15", "h16", "h17",
    "h18", "h19", "h20", "h21", "h22", "h23",
]


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
def fetch_airport(api_key, code):
    """
    Fetch current status for one airport from TSAWaitTimes.com.

    Returns dict or None.
    """
    url = f"{BASE_URL}/airport/{api_key}/{code}/json"
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            return resp.json()
    except (requests.RequestException, json.JSONDecodeError):
        pass
    return None


def parse_hourly(data):
    """
    Parse estimated_hourly_times into a dict of {hour: wait_minutes}.

    Returns dict with keys 0-23, values are floats or None.
    """
    hourly = {}
    entries = data.get("estimated_hourly_times", [])

    for entry in entries:
        timeslot = entry.get("timeslot", "")
        waittime = entry.get("waittime", None)

        hour = parse_timeslot(timeslot)
        if hour is not None and waittime is not None:
            try:
                hourly[hour] = float(waittime)
            except (ValueError, TypeError):
                hourly[hour] = None

    return hourly


def parse_timeslot(timeslot):
    """Parse '5 am - 6 am' into integer hour 0-23."""
    if not timeslot:
        return None
    try:
        start = timeslot.split("-")[0].strip()
        parts = start.split()
        if len(parts) != 2:
            return None
        hour_num = int(parts[0])
        period = parts[1].lower()
        if period == "am":
            return 0 if hour_num == 12 else hour_num
        elif period == "pm":
            return 12 if hour_num == 12 else hour_num + 12
    except (ValueError, IndexError):
        pass
    return None


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------
def get_csv_path(dt=None):
    if dt is None:
        dt = datetime.now()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return os.path.join(OUTPUT_DIR, f"{dt.strftime('%Y-%m-%d')}.csv")


def ensure_header(filepath):
    if not os.path.exists(filepath):
        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)


def append_row(filepath, row):
    with open(filepath, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(row)


# ---------------------------------------------------------------------------
# Collection
# ---------------------------------------------------------------------------
def collect_once(api_key):
    """
    Hit every airport, save to today's CSV.

    Returns (rows_saved, airports_with_data).
    """
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    csv_path = get_csv_path(now)
    ensure_header(csv_path)

    saved = 0
    with_data = 0

    for code in AIRPORTS:
        data = fetch_airport(api_key, code)

        if data and data.get("rightnow") is not None:
            with_data += 1

            rightnow = data.get("rightnow", -1)
            user_reported = data.get("user_reported", 0)
            precheck = data.get("precheck", 0)

            faa = data.get("faa_alerts", {}) or {}
            ground_stops = 1 if faa.get("ground_stops") else 0
            ground_delays = 1 if faa.get("ground_delays") else 0
            general_delays = 1 if faa.get("general_delays") else 0

            hourly = parse_hourly(data)
            hourly_values = [hourly.get(h, "") for h in range(24)]

            row = [
                timestamp,
                code,
                rightnow,
                user_reported,
                precheck,
                ground_stops,
                ground_delays,
                general_delays,
            ] + hourly_values

            append_row(csv_path, row)
            saved += 1
        else:
            # Log failed attempt
            row = [timestamp, code, -1, 0, 0, 0, 0, 0] + [""] * 24
            append_row(csv_path, row)
            saved += 1

        time.sleep(DELAY_BETWEEN_CALLS)

    return saved, with_data


def run_continuous(api_key, interval_minutes=INTERVAL_MINUTES):
    """Run collection loop forever. Ctrl+C to stop."""
    print(f"Airport Scraper (paid API) started")
    print(f"  Airports: {len(AIRPORTS)}")
    print(f"  Interval: every {interval_minutes} minutes")
    print(f"  Output:   {OUTPUT_DIR}/")
    print(f"  Press Ctrl+C to stop\n")

    while True:
        start = time.time()
        now = datetime.now()

        print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Collecting...", end=" ", flush=True)

        try:
            rows, with_data = collect_once(api_key)
            print(f"{rows} rows, {with_data}/{len(AIRPORTS)} airports returned data -> {get_csv_path()}")
        except Exception as e:
            print(f"ERROR: {e}")

        elapsed = time.time() - start
        sleep_time = max(0, (interval_minutes * 60) - elapsed)

        if sleep_time > 0:
            mins_left = int(sleep_time // 60)
            print(f"  Next collection in {mins_left} minutes...")
            time.sleep(sleep_time)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if not API_KEY:
        print("ERROR: No API key found.")
        print("Create a .env file in your project root with:")
        print("  TSA_API_KEY=your_key_here")
        sys.exit(1)

    args = sys.argv[1:]
    interval = INTERVAL_MINUTES
    once = False

    i = 0
    while i < len(args):
        if args[i] == "--once":
            once = True
        elif args[i] == "--interval" and i + 1 < len(args):
            interval = int(args[i + 1])
            i += 1
        i += 1

    if once:
        rows, with_data = collect_once(API_KEY)
        print(f"Collected {rows} rows, {with_data}/{len(AIRPORTS)} airports had data")
        print(f"Saved to {get_csv_path()}")
    else:
        try:
            run_continuous(API_KEY, interval)
        except KeyboardInterrupt:
            print("\nStopped.")