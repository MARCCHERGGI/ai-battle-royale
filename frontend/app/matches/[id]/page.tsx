"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAccount } from "wagmi";
import Link from "next/link";
import { getMatch, listAgents, joinMatch, startMatch, getMatchResult } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import type { Match, Agent, MatchResult } from "@/lib/types";

export default function MatchDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { address } = useAccount();

  const [match, setMatch] = useState<Match | null>(null);
  const [myAgents, setMyAgents] = useState<Agent[]>([]);
  const [result, setResult] = useState<MatchResult | null>(null);
  const [selectedAgent, setSelectedAgent] = useState("");
  const [joining, setJoining] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    const [m, agents] = await Promise.all([getMatch(id), listAgents()]);
    setMatch(m);
    setMyAgents(agents.filter((a) => !address || a.owner_wallet.toLowerCase() === address.toLowerCase()));
    if (m.status === "finished") {
      const r = await getMatchResult(id).catch(() => null);
      setResult(r);
    }
    setLoading(false);
  }

  useEffect(() => { load(); }, [id, address]);

  async function handleJoin() {
    if (!selectedAgent) return;
    setJoining(true);
    setError(null);
    try {
      await joinMatch(id, selectedAgent);
      await load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Join failed");
    } finally {
      setJoining(false);
    }
  }

  async function handleStart() {
    setStarting(true);
    setError(null);
    try {
      await startMatch(id);
      router.push(`/matches/${id}/live`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Start failed");
      setStarting(false);
    }
  }

  if (loading) return <Skeleton />;
  if (!match) return <p className="font-mono text-muted">Match not found.</p>;

  const alreadyJoined = match.participants.some(
    (p) => myAgents.some((a) => a.agent_id === p.agent_id)
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Link href="/matches" className="mb-2 block font-mono text-xs text-muted hover:text-text">
            &larr; Matches
          </Link>
          <h1 className="font-mono text-xl font-bold text-text">
            MATCH #{match.match_id.slice(0, 8).toUpperCase()}
          </h1>
        </div>
        <StatusBadge status={match.status} />
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {[
          { label: "Agents",    value: `${match.agent_count} / ${match.max_agents}` },
          { label: "Map Size",  value: `${match.map_size}x${match.map_size}` },
          { label: "Seed",      value: `#${match.seed}` },
          { label: "Ticks",     value: match.total_ticks > 0 ? match.total_ticks : "—" },
        ].map(({ label, value }) => (
          <div key={label} className="rounded-lg border border-border bg-card p-3">
            <p className="font-mono text-xs text-muted">{label}</p>
            <p className="font-mono text-lg font-bold text-text">{value}</p>
          </div>
        ))}
      </div>

      {/* Live / result link */}
      {match.status === "active" && (
        <Link
          href={`/matches/${id}/live`}
          className="flex items-center justify-between rounded-lg border border-green/40 bg-green/5 p-4 transition hover:bg-green/10"
        >
          <div className="flex items-center gap-2">
            <span className="size-2 animate-pulse rounded-full bg-green" />
            <span className="font-mono text-sm font-bold text-green">Match in progress</span>
          </div>
          <span className="font-mono text-sm text-green">Watch live &rarr;</span>
        </Link>
      )}

      {/* Winner */}
      {match.status === "finished" && result && (
        <div className="rounded-lg border border-orange/40 bg-orange/5 p-4">
          <p className="mb-1 font-mono text-xs text-muted uppercase tracking-widest">Winner</p>
          <p className="font-mono text-2xl font-bold text-orange">{result.winner_name}</p>
          <p className="font-mono text-xs text-muted">{result.total_ticks} ticks</p>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Participant list */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="font-mono text-xs uppercase tracking-widest text-muted">
            Participants ({match.agent_count})
          </h2>
          {match.participants.length === 0 ? (
            <p className="font-mono text-xs text-muted italic">No agents joined yet.</p>
          ) : (
            <div className="space-y-1">
              {match.participants
                .sort((a, b) => (a.place ?? 999) - (b.place ?? 999))
                .map((p) => {
                  const isWinner = p.place === 1 && match.status === "finished";
                  return (
                    <div
                      key={p.agent_id}
                      className={`flex items-center justify-between rounded border px-3 py-2 font-mono text-sm ${
                        isWinner ? "border-orange/40 bg-orange/5 text-orange" : "border-border bg-card text-text"
                      }`}
                    >
                      <span>
                        {isWinner && <span className="mr-2 text-yellow">★</span>}
                        {p.agent_name}
                      </span>
                      <span className="text-xs text-muted">slot {p.slot}</span>
                    </div>
                  );
                })}
            </div>
          )}

          {/* Rankings */}
          {result && result.rankings.length > 0 && (
            <div className="mt-4">
              <h2 className="mb-3 font-mono text-xs uppercase tracking-widest text-muted">Final Rankings</h2>
              <div className="space-y-1">
                {result.rankings.map((r) => (
                  <div key={r.agent_id} className="flex items-center gap-3 rounded border border-border bg-card px-3 py-2 font-mono text-xs">
                    <span className={`w-8 text-right font-bold ${r.place === 1 ? "text-orange" : "text-muted"}`}>
                      #{r.place}
                    </span>
                    <span className="flex-1 text-text">{r.agent_name}</span>
                    <span className="text-muted">
                      {r.eliminated_at_tick ? `elim tick ${r.eliminated_at_tick}` : "survived"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Join / Start panel */}
        {match.status === "open" && (
          <div className="space-y-4">
            <h2 className="font-mono text-xs uppercase tracking-widest text-muted">Actions</h2>

            {!address ? (
              <p className="font-mono text-xs text-muted">Connect wallet to join.</p>
            ) : alreadyJoined ? (
              <div className="rounded border border-green/30 bg-green/5 p-3">
                <p className="font-mono text-xs text-green">&#10003; Your agent is in this match.</p>
              </div>
            ) : (
              <div className="space-y-3">
                <div>
                  <label className="mb-1.5 block font-mono text-xs uppercase tracking-widest text-muted">
                    Select Agent
                  </label>
                  <select
                    className="w-full rounded border border-border bg-bg px-3 py-2 font-mono text-sm text-text outline-none focus:border-orange"
                    value={selectedAgent}
                    onChange={(e) => setSelectedAgent(e.target.value)}
                  >
                    <option value="">Choose agent...</option>
                    {myAgents.map((a) => (
                      <option key={a.agent_id} value={a.agent_id}>{a.name}</option>
                    ))}
                  </select>
                </div>

                <div className="rounded border border-border bg-card p-3 font-mono text-xs text-muted">
                  <p>Entry fee: <span className="text-orange">10 USDC</span></p>
                  <p className="mt-1 text-muted/70">Approve USDC spend before joining.</p>
                </div>

                <button
                  onClick={handleJoin}
                  disabled={joining || !selectedAgent}
                  className="w-full rounded border border-blue bg-blue/10 py-2.5 font-mono text-sm font-bold text-blue transition hover:bg-blue hover:text-bg disabled:opacity-40"
                >
                  {joining ? "JOINING..." : "JOIN MATCH (10 USDC)"}
                </button>
              </div>
            )}

            {/* Start button (operator) */}
            {match.agent_count >= 2 && (
              <button
                onClick={handleStart}
                disabled={starting}
                className="w-full rounded border border-orange bg-orange/10 py-2.5 font-mono text-sm font-bold text-orange transition hover:bg-orange hover:text-bg disabled:opacity-40"
              >
                {starting ? "STARTING..." : "START MATCH"}
              </button>
            )}

            {error && (
              <p className="font-mono text-xs text-red">{error}</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function Skeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="h-8 w-48 rounded bg-card" />
      <div className="grid grid-cols-4 gap-3">
        {[...Array(4)].map((_, i) => <div key={i} className="h-16 rounded bg-card" />)}
      </div>
      <div className="h-48 rounded bg-card" />
    </div>
  );
}
