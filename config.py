# config.py - project config

# airports and airport metadata
AIRPORTS = [
    "JFK", "LGA", "EWR", "BOS", "PHL", "DCA", "IAD", "BWI", "BDL", "PIT",
    "ATL", "MIA", "FLL", "MCO", "CLT", "TPA", "BNA", "RDU", "JAX",
    "ORD", "MDW", "DTW", "MSP", "CLE", "MKE", "STL",
    "LAX", "SFO", "SAN", "SEA", "PDX", "LAS", "DEN", "PHX",
    "DFW", "IAH", "AUS", "DAL", "HOU", "SAT",
]

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

# staffing mods
STAFFING_MODIFIERS = {
    "normal": 1.0,
    "reduced": 0.85,
    "critical": 0.6,
}

# gov shutdown ranges
SHUTDOWN_PERIODS = [
    ("2018-12-22", "2019-01-25"),
    ("2025-03-14", "2025-03-15"), 
]

# feature cols
FEATURES = [
    # time features
    "hour", "day_of_week", "month", "week_of_year", "is_weekend",
    # volume features
    "throughput", "num_departures", "num_cancelled", "avg_delay_min",
    # international share
    "pct_international",
    # lag features
    "wait_same_hour_last_week", "wait_avg_last_4_weeks_same_hour_dow",
    # flags
    "is_holiday", "days_to_nearest_holiday", "is_shutdown",
    "staffing_modifier", "extreme_weather_flag",
]

TARGET = "wait_minutes"

# path for database
DB_PATH = "data/tsa.db"