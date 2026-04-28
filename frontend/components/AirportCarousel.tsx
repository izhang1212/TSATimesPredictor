"use client";

import { useEffect, useRef, useState } from "react";
import { fetchAirports, type Airport } from "@/lib/api";

export default function AirportCarousel() {
    const [airports, setAirports] = useState<Airport[]>([]);
    const trackRef = useRef<HTMLDivElement>(null);
    const offsetRef = useRef(0);
    const velocityRef = useRef(0.4);
    const targetVelocityRef = useRef(0.4);

    // Fetch airports once on mount
    useEffect(() => {
        fetchAirports()
            .then((data) => setAirports(data))
            .catch((err) => console.error("Failed to load airports:", err));
    }, []);

    // Auto-scroll loop
    useEffect(() => {
        if (airports.length === 0) return;

        let rafId: number;
        let decayId: ReturnType<typeof setTimeout> | undefined;

        const tick = () => {
            velocityRef.current +=
                (targetVelocityRef.current - velocityRef.current) * 0.08;
            offsetRef.current -= velocityRef.current;

            const track = trackRef.current;
            if (track) {
                const oneSetWidth = track.scrollWidth / 3;
                if (Math.abs(offsetRef.current) >= oneSetWidth) {
                    offsetRef.current += oneSetWidth;
                }
                track.style.transform = `translate3d(${offsetRef.current}px, 0, 0)`;
            }

            rafId = requestAnimationFrame(tick);
        };

        const onWheel = (e: WheelEvent) => {
            const boost = Math.min(Math.abs(e.deltaY) * 0.05, 4);
            targetVelocityRef.current = 0.4 + boost;
            if (decayId) clearTimeout(decayId);
            decayId = setTimeout(() => {
                targetVelocityRef.current = 0.4;
            }, 200);
        };

        rafId = requestAnimationFrame(tick);
        window.addEventListener("wheel", onWheel, { passive: true });

        return () => {
            cancelAnimationFrame(rafId);
            window.removeEventListener("wheel", onWheel);
            if (decayId) clearTimeout(decayId);
        };
    }, [airports]);

    // Build the looping track: 3 copies of the airport list for seamless scroll
    const track = airports.length > 0 ? [...airports, ...airports, ...airports] : [];

    return (
        <section className="bg-cream py-24 px-10 overflow-hidden">
            <h2 className="font-serif text-3xl md:text-4xl text-stone mb-2">
                Where are you flying from?
            </h2>
            <p className="text-stone-soft text-sm tracking-wide mb-12">
                Browse all supported airports
            </p>

            <div className="overflow-hidden">
                <div ref={trackRef} className="flex gap-6 will-change-transform">
                    {track.map((airport, i) => (
                        <AirportCard key={`${airport.code}-${i}`} airport={airport} />
                    ))}
                </div>
            </div>
        </section>
    );
}

function AirportCard({ airport }: { airport: Airport }) {
    const imageSrc = `/images/airports/${airport.code}.jpg`;

    return (
        <div className="flex-shrink-0 w-96 h-72 rounded-lg overflow-hidden shadow-lg group cursor-pointer relative">
            <div
                className="absolute inset-0 bg-gradient-to-br from-amber to-amber-dark"
                aria-hidden
            />
            <div
                className="absolute inset-0 bg-cover bg-center transition-transform duration-700 group-hover:scale-105"
                style={{ backgroundImage: `url('${imageSrc}')` }}
            />
            <div className="absolute inset-0 bg-gradient-to-t from-stone via-stone/30 to-transparent" />
            <div className="absolute bottom-0 left-0 right-0 p-6 text-cream">
                <div className="font-serif text-4xl tracking-tight">{airport.code}</div>
                <div className="text-sm tracking-wider uppercase opacity-80 mt-1">
                    {airport.city}, {airport.state}
                </div>
            </div>
        </div>
    );
}