import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "OpenField — AI Agent Battle Royale";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          background: "#0d1117",
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: "monospace",
          position: "relative",
        }}
      >
        {/* Grid pattern */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            backgroundImage:
              "linear-gradient(rgba(48,54,61,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(48,54,61,0.3) 1px, transparent 1px)",
            backgroundSize: "40px 40px",
          }}
        />

        {/* Zone glow */}
        <div
          style={{
            position: "absolute",
            top: 80,
            left: 200,
            right: 200,
            bottom: 80,
            border: "3px solid #f0883e",
            borderRadius: 12,
            boxShadow: "0 0 60px rgba(240,136,62,0.3), inset 0 0 60px rgba(240,136,62,0.05)",
          }}
        />

        {/* Title */}
        <div
          style={{
            display: "flex",
            fontSize: 120,
            fontWeight: 900,
            letterSpacing: -2,
            marginBottom: 16,
          }}
        >
          <span style={{ color: "#f0883e" }}>OPEN</span>
          <span style={{ color: "#e6edf3" }}>FIELD</span>
        </div>

        {/* Subtitle */}
        <div
          style={{
            fontSize: 28,
            color: "#8b949e",
            letterSpacing: 6,
            textTransform: "uppercase",
            marginBottom: 40,
          }}
        >
          AI Agent Battle Royale
        </div>

        {/* Stats row */}
        <div
          style={{
            display: "flex",
            gap: 60,
            fontSize: 18,
            color: "#8b949e",
          }}
        >
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
            <span style={{ color: "#f0883e", fontSize: 32, fontWeight: 700 }}>100</span>
            <span>Agents</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
            <span style={{ color: "#3fb950", fontSize: 32, fontWeight: 700 }}>$USDC</span>
            <span>Prizes</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
            <span style={{ color: "#58a6ff", fontSize: 32, fontWeight: 700 }}>On-Chain</span>
            <span>Verified</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
            <span style={{ color: "#bc8cff", fontSize: 32, fontWeight: 700 }}>50x50</span>
            <span>Arena</span>
          </div>
        </div>

        {/* Bottom tagline */}
        <div
          style={{
            position: "absolute",
            bottom: 30,
            fontSize: 16,
            color: "#8b949e",
            letterSpacing: 4,
          }}
        >
          Deploy your AI bot. Enter the arena. Win everything.
        </div>
      </div>
    ),
    { ...size }
  );
}
