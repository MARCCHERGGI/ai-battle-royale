import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./providers/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg:       "#0d1117",
        card:     "#161b22",
        border:   "#30363d",
        muted:    "#8b949e",
        text:     "#e6edf3",
        orange:   "#f0883e",
        green:    "#3fb950",
        red:      "#da3633",
        blue:     "#58a6ff",
        purple:   "#bc8cff",
        yellow:   "#e3b341",
      },
      fontFamily: {
        mono: ["'Courier New'", "Courier", "monospace"],
      },
      animation: {
        pulse_slow: "pulse 3s ease-in-out infinite",
        blink: "blink 1s step-end infinite",
        scanline: "scanline 8s linear infinite",
      },
      keyframes: {
        blink: { "0%,100%": { opacity: "1" }, "50%": { opacity: "0" } },
        scanline: {
          "0%":   { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100vh)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
