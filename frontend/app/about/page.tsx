import Image from "next/image";

export default function AboutPage() {
    return (
        <main className="min-h-screen relative">
            {/* Layered background gradient */}
            <div
                className="fixed inset-0 -z-10"
                style={{
                    background:
                        "radial-gradient(ellipse at top, #F5EFE3 0%, #FAF8F4 30%, #F5EFE3 70%, #E8DFCD 100%)",
                }}
            />

            {/* SECTION 1: What this product does  */}
            <section className="relative min-h-screen flex items-center px-10 py-24 pt-32">
                <div className="absolute top-0 left-0 right-0 h-32 bg-gradient-to-b from-stone-soft/15 to-transparent pointer-events-none" />

                <div className="max-w-7xl mx-auto grid md:grid-cols-2 gap-16 items-center w-full">
                    <div className="relative aspect-[4/5] rounded-2xl overflow-hidden shadow-xl bg-stone-soft/10">
                        <Image
                            src="/images/about/mission.jpg"
                            alt="Airport terminal"
                            fill
                            className="object-cover"
                        />
                    </div>

                    <div>
                        <div className="text-xs tracking-[0.3em] uppercase text-amber-dark mb-4">
                            What we do
                        </div>
                        <h2 className="font-serif text-4xl md:text-5xl text-stone leading-tight mb-8">
                            Take the guesswork out of getting through security.
                        </h2>
                        <div className="space-y-5 text-stone-soft leading-relaxed">
                            <p>
                                WaitWise predicts TSA security wait times at major US airports
                                so travelers can plan their day around the wait — not the other
                                way around. Pick an airport, a date, and a time, and our model
                                tells you what to expect at the checkpoint.
                            </p>
                            <p>
                                We built WaitWise for the people who take air travel
                                seriously: frequent flyers, business travelers, parents
                                navigating airports with kids, and anyone who would rather
                                arrive at the gate calm than running. Whether you{"\u2019"}re catching
                                an early business flight or making a tight connection on a
                                holiday weekend, you shouldn{"\u2019"}t have to guess.
                            </p>
                            <p>
                                Better information means better decisions — about when to
                                leave home, whether to spring for PreCheck, or which flight to
                                book in the first place.
                            </p>
                        </div>
                    </div>
                </div>

                <div className="absolute bottom-0 left-0 right-0 h-40 bg-gradient-to-b from-transparent to-stone-soft/20 pointer-events-none" />
            </section>

            {/* SECTION 2: The data — text left, image right */}
            <section className="relative min-h-screen flex items-center px-10 py-24">
                <div className="absolute top-0 left-0 right-0 h-40 bg-gradient-to-b from-stone-soft/20 to-transparent pointer-events-none" />

                <div className="max-w-7xl mx-auto grid md:grid-cols-2 gap-16 items-center w-full">
                    {/* Text */}
                    <div>
                        <div className="text-xs tracking-[0.3em] uppercase text-amber-dark mb-4">
                            The Data
                        </div>
                        <h2 className="font-serif text-4xl md:text-5xl text-stone leading-tight mb-8">
                            Built on real-world signals.
                        </h2>
                        <div className="space-y-5 text-stone-soft leading-relaxed">
                            <p>
                                A model is only as good as what it learns from. WaitWise pulls
                                from multiple sources to build a complete picture of what
                                drives wait times.
                            </p>
                            <ul className="space-y-3">
                                <li className="flex gap-3">
                                    <span className="text-amber-dark font-serif">·</span>
                                    <span>
                                        <span className="text-stone font-medium">
                                            Historical wait times
                                        </span>{" "}
                                        from public TSA endpoints, scraped continuously to build a
                                        growing reference of how each airport actually behaves.
                                    </span>
                                </li>
                                <li className="flex gap-3">
                                    <span className="text-amber-dark font-serif">·</span>
                                    <span>
                                        <span className="text-stone font-medium">
                                            Throughput data
                                        </span>{" "}
                                        from TSA{"\u2019"}s public reports — the actual passenger counts
                                        moving through each checkpoint hour by hour.
                                    </span>
                                </li>
                                <li className="flex gap-3">
                                    <span className="text-amber-dark font-serif">·</span>
                                    <span>
                                        <span className="text-stone font-medium">
                                            Flight schedules
                                        </span>{" "}
                                        from the Bureau of Transportation Statistics, including
                                        departure volume, cancellations, and the share of
                                        international flights.
                                    </span>
                                </li>
                                <li className="flex gap-3">
                                    <span className="text-amber-dark font-serif">·</span>
                                    <span>
                                        <span className="text-stone font-medium">
                                            Operational signals
                                        </span>{" "}
                                        like weather disruptions, federal holidays, and government
                                        shutdown periods that affect TSA staffing.
                                    </span>
                                </li>
                            </ul>
                            <p className="pt-2">
                                Predictions are based on patterns. Actual wait times can vary
                                with day-of disruptions outside any model{"\u2019"}s view, so we
                                always recommend a buffer.
                            </p>
                        </div>
                    </div>

                    {/* Image */}
                    <div className="relative aspect-[4/5] rounded-2xl overflow-hidden shadow-xl bg-stone-soft/10">
                        <Image
                            src="/images/about/data.jpg"
                            alt="Data"
                            fill
                            className="object-cover"
                        />
                    </div>
                </div>

                <div className="absolute bottom-0 left-0 right-0 h-40 bg-gradient-to-b from-transparent to-stone-soft/25 pointer-events-none" />
            </section>
        </main>
    );
}