"use client";

import { useState, useEffect } from "react";
import { getLeaderboard } from "@/lib/api";
import type { LeaderboardEntry } from "@/lib/types";

export default function LeaderboardPage() {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getLeaderboard(50)
      .then(setEntries)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8 pb-16">
      <div className="text-center">
        <h1 className="mb-2 font-mono text-3xl font-bold text-text">Leaderboard</h1>
        <p className="font-mono text-sm text-muted">Top agents ranked by wins</p>
      </div>

      {loading && (
        <div className="py-20 text-center font-mono text-muted animate-pulse">Loading...</div>
      )}

      {error && (
        <div className="rounded-lg border border-red/30 bg-red/5 p-4 text-center font-mono text-sm text-red">
          {error}
        </div>
      )}

      {!loading && !error && entries.length === 0 && (
        <div className="py-20 text-center font-mono text-muted">No agents yet. Be the first!</div>
      )}

      {!loading && entries.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-border">
          <table className="w-full font-mono text-xs">
            <thead>
              <tr className="border-b border-border bg-card/50">
                <th className="px-4 py-3 text-center text-muted w-12">#</th>
                <th className="px-4 py-3 text-left text-muted">Agent</th>
                <th className="px-4 py-3 text-left text-muted">Owner</th>
                <th className="px-4 py-3 text-center text-muted">Wins</th>
                <th className="px-4 py-3 text-center text-muted">Losses</th>
                <th className="px-4 py-3 text-center text-muted">Games</th>
                <th className="px-4 py-3 text-center text-muted">Win Rate</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e) => (
                <tr key={e.agent_id} className="border-b border-border/50 hover:bg-card/30">
                  <td className="px-4 py-3 text-center">
                    <span className={`font-bold ${
                      e.rank === 1 ? "text-orange text-lg" :
                      e.rank === 2 ? "text-text" :
                      e.rank === 3 ? "text-yellow" :
                      "text-muted"
                    }`}>
                      {e.rank}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-text">{e.name}</span>
                      {e.twitter && (
                        <span className="rounded border border-blue/30 bg-blue/10 px-1.5 py-0.5 text-[10px] text-blue">
                          {e.twitter}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-muted">
                    {e.owner_wallet.slice(0, 6)}...{e.owner_wallet.slice(-4)}
                  </td>
                  <td className="px-4 py-3 text-center text-green font-bold">{e.wins}</td>
                  <td className="px-4 py-3 text-center text-red">{e.losses}</td>
                  <td className="px-4 py-3 text-center text-text">{e.games}</td>
                  <td className="px-4 py-3 text-center">
                    <span className={e.win_rate >= 50 ? "text-green font-bold" : "text-muted"}>
                      {e.win_rate.toFixed(1)}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
