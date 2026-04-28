"use client";

import { useState } from "react";
import { Plane, Calendar, Clock, Search, Loader2 } from "lucide-react";
import { fetchPrediction, type PredictionResult as PredictionResultType } from "@/lib/api";
import PredictionResult from "./PredictionResult";

export default function Hero() {
  const [airport, setAirport] = useState("");
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PredictionResultType | null>(null);

  const handleSearch = async () => {
    setError(null);
    setResult(null);

    if (!airport || !date || !time) {
      setError("Please fill in airport, date, and time.");
      return;
    }

    const hour = parseInt(time.split(":")[0], 10);
    if (isNaN(hour) || hour < 0 || hour > 23) {
      setError("Invalid time.");
      return;
    }

    setLoading(true);
    try {
      const prediction = await fetchPrediction(airport.toUpperCase(), date, hour);
      setResult(prediction);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section
      className="relative min-h-screen w-full flex flex-col items-center justify-center text-center px-6 py-24"
      style={{
        backgroundImage:
          "linear-gradient(rgba(20, 18, 16, 0.35), rgba(20, 18, 16, 0.55)), url('/images/hero2.jpg')",
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}
    >
      {/* Headline */}
      <div className="max-w-3xl text-cream">
        <h1 className="font-serif text-5xl md:text-7xl tracking-tight leading-tight">
          Know the wait <br /> before you go
        </h1>
        <div className="mx-auto my-6 h-px w-24 bg-amber" />
        <p className="text-base md:text-lg tracking-wide opacity-90 max-w-xl mx-auto">
          Predict TSA security wait time for major US airports using lightgbm and prophet models
        </p>
      </div>

      {/* Search bar */}
      <div className="mt-12 w-full max-w-3xl">
        <div className="bg-cream rounded-full shadow-2xl flex items-center px-2 py-2 gap-2">
          <div className="flex items-center gap-3 px-4 py-2 flex-1 border-r border-line">
            <Plane className="w-4 h-4 text-stone-soft" />
            <input
              type="text"
              placeholder="Airport"
              value={airport}
              onChange={(e) => setAirport(e.target.value.toUpperCase())}
              maxLength={3}
              className="bg-transparent outline-none text-stone placeholder:text-stone-soft text-sm w-full uppercase"
            />
          </div>

          <div className="flex items-center gap-3 px-4 py-2 flex-1 border-r border-line">
            <Calendar className="w-4 h-4 text-stone-soft" />
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="bg-transparent outline-none text-stone text-sm w-full"
            />
          </div>

          <div className="flex items-center gap-3 px-4 py-2 flex-1 border-r border-line">
            <Clock className="w-4 h-4 text-stone-soft" />
            <input
              type="time"
              value={time}
              onChange={(e) => setTime(e.target.value)}
              className="bg-transparent outline-none text-stone text-sm w-full"
            />
          </div>

          <button
            onClick={handleSearch}
            disabled={loading}
            className="bg-amber hover:bg-amber-dark transition-colors text-cream rounded-full px-6 py-3 flex items-center gap-2 text-sm tracking-wider uppercase disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Search className="w-4 h-4" />
            )}
            {loading ? "Loading" : "Search"}
          </button>
        </div>

        {error && (
          <div className="mt-4 text-rose-200 text-sm bg-rose-950/40 border border-rose-300/30 rounded-lg px-4 py-2 inline-block">
            {error}
          </div>
        )}

        {result && <PredictionResult result={result} />}
      </div>

      {!result && (
        <div className="absolute bottom-10 text-cream text-xs tracking-[0.3em] uppercase opacity-70">
          ↓ Scroll for airports
        </div>
      )}
    </section>
  );
}