"use client";
import { useEffect, useState } from "react";
import { listMatches } from "@/lib/api";
import { MatchCard } from "@/components/MatchCard";
import type { MatchListItem, MatchStatus } from "@/lib/types";

const FILTERS: { label: string; value: MatchStatus | "all" }[] = [
  { label: "All",      value: "all" },
  { label: "Open",     value: "open" },
  { label: "Live",     value: "active" },
  { label: "Finished", value: "finished" },
];

export default function MatchesPage() {
  const [matches, setMatches] = useState<MatchListItem[]>([]);
  const [filter, setFilter] = useState<MatchStatus | "all">("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    listMatches(filter === "all" ? undefined : filter)
      .then(setMatches)
      .finally(() => setLoading(false));
  }, [filter]);

  const grouped = {
    active:   matches.filter((m) => m.status === "active"),
    open:     matches.filter((m) => m.status === "open"),
    finished: matches.filter((m) => m.status === "finished" || m.status === "cancelled"),
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="font-mono text-2xl font-bold text-text">MATCHES</h1>
          <p className="font-mono text-xs text-muted">{matches.length} matches total</p>
        </div>

        {/* Filter tabs */}
        <div className="flex gap-1 rounded border border-border bg-card p-1">
          {FILTERS.map(({ label, value }) => (
            <button
              key={value}
              onClick={() => setFilter(value)}
              className={`rounded px-3 py-1.5 font-mono text-xs transition-all ${
                filter === value
                  ? "bg-orange text-bg font-bold"
                  : "text-muted hover:text-text"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-28 animate-pulse rounded-lg border border-border bg-card" />
          ))}
        </div>
      ) : (
        <>
          {/* Live matches — prominent */}
          {(filter === "all" || filter === "active") && grouped.active.length > 0 && (
            <section>
              <h2 className="mb-3 flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-muted">
                <span className="size-1.5 animate-pulse rounded-full bg-green" />
                Live Now ({grouped.active.length})
              </h2>
              <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {grouped.active.map((m) => <MatchCard key={m.match_id} match={m} />)}
              </div>
            </section>
          )}

          {/* Open matches */}
          {(filter === "all" || filter === "open") && grouped.open.length > 0 && (
            <section>
              <h2 className="mb-3 font-mono text-xs uppercase tracking-widest text-muted">
                Open ({grouped.open.length})
              </h2>
              <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {grouped.open.map((m) => <MatchCard key={m.match_id} match={m} />)}
              </div>
            </section>
          )}

          {/* Finished matches */}
          {(filter === "all" || filter === "finished") && grouped.finished.length > 0 && (
            <section>
              <h2 className="mb-3 font-mono text-xs uppercase tracking-widest text-muted">
                Finished ({grouped.finished.length})
              </h2>
              <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {grouped.finished.map((m) => <MatchCard key={m.match_id} match={m} />)}
              </div>
            </section>
          )}

          {matches.length === 0 && (
            <div className="py-20 text-center font-mono text-muted">
              No matches found.
            </div>
          )}
        </>
      )}
    </div>
  );
}
