"use client";

import { useState } from "react";
import Link from "next/link";
import { Menu, X } from "lucide-react";

export default function Nav() {
    const [menuOpen, setMenuOpen] = useState(false);

    return (
        <>
            {/* Fixed top nav */}
            <nav className="fixed top-0 left-0 right-0 z-50 flex justify-between items-center px-10 py-6 text-cream backdrop-blur-sm bg-stone/30">
                <Link href="/" className="text-2xl tracking-wide font-serif">
                    Wait<span className="text-amber">Wise</span>
                </Link>
                <div className="flex items-center gap-8 text-sm tracking-wider uppercase">
                    <Link href="/" className="hover:text-amber transition-colors">
                        Home
                    </Link>
                    <Link href="/about" className="hover:text-amber transition-colors">
                        About
                    </Link>
                    <Link href="/how-it-works" className="hover:text-amber transition-colors">
                        How it works
                    </Link>
                    <button
                        onClick={() => setMenuOpen(true)}
                        className="hover:text-amber transition-colors"
                        aria-label="Open menu"
                    >
                        <Menu className="w-6 h-6" />
                    </button>
                </div>
            </nav>

            <SidePanel open={menuOpen} onClose={() => setMenuOpen(false)} />
        </>
    );
}

function SidePanel({
    open,
    onClose,
}: {
    open: boolean;
    onClose: () => void;
}) {
    const links = [
        { label: "Home", href: "/" },
        { label: "About", href: "/about" },
        { label: "How It Works", href: "/how-it-works" },
        { label: "Airports", href: "/airports" },
    ];

    return (
        <>
            {/* Backdrop */}
            <div
                className={`fixed inset-0 z-50 bg-stone/40 backdrop-blur-sm transition-opacity duration-300 ${open ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
                    }`}
                onClick={onClose}
                aria-hidden
            />

            {/* Panel */}
            <aside
                className={`fixed top-0 right-0 z-50 h-full w-80 bg-white shadow-2xl transition-transform duration-300 ease-out ${open ? "translate-x-0" : "translate-x-full"
                    }`}
            >
                <div className="flex items-center justify-between px-6 py-6 border-b border-line">
                    <span className="font-serif text-xl text-stone">Menu</span>
                    <button
                        onClick={onClose}
                        className="text-stone-soft hover:text-stone transition-colors"
                        aria-label="Close menu"
                    >
                        <X className="w-6 h-6" />
                    </button>
                </div>

                <nav className="flex flex-col py-4">
                    {links.map((link) => (
                        <Link
                            key={link.href}
                            href={link.href}
                            onClick={onClose}
                            className="px-6 py-4 text-stone hover:bg-cream hover:text-amber-dark transition-colors text-lg font-serif border-b border-line/50"
                        >
                            {link.label}
                        </Link>
                    ))}
                </nav>
            </aside>
        </>
    );
}