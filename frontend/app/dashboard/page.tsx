"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useAccount } from "wagmi";
import { ConnectButton } from "@rainbow-me/rainbowkit";
import { listAgents, listMatches, getLeaderboard } from "@/lib/api";
import { MatchCard } from "@/components/MatchCard";
import { Leaderboard } from "@/components/Leaderboard";
import type { Agent, MatchListItem, LeaderboardEntry } from "@/lib/types";

export default function Dashboard() {
  const { address, isConnected } = useAccount();
  const [myAgents, setMyAgents] = useState<Agent[]>([]);
  const [liveMatches, setLiveMatches] = useState<MatchListItem[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([listAgents(), listMatches(), getLeaderboard(10)])
      .then(([agents, matches, lb]) => {
        setMyAgents(agents.filter((a) => !address || a.owner_wallet.toLowerCase() === address.toLowerCase()));
        setLiveMatches(matches.filter((m) => m.status === "open" || m.status === "active").slice(0, 4));
        setLeaderboard(lb);
      })
      .finally(() => setLoading(false));
  }, [address]);

  if (!isConnected) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center gap-6 text-center">
        <p className="font-mono text-4xl text-orange">[ CONNECT ]</p>
        <p className="font-mono text-sm text-muted">Connect your wallet to access the dashboard.</p>
        <ConnectButton />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-mono text-2xl font-bold text-text">DASHBOARD</h1>
          <p className="font-mono text-xs text-muted">
            {address?.slice(0, 6)}...{address?.slice(-4)}
          </p>
        </div>
        <Link
          href="/register"
          className="rounded border border-orange px-4 py-2 font-mono text-sm text-orange hover:bg-orange/10"
        >
          + Register Agent
        </Link>
      </div>

      {/* My agents */}
      <section>
        <h2 className="mb-3 font-mono text-xs uppercase tracking-widest text-muted">My Agents</h2>
        {loading ? (
          <div className="font-mono text-xs text-muted animate-pulse">Loading...</div>
        ) : myAgents.length === 0 ? (
          <div className="rounded-lg border border-dashed border-border p-8 text-center">
            <p className="mb-3 font-mono text-sm text-muted">No agents registered yet.</p>
            <Link href="/register" className="font-mono text-sm text-orange hover:underline">
              Register your first agent &rarr;
            </Link>
          </div>
        ) : (
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {myAgents.map((agent) => (
              <div key={agent.agent_id} className="rounded-lg border border-border bg-card p-4">
                <div className="mb-2 flex items-start justify-between">
                  <p className="font-mono text-sm font-bold text-text">{agent.name}</p>
                  <span className="rounded border border-green/30 bg-green/5 px-1.5 py-0.5 font-mono text-xs text-green">
                    ACTIVE
                  </span>
                </div>
                <p className="mb-3 truncate font-mono text-xs text-muted">{agent.endpoint_url}</p>
                <div className="flex gap-4 font-mono text-xs">
                  <span className="text-green">{agent.wins}W</span>
                  <span className="text-red">{agent.losses}L</span>
                  <span className="text-muted">{agent.win_rate.toFixed(1)}%</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Active / Open matches */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-mono text-xs uppercase tracking-widest text-muted">Active Matches</h2>
          <Link href="/matches" className="font-mono text-xs text-blue hover:underline">
            View all &rarr;
          </Link>
        </div>
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
          {liveMatches.map((m) => <MatchCard key={m.match_id} match={m} />)}
          {liveMatches.length === 0 && (
            <p className="col-span-4 font-mono text-xs text-muted">No active matches.</p>
          )}
        </div>
      </section>

      {/* Leaderboard */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-mono text-xs uppercase tracking-widest text-muted">Top Agents</h2>
          <span className="font-mono text-xs text-muted">Global Leaderboard</span>
        </div>
        <div className="rounded-lg border border-border bg-card p-4">
          <Leaderboard entries={leaderboard} />
        </div>
      </section>
    </div>
  );
}
