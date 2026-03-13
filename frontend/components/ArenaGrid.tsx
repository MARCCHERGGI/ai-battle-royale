"use client";
import { useEffect, useRef } from "react";
import type { MatchState } from "@/lib/types";

interface Props {
  state: MatchState;
  size?: number; // canvas px
}

export function ArenaGrid({ state, size = 600 }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const mapSize = 50; // game grid units
    const cell = size / mapSize;
    const { zone, agents } = state;

    // ── Background ──────────────────────────────────────────────────────────
    ctx.fillStyle = "#0d1117";
    ctx.fillRect(0, 0, size, size);

    // ── Grid lines ───────────────────────────────────────────────────────────
    ctx.strokeStyle = "#21262d";
    ctx.lineWidth = 0.5;
    for (let i = 0; i <= mapSize; i++) {
      ctx.beginPath(); ctx.moveTo(i * cell, 0);     ctx.lineTo(i * cell, size); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(0, i * cell);     ctx.lineTo(size, i * cell); ctx.stroke();
    }

    // ── Danger zone (outside safe area) ─────────────────────────────────────
    if (zone) {
      // Red tint outside zone
      ctx.fillStyle = "rgba(218, 54, 51, 0.12)";
      ctx.fillRect(0, 0, size, size);

      // Safe zone clear
      ctx.fillStyle = "#1c2128";
      ctx.fillRect(
        zone.x1 * cell, zone.y1 * cell,
        (zone.x2 - zone.x1 + 1) * cell,
        (zone.y2 - zone.y1 + 1) * cell,
      );

      // Safe zone border glow
      ctx.strokeStyle = "#f0883e";
      ctx.lineWidth = 2;
      ctx.shadowColor = "#f0883e";
      ctx.shadowBlur = 8;
      ctx.strokeRect(
        zone.x1 * cell, zone.y1 * cell,
        (zone.x2 - zone.x1 + 1) * cell,
        (zone.y2 - zone.y1 + 1) * cell,
      );
      ctx.shadowBlur = 0;
    }

    // ── Re-draw grid over safe zone so it looks clean ────────────────────────
    ctx.strokeStyle = "#21262d";
    ctx.lineWidth = 0.4;
    if (zone) {
      for (let i = zone.x1; i <= zone.x2 + 1; i++) {
        ctx.beginPath(); ctx.moveTo(i * cell, zone.y1 * cell); ctx.lineTo(i * cell, (zone.y2 + 1) * cell); ctx.stroke();
      }
      for (let j = zone.y1; j <= zone.y2 + 1; j++) {
        ctx.beginPath(); ctx.moveTo(zone.x1 * cell, j * cell); ctx.lineTo((zone.x2 + 1) * cell, j * cell); ctx.stroke();
      }
    }

    // ── Agents ────────────────────────────────────────────────────────────────
    const radius = Math.max(2.5, cell * 0.38);
    agents.forEach((agent) => {
      if (!agent.alive) return;

      const cx = (agent.x + 0.5) * cell;
      const cy = (agent.y + 0.5) * cell;
      const hpFrac = Math.max(0, Math.min(1, agent.hp / 100));

      // Agent body color: green → yellow → red
      let color: string;
      if (hpFrac > 0.6)      color = "#3fb950";
      else if (hpFrac > 0.3) color = "#e3b341";
      else                   color = "#da3633";

      // Glow
      ctx.shadowColor = color;
      ctx.shadowBlur = 6;

      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(cx, cy, radius, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;

      // HP bar
      const barW = cell * 0.9;
      const barH = 2;
      const barX = cx - barW / 2;
      const barY = cy + radius + 1.5;

      ctx.fillStyle = "#30363d";
      ctx.fillRect(barX, barY, barW, barH);
      ctx.fillStyle = color;
      ctx.fillRect(barX, barY, barW * hpFrac, barH);
    });

    // ── Dead agents (ghost) ───────────────────────────────────────────────────
    agents.forEach((agent) => {
      if (agent.alive) return;
      ctx.fillStyle = "rgba(139, 148, 158, 0.25)";
      ctx.beginPath();
      ctx.arc((agent.x + 0.5) * cell, (agent.y + 0.5) * cell, radius * 0.5, 0, Math.PI * 2);
      ctx.fill();
    });

  }, [state, size]);

  return (
    <canvas
      ref={canvasRef}
      width={size}
      height={size}
      className="w-full rounded-lg border border-border"
      style={{ imageRendering: "pixelated" }}
    />
  );
}
