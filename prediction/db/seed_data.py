"""
seed_data.py - generate synthetic normalized CSVs for testing

Writes:
    data/normalized/wait_times.csv
    data/normalized/throughput.csv
    data/normalized/flights.csv
    data/normalized/weather.csv

Generates realistic-ish patterns so the model has something to learn:
    - Higher wait times at peak travel hours (6-9am, 4-7pm)
    - Weekend dips and peaks
    - Seasonal variation (summer highs, winter moderate)
    - Correlated throughput, flight volume, and wait times
    - Occasional weather events
    - Small random noise so the model isn't learning a perfect formula

Default: 120 days of hourly data for 5 representative airports.
"""

import os
import random
from datetime import date, timedelta

import numpy as np
import pandas as pd

from config import PREDICTION_DIR
NORMALIZED_DIR = os.path.join(PREDICTION_DIR, "data", "normalized")

# Small subset for fast testing - full 40 airports would generate ~5M rows
SEED_AIRPORTS = ["JFK", "LGA", "EWR", "ATL", "LAX"]

# Each airport has a baseline wait time profile (min, peak multiplier)
AIRPORT_PROFILES = {
    "JFK": {"base_wait": 18, "volatility": 6, "throughput_base": 1800},
    "LGA": {"base_wait": 15, "volatility": 5, "throughput_base": 1200},
    "EWR": {"base_wait": 16, "volatility": 5, "throughput_base": 1500},
    "ATL": {"base_wait": 14, "volatility": 4, "throughput_base": 2500},
    "LAX": {"base_wait": 17, "volatility": 6, "throughput_base": 2200},
}

SEED_DAYS = 120
START_DATE = date(2025, 10, 1)
RNG_SEED = 42


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def hour_of_day_multiplier(hour):
    """Two peaks: morning rush and evening rush."""
    # Gaussian bumps around 7am and 5pm
    morning = np.exp(-((hour - 7) ** 2) / 4)
    evening = np.exp(-((hour - 17) ** 2) / 5)
    baseline = 0.3  # floor so we're never at zero
    return baseline + 1.2 * morning + 1.0 * evening


def day_of_week_multiplier(dow):
    """Monday-Friday travel patterns. Sunday evening and Monday morning peak."""
    # 0=Mon, 6=Sun
    weights = {0: 1.15, 1: 1.05, 2: 1.00, 3: 1.05, 4: 1.20, 5: 0.85, 6: 1.00}
    return weights[dow]


def season_multiplier(month):
    """Summer high, holiday spikes, January low."""
    monthly = {
        1: 0.85, 2: 0.85, 3: 0.95, 4: 1.00, 5: 1.05, 6: 1.15,
        7: 1.20, 8: 1.20, 9: 1.05, 10: 1.00, 11: 1.15, 12: 1.20,
    }
    return monthly[month]


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------
def generate():
    random.seed(RNG_SEED)
    np.random.seed(RNG_SEED)
    os.makedirs(NORMALIZED_DIR, exist_ok=True)

    wait_rows = []
    throughput_rows = []
    flight_rows = []
    weather_rows = []

    for airport in SEED_AIRPORTS:
        profile = AIRPORT_PROFILES[airport]
        base = profile["base_wait"]
        volatility = profile["volatility"]
        throughput_base = profile["throughput_base"]

        for day_offset in range(SEED_DAYS):
            d = START_DATE + timedelta(days=day_offset)
            date_str = d.strftime("%Y-%m-%d")
            dow = d.weekday()
            month = d.month

            # One weather event per airport every ~15 days
            is_weather_day = random.random() < 0.07
            weather_temp = 60 + 20 * np.sin(2 * np.pi * d.timetuple().tm_yday / 365)
            weather_precip = 0.0
            weather_wind = 5 + random.random() * 10
            weather_conditions = "Clear"
            if is_weather_day:
                weather_precip = round(random.uniform(0.4, 1.5), 2)
                weather_wind = round(random.uniform(20, 40), 1)
                weather_conditions = random.choice(["Rain", "Storm", "Snow"])

            for hour in range(24):
                # --- Wait time ---
                mult = (
                    hour_of_day_multiplier(hour)
                    * day_of_week_multiplier(dow)
                    * season_multiplier(month)
                )
                weather_penalty = 5 if is_weather_day and hour in range(6, 22) else 0
                noise = np.random.normal(0, volatility * 0.3)
                wait = base * mult + weather_penalty + noise
                wait = max(1.0, round(wait, 1))

                wait_rows.append({
                    "airport_code": airport,
                    "date": date_str,
                    "hour": hour,
                    "wait_minutes": wait,
                    "user_reported": int(wait + np.random.normal(0, 2)),
                    "source": "seed",
                })

                # --- Throughput ---
                # Correlated with wait multiplier but with more noise
                throughput = throughput_base * mult * 0.5 + np.random.normal(0, 150)
                throughput = max(0, int(throughput))
                throughput_rows.append({
                    "airport_code": airport,
                    "date": date_str,
                    "hour": hour,
                    "checkpoint": "Main Checkpoint",
                    "passengers": throughput,
                })

                # --- Flights ---
                num_departures = max(0, int(10 * mult + np.random.normal(0, 2)))
                # International share varies by airport
                intl_share = {"JFK": 0.35, "LAX": 0.25, "EWR": 0.20, "ATL": 0.10, "LGA": 0.02}
                num_international = int(num_departures * intl_share.get(airport, 0.10))
                num_cancelled = 1 if is_weather_day and random.random() < 0.3 else 0
                avg_delay = round(15.0 + random.random() * 10, 1) if is_weather_day else round(5.0 + random.random() * 5, 1)

                flight_rows.append({
                    "airport_code": airport,
                    "date": date_str,
                    "hour": hour,
                    "num_departures": num_departures,
                    "num_cancelled": num_cancelled,
                    "num_international": num_international,
                    "avg_delay_min": avg_delay,
                })

                # --- Weather (one row per hour, same values all day for simplicity) ---
                weather_rows.append({
                    "airport_code": airport,
                    "date": date_str,
                    "hour": hour,
                    "temp_f": round(weather_temp + np.random.normal(0, 2), 1),
                    "wind_mph": round(weather_wind + np.random.normal(0, 1), 1),
                    "precip_in": weather_precip,
                    "conditions": weather_conditions,
                })

    pd.DataFrame(wait_rows).to_csv(os.path.join(NORMALIZED_DIR, "wait_times.csv"), index=False)
    pd.DataFrame(throughput_rows).to_csv(os.path.join(NORMALIZED_DIR, "throughput.csv"), index=False)
    pd.DataFrame(flight_rows).to_csv(os.path.join(NORMALIZED_DIR, "flights.csv"), index=False)
    pd.DataFrame(weather_rows).to_csv(os.path.join(NORMALIZED_DIR, "weather.csv"), index=False)

    return {
        "airports": len(SEED_AIRPORTS),
        "days": SEED_DAYS,
        "wait_times_rows": len(wait_rows),
        "throughput_rows": len(throughput_rows),
        "flights_rows": len(flight_rows),
        "weather_rows": len(weather_rows),
    }