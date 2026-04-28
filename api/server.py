"""
server.py - FastAPI backend exposing the TSA wait time prediction model.

Run with:
    uvicorn api.server:app --reload --port 8000

The frontend (Next.js on http://localhost:3000) calls these endpoints.
"""

import sys
from pathlib import Path

# Make the prediction/ folder importable
PREDICTION_DIR = Path(__file__).parent.parent / "prediction"
sys.path.insert(0, str(PREDICTION_DIR))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from prediction.models.ensemble import predict_wait_time
from prediction.config import AIRPORT_INFO, AIRPORTS

US_STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii",
    "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine",
    "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska",
    "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico",
    "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island",
    "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas",
    "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}

app = FastAPI(
    title="WaitWise API",
    description="TSA wait time prediction service",
    version="0.1.0",
)

# Allow the Next.js frontend (running on :3000) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------
class PredictionRequest(BaseModel):
    airport_code: str = Field(..., description="3-letter IATA code, e.g. 'JFK'")
    date: str = Field(..., description="YYYY-MM-DD")
    hour: int = Field(..., ge=0, le=23, description="Hour of day, 0-23")


class AirportInfo(BaseModel):
    code: str
    name: str
    city: str
    state: str
    state_full: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    """Health check."""
    return {"status": "ok", "service": "waitwise-api"}


@app.get("/api/airports", response_model=list[AirportInfo])
def list_airports():
    """Return all supported airports for the frontend carousel and dropdown."""
    return [
        AirportInfo(
            code=code,
            name=info[0],
            city=info[1],
            state=info[2],
            state_full=US_STATES.get(info[2], info[2]),
        )
        for code, info in AIRPORT_INFO.items()
    ]


@app.post("/api/predict")
def predict(req: PredictionRequest):
    """
    Predict TSA wait time for a given airport, date, and hour.
    Returns the full prediction dict from the ensemble.
    """
    code = req.airport_code.upper()
    if code not in AIRPORTS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown airport code: {code}. Scroll down to see available airport locations.",
        )

    try:
        result = predict_wait_time(code, req.date, req.hour)
        return result
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Models not trained yet. Run prediction/main.py first. ({e})",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))