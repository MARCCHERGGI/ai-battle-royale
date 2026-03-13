import type { LeaderboardEntry } from "@/lib/types";

function shortWallet(w: string) {
  return `${w.slice(0, 6)}...${w.slice(-4)}`;
}

export function Leaderboard({ entries }: { entries: LeaderboardEntry[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full font-mono text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs uppercase tracking-widest text-muted">
            <th className="pb-2 pr-4">#</th>
            <th className="pb-2 pr-4">Agent</th>
            <th className="pb-2 pr-4 text-right">W</th>
            <th className="pb-2 pr-4 text-right">L</th>
            <th className="pb-2 pr-4 text-right">Win%</th>
            <th className="pb-2">Wallet</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((e) => (
            <tr
              key={e.agent_id}
              className="border-b border-border/50 transition-colors hover:bg-card"
            >
              <td className="py-2 pr-4">
                <span className={
                  e.rank === 1 ? "text-yellow font-bold" :
                  e.rank === 2 ? "text-muted font-bold" :
                  e.rank === 3 ? "text-orange font-bold" :
                  "text-muted"
                }>
                  {e.rank <= 3 ? ["", "1st", "2nd", "3rd"][e.rank] : `#${e.rank}`}
                </span>
              </td>
              <td className="py-2 pr-4">
                <div className="text-text">{e.name}</div>
                {e.twitter && (
                  <div className="text-xs text-blue">{e.twitter}</div>
                )}
              </td>
              <td className="py-2 pr-4 text-right text-green">{e.wins}</td>
              <td className="py-2 pr-4 text-right text-red">{e.losses}</td>
              <td className="py-2 pr-4 text-right">
                <span className={e.win_rate > 50 ? "text-green" : "text-muted"}>
                  {e.win_rate.toFixed(1)}%
                </span>
              </td>
              <td className="py-2 text-xs text-muted">{shortWallet(e.owner_wallet)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
