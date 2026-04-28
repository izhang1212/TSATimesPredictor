"use client";

import { useEffect, useRef, useState } from "react";

const AIRPORTS = [
    { code: "JFK", city: "New York", state: "New York", image: "/images/airports/jfk.jpg" },
    { code: "LGA", city: "New York", state: "New York", image: "/images/airports/lga.jpg" },
    { code: "EWR", city: "Newark", state: "New Jersey", image: "/images/airports/ewr.jpg" },
    { code: "ATL", city: "Atlanta", state: "Georgia", image: "/images/airports/atl.jpg" },
    { code: "LAX", city: "Los Angeles", state: "California", image: "/images/airports/lax.jpg" },
    { code: "IAH", city: "Houston", state: "Texas", image: "/images/airports/IAH.jpg" },
    { code: "AUS", city: "Austin", state: "Texas", image: "/images/airports/AUS.jpg" },
    { code: "BOS", city: "Boston", state: "Massachusetts", image: "/images/airports/BOS.jpg" },
    { code: "MCO", city: "Orlando", state: "Florida", image: "/images/airports/MCO.jpg" },
    { code: "PHL", city: "Philadelphia", state: "Pennsylvania", image: "/images/airports/PHL.jpg" },
    { code: "PHX", city: "Phoenix", state: "Arizona", image: "/images/airports/PHX.jpg" },
    { code: "DCA", city: "Arlington", state: "Virginia", image: "/images/airports/DCA.jpg" },
    { code: "DAL", city: "Dallas", state: "Texas", image: "/images/airports/DAL.jpg" },
    { code: "JAX", city: "Jaxonville", state: "Florida", image: "/images/airports/JAX.jpg" },
    { code: "SFO", city: "San Francisco", state: "California", image: "/images/airports/SFO.jpg" },
    { code: "MIA", city: "Miami", state: "Florida", image: "/images/airports/MIA.jpg" },

];

// Duplicate the list so the loop is seamless
const TRACK = [...AIRPORTS, ...AIRPORTS, ...AIRPORTS];

export default function AirportCarousel() {
    const trackRef = useRef<HTMLDivElement>(null);
    const offsetRef = useRef(0);
    const velocityRef = useRef(0.4);
    const targetVelocityRef = useRef(0.4);

    useEffect(() => {
        let rafId: number;
        let decayId: ReturnType<typeof setTimeout> | undefined;

        const tick = () => {
            // Ease velocity toward target
            velocityRef.current += (targetVelocityRef.current - velocityRef.current) * 0.08;
            offsetRef.current -= velocityRef.current;

            const track = trackRef.current;
            if (track) {
                // When we've scrolled past one full set, snap back by that width
                // so the loop looks continuous.
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
    }, []);

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
                    {TRACK.map((airport, i) => (
                        <AirportCard key={`${airport.code}-${i}`} {...airport} />
                    ))}
                </div>
            </div>
        </section>
    );
}

function AirportCard({
  code,
  city,
  state,
  image,
}: {
  code: string;
  city: string;
  state: string;
  image: string;
}) {
  return (
    <div className="flex-shrink-0 w-108 h-96 rounded-lg overflow-hidden shadow-lg group cursor-pointer relative">
      <div
        className="absolute inset-0 bg-gradient-to-br from-amber to-amber-dark"
        aria-hidden
      />
      <div
        className="absolute inset-0 bg-cover bg-center transition-transform duration-700 group-hover:scale-105"
        style={{ backgroundImage: `url('${image}')` }}
      />
      <div className="absolute inset-0 bg-gradient-to-t from-stone via-stone/30 to-transparent" />
      <div className="absolute bottom-0 left-0 right-0 p-6 text-cream">
        <div className="font-serif text-4xl tracking-tight">{code}</div>
        <div className="text-sm tracking-wider uppercase opacity-80 mt-1">
          {city}, {state}
        </div>
      </div>
    </div>
  );
}