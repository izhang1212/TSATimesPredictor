"use client";

import { useState } from "react";
import { Plane, Calendar, Clock, Search } from "lucide-react";

export default function Hero() {
  const [airport, setAirport] = useState("");
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");

  const handleSearch = () => {
    // Wiring to API comes later — just log for now
    console.log({ airport, date, time });
  };

  return (
    <section
      className="relative h-screen w-full flex flex-col items-center justify-center text-center px-6"
      style={{
        backgroundImage:
          "linear-gradient(rgba(20, 18, 16, 0.35), rgba(20, 18, 16, 0.55)), url('/images/hero.png')",
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}
    >
      {/* Top nav */}
      <nav className="absolute top-0 left-0 right-0 flex justify-between items-center px-10 py-6 text-cream">
        <div className="text-2xl tracking-wide font-serif">
          Wait<span className="text-amber">Wise</span>
        </div>
        <div className="flex gap-8 text-sm tracking-wider uppercase">
          <a href="#about" className="hover:text-amber transition-colors">About</a>
          <a href="#how" className="hover:text-amber transition-colors">How it works</a>
        </div>
      </nav>

      {/* Headline */}
      <div className="max-w-3xl text-cream">
        <h1 className="font-serif text-5xl md:text-7xl tracking-tight leading-tight">
          Know the wait <br /> before you go
        </h1>
        <div className="mx-auto my-6 h-px w-24 bg-amber" />
        <p className="text-base md:text-lg tracking-wide opacity-90 max-w-xl mx-auto">
          Predicts TSA security wait times using LightGBM and Prophet for major US airports
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
              className="bg-transparent outline-none text-stone placeholder:text-stone-soft text-sm w-full"
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
            className="bg-amber hover:bg-amber-dark transition-colors text-cream rounded-full px-6 py-3 flex items-center gap-2 text-sm tracking-wider uppercase"
          >
            <Search className="w-4 h-4" />
            Search
          </button>
        </div>
      </div>

      {/* Scroll cue */}
      <div className="absolute bottom-10 text-cream text-xs tracking-[0.3em] uppercase opacity-70">
        ↓ Scroll for airports
      </div>
    </section>
  );
}