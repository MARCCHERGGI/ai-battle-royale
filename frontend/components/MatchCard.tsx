import Link from "next/link";
import type { MatchListItem } from "@/lib/types";
import { StatusBadge } from "./StatusBadge";

function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60_000);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

export function MatchCard({ match }: { match: MatchListItem }) {
  const fill = Math.round((match.agent_count / match.max_agents) * 100);
  return (
    <Link
      href={match.status === "active" ? `/matches/${match.match_id}/live` : `/matches/${match.match_id}`}
      className="group block rounded-lg border border-border bg-card p-4 transition-all hover:border-orange/40 hover:bg-orange/5"
    >
      <div className="mb-3 flex items-start justify-between gap-2">
        <div>
          <p className="font-mono text-xs text-muted">
            #{match.match_id.slice(0, 8).toUpperCase()}
          </p>
          <p className="mt-0.5 font-mono text-sm text-text">
            {match.agent_count} / {match.max_agents} agents
          </p>
        </div>
        <StatusBadge status={match.status} />
      </div>

      {/* Fill bar */}
      <div className="mb-3 h-1 rounded bg-border">
        <div
          className="h-full rounded transition-all"
          style={{
            width: `${fill}%`,
            background: fill === 100 ? "#da3633" : fill > 60 ? "#e3b341" : "#3fb950",
          }}
        />
      </div>

      <div className="flex items-center justify-between font-mono text-xs text-muted">
        <span>{timeAgo(match.created_at)}</span>
        {match.status === "active" && (
          <span className="text-orange group-hover:underline">Watch live &rarr;</span>
        )}
        {match.status === "finished" && (
          <span className="text-muted">View results &rarr;</span>
        )}
        {match.status === "open" && (
          <span className="text-blue group-hover:underline">Join &rarr;</span>
        )}
      </div>
    </Link>
  );
}
