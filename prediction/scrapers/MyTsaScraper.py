"""
airportscraper.py
=================
Pulls real-time TSA wait times from the free MyTSA government API
every 30 minutes and saves them to daily CSV files.

No API key required.

Usage:
    python airportscraper.py              # run continuously (every 30 min)
    python airportscraper.py --once       # run once and exit
    python airportscraper.py --interval 15  # custom interval in minutes

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
import xml.etree.ElementTree as ET
from datetime import datetime

import requests

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
OUTPUT_DIR = "data/raw/wait_times"
INTERVAL_MINUTES = 30
DELAY_BETWEEN_CALLS = 1.5  # seconds between API calls (be polite)

MYTSA_URL = "http://apps.tsa.dhs.gov/MyTSAWebService/GetTSOWaitTimes.ashx"
MYTSA_METADATA_URL = "http://www.tsa.gov/data/apcp.xml"

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
    "checkpoint",
    "wait_minutes",
    "precheck",
    "reported_at",
]


# ---------------------------------------------------------------------------
# Metadata cache (maps checkpoint IDs to names)
# ---------------------------------------------------------------------------
_checkpoint_names = {}


def load_metadata():
    """
    Load airport/checkpoint metadata from TSA's XML file.
    Maps internal IDs to human-readable checkpoint names.
    """
    global _checkpoint_names
    try:
        resp = requests.get(MYTSA_METADATA_URL, timeout=30)
        if resp.status_code != 200:
            return
        root = ET.fromstring(resp.content)
        for airport in root.findall(".//airport"):
            code = airport.findtext("code", "").strip()
            for cp in airport.findall(".//checkpoint"):
                cp_id = cp.findtext("id", "").strip()
                cp_name = cp.findtext("longname", "") or cp.findtext("shortname", "")
                if cp_id and cp_name:
                    _checkpoint_names[cp_id] = cp_name.strip()
    except Exception:
        pass


def get_checkpoint_name(cp_id):
    """Resolve a checkpoint ID to its name, or return the ID."""
    return _checkpoint_names.get(str(cp_id), str(cp_id))


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
def fetch_wait_times(airport_code):
    """
    Fetch wait times for one airport from the free MyTSA API.

    Returns list of dicts:
        [{"checkpoint": "...", "wait_minutes": 15, "precheck": 0, "reported_at": "..."}, ...]
    """
    try:
        resp = requests.get(
            MYTSA_URL,
            params={"ap": airport_code, "output": "json"},
            timeout=30,
        )
        if resp.status_code != 200:
            return []

        data = resp.json()
    except (requests.RequestException, json.JSONDecodeError):
        return []

    # The API returns a list of recent wait time reports
    # Each entry has: checkpoint_id, wait_time, created_at, precheck, etc.
    results = []

    if isinstance(data, list):
        entries = data
    elif isinstance(data, dict):
        entries = data.get("WaitTimes", data.get("waitTimes", []))
        if not entries and "WaitTime" in data:
            entries = data["WaitTime"]
            if isinstance(entries, dict):
                entries = [entries]
    else:
        return []

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        # The API field names vary — try common variants
        wait = (
            entry.get("wait_time")
            or entry.get("WaitTime")
            or entry.get("waitTime")
            or entry.get("mins")
            or entry.get("Wait")
        )
        checkpoint = (
            entry.get("CheckpointIndex")
            or entry.get("checkpoint_id")
            or entry.get("checkpoint")
            or entry.get("Checkpoint")
            or ""
        )
        precheck = (
            entry.get("PreCheck")
            or entry.get("precheck")
            or entry.get("pre_check")
            or 0
        )
        created = (
            entry.get("Created_Datetime")
            or entry.get("created_at")
            or entry.get("CreatedAt")
            or entry.get("created")
            or ""
        )

        if wait is not None:
            try:
                results.append({
                    "checkpoint": get_checkpoint_name(checkpoint),
                    "wait_minutes": int(float(str(wait))),
                    "precheck": 1 if str(precheck).lower() in ("1", "true", "yes") else 0,
                    "reported_at": str(created),
                })
            except (ValueError, TypeError):
                continue

    return results


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------
def get_csv_path(dt=None):
    """Get path for today's CSV: data/day/2026-04-04.csv"""
    if dt is None:
        dt = datetime.now()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return os.path.join(OUTPUT_DIR, f"{dt.strftime('%Y-%m-%d')}.csv")


def ensure_header(filepath):
    """Write CSV header if the file doesn't exist yet."""
    if not os.path.exists(filepath):
        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)


def append_rows(filepath, rows):
    """Append rows to a CSV file."""
    with open(filepath, "a", newline="") as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)


# ---------------------------------------------------------------------------
# Collection
# ---------------------------------------------------------------------------
def collect_once():
    """
    Hit every airport once, save results to today's CSV.

    Returns (rows_saved, airports_with_data, airports_attempted).
    """
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    csv_path = get_csv_path(now)
    ensure_header(csv_path)

    rows = []
    airports_with_data = 0

    for code in AIRPORTS:
        wait_times = fetch_wait_times(code)

        if wait_times:
            airports_with_data += 1
            for wt in wait_times:
                rows.append([
                    timestamp,
                    code,
                    wt["checkpoint"],
                    wt["wait_minutes"],
                    wt["precheck"],
                    wt["reported_at"],
                ])
        else:
            # No data — still log that we checked (with -1 as sentinel)
            rows.append([timestamp, code, "", -1, 0, ""])

        time.sleep(DELAY_BETWEEN_CALLS)

    append_rows(csv_path, rows)
    return len(rows), airports_with_data, len(AIRPORTS)


def run_continuous(interval_minutes=INTERVAL_MINUTES):
    """
    Run collection loop forever. Ctrl+C to stop.
    """
    print(f"Airport Scraper started")
    print(f"  Airports: {len(AIRPORTS)}")
    print(f"  Interval: every {interval_minutes} minutes")
    print(f"  Output:   {OUTPUT_DIR}/")
    print(f"  Press Ctrl+C to stop\n")

    # Try to load checkpoint metadata on startup
    print("Loading checkpoint metadata...")
    load_metadata()
    if _checkpoint_names:
        print(f"  Loaded {len(_checkpoint_names)} checkpoint names")
    else:
        print("  Could not load metadata (checkpoint IDs will be used as-is)")
    print()

    while True:
        start = time.time()
        now = datetime.now()

        print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Collecting...", end=" ", flush=True)

        try:
            rows, with_data, total = collect_once()
            print(f"{rows} rows from {with_data}/{total} airports -> {get_csv_path()}")
        except Exception as e:
            print(f"ERROR: {e}")

        elapsed = time.time() - start
        sleep_time = max(0, (interval_minutes * 60) - elapsed)

        if sleep_time > 0:
            next_run = datetime.now().strftime("%H:%M:%S")
            mins_left = int(sleep_time // 60)
            print(f"  Next collection in {mins_left} minutes...")
            time.sleep(sleep_time)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
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
        load_metadata()
        rows, with_data, total = collect_once()
        print(f"Collected {rows} rows from {with_data}/{total} airports")
        print(f"Saved to {get_csv_path()}")
    else:
        try:
            run_continuous(interval)
        except KeyboardInterrupt:
            print("\nStopped.")