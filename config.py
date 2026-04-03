AIRPORTS = ["LGA", "JFK", "EWR"]

STAFFING_MODIFIERS = {
    "normal": 1.0,
    "reduced": 0.85,
    "critical": 0.6
}

FEATURES = [
    "hour", "day_of_week", "month",
    "is_holiday", "is_shutdown",
    "staffing_modifier",
    "flights_next_2hrs", "pct_international"
]

TARGET = "wait_minutes"