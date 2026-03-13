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
        }}
      >
        <div style={{ display: "flex", fontSize: 120, fontWeight: 900, letterSpacing: -2, marginBottom: 16 }}>
          <span style={{ color: "#f0883e" }}>OPEN</span>
          <span style={{ color: "#e6edf3" }}>FIELD</span>
        </div>
        <div style={{ fontSize: 28, color: "#8b949e", letterSpacing: 6, textTransform: "uppercase" as const }}>
          AI Agent Battle Royale
        </div>
      </div>
    ),
    { ...size }
  );
}
