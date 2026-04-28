// lib/api.ts
// Functions for calling the WaitWise FastAPI backend.

const API_BASE = "http://localhost:8000";

export type Tier = "short" | "moderate" | "busy" | "heavy";

export type PredictionResult = {
    airport_code: string;
    date: string;
    hour: number;
    prediction_minutes: number;
    tier: Tier;
    range_low: number;
    range_high: number;
    model_predictions: {
        lightgbm: number;
        prophet: number;
    };
    weights: {
        lightgbm: number;
        prophet: number;
    };
};

export type Airport = {
  code: string;
  name: string;
  city: string;
  state: string;       
  state_full: string;  
};

export async function fetchAirports(): Promise<Airport[]> {
    const res = await fetch(`${API_BASE}/api/airports`);
    if (!res.ok) {
        throw new Error(`Failed to fetch airports: ${res.statusText}`);
    }
    return res.json();
}

export async function fetchPrediction(
    airport_code: string,
    date: string,
    hour: number
): Promise<PredictionResult> {
    const res = await fetch(`${API_BASE}/api/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ airport_code, date, hour }),
    });

    if (!res.ok) {
        const errorBody = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(errorBody.detail || "Prediction failed");
    }

    return res.json();
}