import clsx from "clsx";
import type { MatchStatus } from "@/lib/types";

const cfg: Record<MatchStatus, { label: string; cls: string; dot?: boolean }> = {
  open:      { label: "OPEN",      cls: "border-blue/40 text-blue bg-blue/5" },
  starting:  { label: "STARTING",  cls: "border-yellow/40 text-yellow bg-yellow/5" },
  active:    { label: "LIVE",      cls: "border-green/40 text-green bg-green/5", dot: true },
  finished:  { label: "FINISHED",  cls: "border-border text-muted" },
  cancelled: { label: "CANCELLED", cls: "border-red/40 text-red bg-red/5" },
};

export function StatusBadge({ status }: { status: MatchStatus }) {
  const { label, cls, dot } = cfg[status] ?? cfg.open;
  return (
    <span className={clsx("inline-flex items-center gap-1.5 rounded border px-2 py-0.5 font-mono text-xs", cls)}>
      {dot && <span className="size-1.5 animate-pulse rounded-full bg-green" />}
      {label}
    </span>
  );
}
