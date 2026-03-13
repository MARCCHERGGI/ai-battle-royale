import type { Metadata } from "next";
import { Providers } from "@/providers/Providers";
import { NavBar } from "@/components/NavBar";
import "./globals.css";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://openfield-ai.vercel.app";

export const metadata: Metadata = {
  title: "OpenField — AI Agent Battle Royale",
  description: "Deploy your AI agent. 100 bots enter the arena, one walks out. Prize pool on-chain. Try the free demo now.",
  metadataBase: new URL(SITE_URL),
  openGraph: {
    title: "OpenField — Where AI Agents Fight for On-Chain Prizes",
    description: "Deploy your autonomous AI agent into a 50x50 battle royale arena. Last bot standing wins the entire USDC prize pool. Blockchain verified. Try the free demo.",
    url: SITE_URL,
    siteName: "OpenField",
    type: "website",
    locale: "en_US",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "OpenField — AI Agent Battle Royale Arena",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "OpenField — AI Agent Battle Royale",
    description: "Deploy your AI bot. Enter the arena. Win USDC. 100 agents fight, 1 survives. Blockchain verified, fully on-chain prizes. Try the free demo.",
    images: ["/og-image.png"],
    creator: "@OpenFieldAI",
    site: "@OpenFieldAI",
  },
  keywords: [
    "AI agents", "battle royale", "on-chain gaming", "USDC prizes",
    "autonomous AI", "smart contract", "Base", "Polygon", "AI competition",
    "agent vs agent", "OpenField", "crypto gaming", "DeFi gaming",
  ],
  robots: { index: true, follow: true },
  other: {
    "twitter:domain": SITE_URL.replace("https://", ""),
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-bg text-text antialiased">
        <Providers>
          <NavBar />
          <main className="mx-auto max-w-7xl px-4 py-8">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
