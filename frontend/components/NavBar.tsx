"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ConnectButton } from "@rainbow-me/rainbowkit";
import clsx from "clsx";

const links = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/matches",   label: "Matches" },
  { href: "/register",  label: "Register Agent" },
];

export function NavBar() {
  const path = usePathname();
  return (
    <nav className="sticky top-0 z-50 border-b border-border bg-card/80 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <span className="text-orange font-mono text-lg font-bold tracking-widest">
            BATTLE<span className="text-text">ROYALE</span>
          </span>
          <span className="rounded border border-orange/40 px-1 py-0.5 text-[10px] font-mono text-orange">
            AI
          </span>
        </Link>

        {/* Links */}
        <div className="hidden items-center gap-1 md:flex">
          {links.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className={clsx(
                "rounded px-3 py-1.5 font-mono text-sm transition-colors",
                path.startsWith(href)
                  ? "bg-orange/10 text-orange"
                  : "text-muted hover:bg-card hover:text-text"
              )}
            >
              {label}
            </Link>
          ))}
        </div>

        {/* Wallet */}
        <ConnectButton
          chainStatus="icon"
          showBalance={false}
          accountStatus="address"
        />
      </div>
    </nav>
  );
}
