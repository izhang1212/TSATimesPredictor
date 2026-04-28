"use client";

import { useEffect, useState, useMemo } from "react";
import { Search } from "lucide-react";
import { fetchAirports, type Airport } from "@/lib/api";

export default function AirportsPage() {
    const [airports, setAirports] = useState<Airport[]>([]);
    const [query, setQuery] = useState("");
    const [loading, setLoading] = useState(true);

    // Fetch airport list once on mount
    useEffect(() => {
        fetchAirports()
            .then((data) =>
                setAirports([...data].sort((a, b) => a.code.localeCompare(b.code)))
            )
            .catch((err) => console.error("Failed to load airports:", err))
            .finally(() => setLoading(false));
    }, []);

    // Filter across code, name, city, state
    const filtered = useMemo(() => {
        const q = query.trim().toLowerCase();
        if (!q) return airports;
        return airports.filter((a) => {
            return (
                a.code.toLowerCase().includes(q) ||
                a.name.toLowerCase().includes(q) ||
                a.city.toLowerCase().includes(q) ||
                a.state.toLowerCase().includes(q) ||
                a.state_full.toLowerCase().includes(q)
            );
        });
    }, [airports, query]);

    return (
        <main className="min-h-screen relative">
            {/* Background gradient — same as About / How It Works */}
            <div
                className="fixed inset-0 -z-10"
                style={{
                    background:
                        "radial-gradient(ellipse at top, #F5EFE3 0%, #FAF8F4 30%, #F5EFE3 70%, #E8DFCD 100%)",
                }}
            />

            {/* Header */}
            <section className="relative px-10 pt-32 pb-12">
                <div className="absolute top-0 left-0 right-0 h-32 bg-gradient-to-b from-stone-soft/15 to-transparent pointer-events-none" />

                <div className="max-w-5xl mx-auto text-center">
                    <div className="text-xs tracking-[0.3em] uppercase text-amber-dark mb-4">
                        Coverage
                    </div>
                    <h1 className="font-serif text-4xl md:text-6xl text-stone leading-tight mb-6">
                        Supported Airports
                    </h1>
                    <div className="mx-auto mb-6 h-px w-24 bg-amber" />
                    <p className="text-stone-soft leading-relaxed max-w-2xl mx-auto">
                        WaitWise currently predicts wait times at{" "}
                        <span className="text-stone font-medium">{airports.length}</span>{" "}
                        major US airports. Coverage expands as we add new data sources.
                    </p>
                </div>
            </section>

            {/* Search bar */}
            <section className="relative px-10 pb-8">
                <div className="max-w-3xl mx-auto">
                    <div className="bg-cream rounded-full shadow-lg flex items-center px-6 py-4 gap-3 border border-line">
                        <Search className="w-5 h-5 text-stone-soft flex-shrink-0" />
                        <input
                            type="text"
                            placeholder="Search by airport code, name, city, or state"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            className="bg-transparent outline-none text-stone placeholder:text-stone-soft text-sm w-full"
                        />
                        {query && (
                            <button
                                onClick={() => setQuery("")}
                                className="text-xs text-stone-soft hover:text-stone uppercase tracking-wider flex-shrink-0"
                            >
                                Clear
                            </button>
                        )}
                    </div>
                    {query && (
                        <div className="text-center text-stone-soft text-sm mt-3">
                            {filtered.length} {filtered.length === 1 ? "match" : "matches"}
                        </div>
                    )}
                </div>
            </section>

            {/* List */}
            <section className="relative px-10 pb-32">
                <div className="max-w-5xl mx-auto">
                    {loading && (
                        <div className="text-center text-stone-soft py-12">
                            Loading airports...
                        </div>
                    )}

                    {!loading && filtered.length === 0 && (
                        <div className="text-center text-stone-soft py-12">
                            No airports match your search.
                        </div>
                    )}

                    <div className="flex flex-col gap-6">
                        {filtered.map((airport) => (
                            <AirportRow key={airport.code} airport={airport} />
                        ))}
                    </div>
                </div>

                <div className="absolute bottom-0 left-0 right-0 h-40 bg-gradient-to-b from-transparent to-stone-soft/25 pointer-events-none" />
            </section>
        </main>
    );
}

// ---------------------------------------------------------------------------
// Row: text on left, image on right
// ---------------------------------------------------------------------------
function AirportRow({ airport }: { airport: Airport }) {
    const imageSrc = `/images/airports/${airport.code}.jpg`;

    return (
        <div className="bg-cream/60 backdrop-blur-sm rounded-2xl shadow-md hover:shadow-xl transition-shadow border border-line/50 overflow-hidden grid md:grid-cols-2 items-stretch">
            {/* Text on left */}
            <div className="p-8 flex flex-col justify-center">
                <div className="text-xs tracking-[0.3em] uppercase text-stone-soft mb-2">
                    {airport.state}
                </div>
                <div className="font-serif text-5xl text-stone leading-none mb-3">
                    {airport.code}
                </div>
                <div className="font-serif text-xl text-stone mb-1">
                    {airport.name}
                </div>
                <div className="text-stone-soft text-sm">
                    {airport.city}, {airport.state}
                </div>
            </div>

            {/* Image on right */}
            <div className="relative aspect-[4/3] md:aspect-auto md:min-h-[220px] bg-stone-soft/10">
                {/* Amber gradient fallback */}
                <div className="absolute inset-0 bg-gradient-to-br from-amber to-amber-dark" />
                {/* Photo overlay */}
                <div
                    className="absolute inset-0 bg-cover bg-center"
                    style={{ backgroundImage: `url('${imageSrc}')` }}
                />
            </div>
        </div>
    );
}