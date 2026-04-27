"use client";

import type { PredictionResult as PredictionResultType } from "@/lib/api";

const TIER_LABELS: Record<PredictionResultType["tier"], string> = {
    short: "Short Wait",
    moderate: "Moderate Wait",
    busy: "Busy",
    heavy: "Heavy Wait",
};

// Severity dot logic based on minutes (per your spec, not the model's tier)
function getSeverity(minutes: number): {
    color: string;
    label: string;
    glow: string;
} {
    if (minutes < 15) {
        return {
            color: "bg-emerald-500",
            glow: "shadow-[0_0_30px_rgba(16,185,129,0.6)]",
            label: "Low",
        };
    }
    if (minutes < 35) {
        return {
            color: "bg-amber-400",
            glow: "shadow-[0_0_30px_rgba(251,191,36,0.6)]",
            label: "Moderate",
        };
    }
    return {
        color: "bg-rose-500",
        glow: "shadow-[0_0_30px_rgba(244,63,94,0.6)]",
        label: "High",
    };
}

export default function PredictionResult({
    result,
}: {
    result: PredictionResultType;
}) {
    const minutes = Math.round(result.prediction_minutes);
    const low = Math.round(result.range_low);
    const high = Math.round(result.range_high);
    const severity = getSeverity(minutes);

    // Format date as e.g. "Thu, Apr 30"
    const dateObj = new Date(result.date + "T00:00:00");
    const formattedDate = dateObj.toLocaleDateString("en-US", {
        weekday: "short",
        month: "short",
        day: "numeric",
    });

    // Format hour as 12-hour
    const hour12 = result.hour % 12 === 0 ? 12 : result.hour % 12;
    const ampm = result.hour < 12 ? "AM" : "PM";
    const formattedTime = `${hour12}:00 ${ampm}`;

    return (
        <div className="w-full max-w-3xl -mt-2">
            {/* Connector dot/line so it visually attaches to the search bar */}
            <div className="flex justify-center">
                <div className="w-px h-6 bg-cream/40" />
            </div>

            {/* Main panel */}
            <div className="bg-cream rounded-3xl shadow-2xl px-8 py-6 flex items-center gap-8">
                {/* Left: severity circle */}
                <div className="flex-shrink-0 flex flex-col items-center gap-2">
                    <div
                        className={`w-20 h-20 rounded-full ${severity.color} ${severity.glow} flex items-center justify-center leading-none`}
                    >
                        <span className="font-serif text-3xl text-white leading-none -translate-y-1">{minutes}</span>
                    </div>
                    <span className="text-xs tracking-[0.2em] uppercase text-stone-soft font-medium">
                        {severity.label}
                    </span>
                </div>

                {/* Vertical divider */}
                <div className="w-px self-stretch bg-line" />

                {/* Center: main prediction info */}
                <div className="flex-1 text-left">
                    <div className="text-xs tracking-[0.25em] uppercase text-stone-soft mb-1">
                        Predicted Wait
                    </div>
                    <div className="font-serif text-3xl text-stone leading-tight">
                        {minutes} <span className="text-xl text-stone-soft">minutes</span>
                    </div>
                    <div className="text-stone-soft text-sm mt-1">
                        Range: {low}–{high} min
                    </div>
                </div>

                {/* Right: context info */}
                <div className="flex-shrink-0 text-right border-l border-line pl-6">
                    <div className="text-xs tracking-[0.25em] uppercase text-stone-soft mb-1">
                        {result.airport_code}
                    </div>
                    <div className="text-stone text-sm font-medium">{formattedDate}</div>
                    <div className="text-stone-soft text-sm">{formattedTime}</div>
                    <div
                        className={`mt-2 inline-block text-xs tracking-wider uppercase font-medium px-2 py-0.5 rounded ${minutes < 15
                                ? "bg-emerald-50 text-emerald-800"
                                : minutes < 35
                                    ? "bg-amber-50 text-amber-900"
                                    : "bg-rose-50 text-rose-900"
                            }`}
                    >
                        {TIER_LABELS[result.tier]}
                    </div>
                </div>
            </div>

            {/* Tiny disclaimer below */}
            <div className="text-center text-xs text-cream/70 mt-3 tracking-wide">
                Based on historical patterns. Allow buffer time when traveling.
            </div>
        </div>
    );
}