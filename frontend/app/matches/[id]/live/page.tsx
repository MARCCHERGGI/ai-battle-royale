"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useMatchState } from "@/hooks/useMatchState";
import { getMatchResult } from "@/lib/api";
import { ArenaGrid } from "@/components/ArenaGrid";
import { EliminationFeed } from "@/components/EliminationFeed";
import { StatusBadge } from "@/components/StatusBadge";
import type { MatchResult } from "@/lib/types";

export default function LiveMatchPage() {
  const { id } = useParams<{ id: string }>();
  const { state, error, loading } = useMatchState(id, true);
  const [result, setResult] = useState<MatchResult | null>(null);
  const [allEvents, setAllEvents] = useState<string[]>([]);

  // Accumulate all events over time
  useEffect(() => {
    if (!state?.recent_events?.length) return;
    setAllEvents((prev) => {
      const newEvs = state.recent_events.filter((e) => !prev.includes(e));
      return newEvs.length ? [...newEvs, ...prev].slice(0, 100) : prev;
    });
  }, [state?.recent_events]);

  // Fetch result when match ends
  useEffect(() => {
    if (state?.status === "finished") {
      getMatchResult(id).then(setResult).catch(() => null);
    }
  }, [state?.status, id]);

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <p className="animate-pulse font-mono text-orange">Loading arena...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-20 text-center font-mono">
        <p className="text-red">{error}</p>
        <Link href="/matches" className="mt-4 block text-xs text-muted hover:text-text">
          &larr; Back to matches
        </Link>
      </div>
    );
  }

  if (!state) return null;

  const isFinished = state.status === "finished" || state.status === "cancelled";

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Link href={`/matches/${id}`} className="font-mono text-xs text-muted hover:text-text">
            &larr;
          </Link>
          <h1 className="font-mono text-lg font-bold text-text">
            ARENA #{id.slice(0, 8).toUpperCase()}
          </h1>
          <StatusBadge status={state.status} />
        </div>
        <div className="flex items-center gap-4 font-mono text-xs text-muted">
          <span>Tick <span className="text-orange font-bold">{state.tick}</span></span>
          <span>
            Alive{" "}
            <span className="text-green font-bold">{state.alive_count}</span>
            <span className="text-muted">/{state.total_agents}</span>
          </span>
        </div>
      </div>

      {/* Winner banner */}
      {isFinished && result && (
        <div className="rounded-lg border border-orange/50 bg-orange/10 p-4 text-center">
          <p className="font-mono text-xs uppercase tracking-widest text-orange">Match Over</p>
          <p className="mt-1 font-mono text-3xl font-bold text-text">{result.winner_name}</p>
          <p className="font-mono text-xs text-muted">wins in {result.total_ticks} ticks</p>
        </div>
      )}

      {/* Main layout */}
      <div className="grid gap-4 lg:grid-cols-4">
        {/* Arena — takes 3 cols */}
        <div className="lg:col-span-3">
          <ArenaGrid state={state} size={640} />

          {/* Zone info */}
          {state.zone && (
            <div className="mt-2 flex items-center gap-4 font-mono text-xs text-muted">
              <span className="text-orange">Safe zone:</span>
              <span>
                ({state.zone.x1},{state.zone.y1}) &rarr; ({state.zone.x2},{state.zone.y2})
              </span>
              <span>
                {state.zone.x2 - state.zone.x1 + 1} &times; {state.zone.y2 - state.zone.y1 + 1}
              </span>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="flex flex-col gap-4">
          {/* Agent list */}
          <div className="rounded-lg border border-border bg-card p-3">
            <h3 className="mb-2 font-mono text-xs uppercase tracking-widest text-muted">
              Agents ({state.alive_count}/{state.total_agents})
            </h3>
            <div className="max-h-64 space-y-1 overflow-y-auto">
              {[...state.agents]
                .sort((a, b) => (b.alive ? 1 : 0) - (a.alive ? 1 : 0) || b.hp - a.hp)
                .map((agent) => {
                  const hpPct = Math.max(0, Math.min(100, agent.hp));
                  const color = !agent.alive ? "#484f58" :
                    hpPct > 60 ? "#3fb950" : hpPct > 30 ? "#e3b341" : "#da3633";
                  return (
                    <div
                      key={agent.agent_id}
                      className="flex items-center gap-2"
                      style={{ opacity: agent.alive ? 1 : 0.35 }}
                    >
                      <div
                        className="size-1.5 shrink-0 rounded-full"
                        style={{ background: color }}
                      />
                      <span className="flex-1 truncate font-mono text-xs text-text">
                        {agent.name}
                      </span>
                      <div className="h-1 w-12 rounded bg-border">
                        <div
                          className="h-full rounded transition-all"
                          style={{ width: `${hpPct}%`, background: color }}
                        />
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>

          {/* Event log */}
          <div className="flex-1 rounded-lg border border-border bg-card p-3" style={{ minHeight: 200 }}>
            <EliminationFeed events={allEvents} tick={state.tick} />
          </div>
        </div>
      </div>

      {/* Result table */}
      {isFinished && result && (
        <div className="rounded-lg border border-border bg-card p-4">
          <h2 className="mb-3 font-mono text-xs uppercase tracking-widest text-muted">Final Rankings</h2>
          <div className="grid gap-1 md:grid-cols-2 lg:grid-cols-3">
            {result.rankings.slice(0, 9).map((r) => (
              <div
                key={r.agent_id}
                className={`flex items-center gap-3 rounded border px-3 py-2 font-mono text-xs ${
                  r.place === 1
                    ? "border-orange/40 bg-orange/5 text-orange"
                    : "border-border bg-bg text-muted"
                }`}
              >
                <span className="w-6 text-right font-bold">#{r.place}</span>
                <span className="flex-1 text-text">{r.agent_name}</span>
                <span>{r.eliminated_at_tick ? `t${r.eliminated_at_tick}` : "★"}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
