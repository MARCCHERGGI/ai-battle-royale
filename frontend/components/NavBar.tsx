"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ConnectButton } from "@rainbow-me/rainbowkit";
import clsx from "clsx";

const links = [
  { href: "/rules",        label: "Rules" },
  { href: "/matches",      label: "Matches" },
  { href: "/leaderboard",  label: "Leaderboard" },
  { href: "/verify",       label: "Register" },
  { href: "/dashboard",    label: "Dashboard" },
];

export function NavBar() {
  const path = usePathname();
  return (
    <nav className="sticky top-0 z-50 border-b border-border bg-card/80 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <span className="text-orange font-mono text-lg font-bold tracking-widest">
            OPEN<span className="text-text">FIELD</span>
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
