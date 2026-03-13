"use client";
import { useEffect, useRef } from "react";
import clsx from "clsx";

interface Props {
  events: string[];
  tick?: number;
}

function classifyEvent(e: string) {
  if (e.toLowerCase().includes("zone shrunk")) return "zone";
  if (e.toLowerCase().includes("eliminated by zone")) return "elim-zone";
  if (e.toLowerCase().includes("eliminated by combat")) return "elim-combat";
  if (e.toLowerCase().includes("eliminated by strikes")) return "elim-strike";
  return "info";
}

export function EliminationFeed({ events, tick }: Props) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (ref.current) ref.current.scrollTop = 0;
  }, [events]);

  return (
    <div className="flex h-full flex-col">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="font-mono text-xs uppercase tracking-widest text-muted">Event Log</h3>
        {tick !== undefined && (
          <span className="font-mono text-xs text-orange">tick {tick}</span>
        )}
      </div>
      <div ref={ref} className="flex-1 space-y-1 overflow-y-auto pr-1">
        {events.length === 0 ? (
          <p className="font-mono text-xs text-muted italic">Waiting for events...</p>
        ) : (
          [...events].reverse().map((e, i) => {
            const kind = classifyEvent(e);
            return (
              <div
                key={i}
                className={clsx(
                  "rounded px-2 py-1 font-mono text-xs",
                  kind === "zone"        && "bg-orange/10 text-orange",
                  kind === "elim-zone"   && "bg-red/10 text-red",
                  kind === "elim-combat" && "bg-red/10 text-red",
                  kind === "elim-strike" && "bg-yellow/10 text-yellow",
                  kind === "info"        && "bg-card text-muted",
                )}
              >
                {e}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
