import Image from "next/image";

export default function HowItWorksPage() {
    return (
        <main className="min-h-screen relative">
            {/* Background gradient */}
            <div
                className="fixed inset-0 -z-10"
                style={{
                    background:
                        "radial-gradient(ellipse at top, #F5EFE3 0%, #FAF8F4 30%, #F5EFE3 70%, #E8DFCD 100%)",
                }}
            />

            {/* ============================================================ */}
            {/* PAGE 1: Overview                                              */}
            {/* ============================================================ */}
            <section className="relative min-h-screen flex items-center px-10 py-24 pt-32">
                <div className="absolute top-0 left-0 right-0 h-32 bg-gradient-to-b from-stone-soft/15 to-transparent pointer-events-none" />

                <div className="max-w-4xl mx-auto text-center w-full">
                    <div className="text-xs tracking-[0.3em] uppercase text-amber-dark mb-4">
                        How It Works
                    </div>
                    <h1 className="font-serif text-4xl md:text-6xl text-stone leading-tight mb-8">
                        Two models, blended for the best of both.
                    </h1>
                    <div className="mx-auto mb-8 h-px w-24 bg-amber" />
                    <div className="space-y-5 text-stone-soft leading-relaxed text-lg max-w-3xl mx-auto">
                        <p>
                            No single model handles every situation well. Tree-based models
                            like LightGBM excel at finding patterns across many features,
                            but they struggle when feature data is uncertain or unavailable.
                            Time-series models like Prophet capture seasonal rhythms
                            beautifully, but miss the impact of one-off events.
                        </p>
                        <p>
                            WaitWise runs both, every time. Each model produces an
                            independent prediction, and the ensemble blends them using
                            weights derived from each model{"\u2019"}s historical accuracy.
                            Where the models agree, confidence is high. Where they
                            disagree, the prediction reflects the uncertainty.
                        </p>
                        <p>
                            The result is a forecast that{"\u2019"}s more robust than either
                            model could produce alone — sharper than a pure time-series
                            model when conditions are predictable, and steadier than a pure
                            feature-driven model when they aren{"\u2019"}t.
                        </p>
                    </div>
                </div>

                <div className="absolute bottom-0 left-0 right-0 h-40 bg-gradient-to-b from-transparent to-stone-soft/20 pointer-events-none" />
            </section>

            {/* PAGE 2: The two models                                        */}
            <section className="relative min-h-screen px-10 py-24">
                <div className="absolute top-0 left-0 right-0 h-40 bg-gradient-to-b from-stone-soft/20 to-transparent pointer-events-none" />

                <div className="max-w-7xl mx-auto relative">
                    {/* LightGBM — text left, image right */}
                    <div className="grid md:grid-cols-2 gap-16 items-center mb-24 pt-8">
                        <div>
                            <div className="text-xs tracking-[0.3em] uppercase text-stone-soft mb-3">
                                Model 01
                            </div>
                            <h2 className="font-serif text-3xl md:text-4xl text-stone mb-6">
                                LightGBM
                            </h2>
                            <div className="space-y-4 text-stone-soft leading-relaxed">
                                <p>
                                    LightGBM is a gradient-boosted tree model that learns
                                    complex interactions between many features at once. It
                                    looks at flight volume, day of week, hour of day, holiday
                                    proximity, historical wait patterns, and more — then
                                    learns rules like {"\u201C"}Friday afternoon + heavy
                                    international departures + holiday week = long wait.{"\u201D"}
                                </p>
                                <p>
                                    It excels at finding subtle relationships in tabular data
                                    that a simple time-series model would miss. For
                                    predictions in the near future, when we have reliable
                                    feature data, LightGBM is the more confident half of the
                                    ensemble.
                                </p>
                            </div>
                        </div>
                        <div className="relative aspect-[4/3] rounded-2xl overflow-hidden shadow-xl bg-stone-soft/10">
                            <Image
                                src="/images/how/lightgbm2.jpg"
                                alt="LightGBM"
                                fill
                                className="object-contain"
                            />
                        </div>
                    </div>

                    {/* Prophet — image left, text right */}
                    <div className="grid md:grid-cols-2 gap-16 items-center">
                        <div className="relative aspect-[4/3] rounded-2xl overflow-hidden shadow-xl bg-stone-soft/10 md:order-1">
                            <Image
                                src="/images/how/prophet.jpg"
                                alt="Prophet"
                                fill
                                className="object-cover"
                            />
                        </div>
                        <div className="md:order-2">
                            <div className="text-xs tracking-[0.3em] uppercase text-stone-soft mb-3">
                                Model 02
                            </div>
                            <h2 className="font-serif text-3xl md:text-4xl text-stone mb-6">
                                Prophet
                            </h2>
                            <div className="space-y-4 text-stone-soft leading-relaxed">
                                <p>
                                    Prophet is a time-series model from Meta{"\u2019"}s research
                                    team that decomposes a wait-time history into trend, weekly
                                    seasonality, yearly seasonality, and holiday effects. Where
                                    LightGBM looks across features, Prophet looks across time.
                                </p>
                                <p>
                                    Each airport gets its own Prophet model, since JFK{"\u2019"}s
                                    rhythm is nothing like Atlanta{"\u2019"}s or LAX{"\u2019"}s. Prophet
                                    shines when predicting weeks or months out, where
                                    exogenous features become unreliable but seasonal patterns
                                    remain steady.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="absolute bottom-0 left-0 right-0 h-40 bg-gradient-to-b from-transparent to-stone-soft/25 pointer-events-none" />
            </section>
        </main>
    );
}