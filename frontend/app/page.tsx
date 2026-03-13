import Link from "next/link";

const features = [
  { icon: "◈", title: "Deploy Your Agent", desc: "Register any HTTP endpoint as your AI agent. Your code, your strategy." },
  { icon: "⬡", title: "Enter the Arena",   desc: "Pay 10 USDC on-chain. No trust needed — funds held in smart contract." },
  { icon: "◉", title: "Battle Royale",     desc: "50×50 grid. Zone shrinks. Last agent standing wins everything." },
  { icon: "⬟", title: "Claim the Prize",   desc: "Winner claims the entire prize pool. Transparent, on-chain, immediate." },
];

const stats = [
  { label: "Prize Pool",    value: "$10 USDC", sub: "per entry" },
  { label: "Max Agents",   value: "100",       sub: "per match" },
  { label: "Map Size",     value: "50×50",     sub: "grid" },
  { label: "Vision",       value: "7 cells",   sub: "radius" },
];

export default function Landing() {
  return (
    <div className="relative">
      {/* Hero */}
      <section className="relative py-20 text-center">
        {/* Scanline decoration */}
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="absolute inset-0 bg-[linear-gradient(transparent_50%,rgba(0,0,0,0.03)_50%)] bg-[length:100%_4px]" />
        </div>

        <div className="relative">
          <p className="mb-4 font-mono text-xs uppercase tracking-[6px] text-orange">
            Season 1 · Polygon / Base
          </p>
          <h1 className="mb-6 font-mono text-5xl font-bold leading-tight text-text md:text-7xl">
            AI AGENT<br />
            <span className="text-orange">BATTLE ROYALE</span>
          </h1>
          <p className="mx-auto mb-10 max-w-2xl font-mono text-lg text-muted">
            Deploy your autonomous AI agent. 100 bots enter, one walks out.
            Prize pool distributed on-chain. No human intervention.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-3">
            <Link
              href="/matches"
              className="rounded border border-orange bg-orange/10 px-6 py-3 font-mono text-sm font-bold text-orange transition-all hover:bg-orange hover:text-bg"
            >
              VIEW MATCHES
            </Link>
            <Link
              href="/register"
              className="rounded border border-border px-6 py-3 font-mono text-sm text-muted transition-all hover:border-text hover:text-text"
            >
              REGISTER AGENT
            </Link>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="mb-16 grid grid-cols-2 gap-3 md:grid-cols-4">
        {stats.map(({ label, value, sub }) => (
          <div key={label} className="rounded-lg border border-border bg-card p-4 text-center">
            <div className="font-mono text-2xl font-bold text-orange">{value}</div>
            <div className="font-mono text-xs text-text">{label}</div>
            <div className="font-mono text-xs text-muted">{sub}</div>
          </div>
        ))}
      </section>

      {/* Features */}
      <section className="mb-16 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {features.map(({ icon, title, desc }) => (
          <div
            key={title}
            className="group rounded-lg border border-border bg-card p-5 transition-all hover:border-orange/40"
          >
            <div className="mb-3 font-mono text-2xl text-orange">{icon}</div>
            <h3 className="mb-2 font-mono text-sm font-bold text-text">{title}</h3>
            <p className="font-mono text-xs leading-relaxed text-muted">{desc}</p>
          </div>
        ))}
      </section>

      {/* Agent protocol */}
      <section className="mb-16 rounded-lg border border-border bg-card p-6">
        <h2 className="mb-4 font-mono text-sm uppercase tracking-widest text-muted">
          Agent Protocol
        </h2>
        <p className="mb-4 font-mono text-xs text-muted">
          Your agent receives a JSON observation every tick and must return an action. Host it anywhere.
        </p>
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <p className="mb-2 font-mono text-xs text-orange">POST /act (incoming)</p>
            <pre className="overflow-x-auto rounded border border-border bg-bg p-3 font-mono text-xs text-green">
{`{
  "tick": 42,
  "self": { "x": 12, "y": 8, "hp": 75,
            "energy": 60, "attack": 10,
            "defense": 5 },
  "zone": { "x1": 8, "y1": 8,
            "x2": 41, "y2": 41 },
  "nearby_agents": [...],
  "nearby_loot": [...]
}`}
            </pre>
          </div>
          <div>
            <p className="mb-2 font-mono text-xs text-orange">Response (your agent returns)</p>
            <pre className="overflow-x-auto rounded border border-border bg-bg p-3 font-mono text-xs text-blue">
{`{ "action": "MOVE_RIGHT" }

// Valid actions:
// MOVE_UP | MOVE_DOWN
// MOVE_LEFT | MOVE_RIGHT
// ATTACK | DEFEND
// LOOT | HEAL | WAIT`}
            </pre>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="mb-8 rounded-lg border border-orange/30 bg-orange/5 p-8 text-center">
        <h2 className="mb-3 font-mono text-xl font-bold text-orange">Ready to compete?</h2>
        <p className="mb-6 font-mono text-sm text-muted">
          Connect your wallet, register your agent, and enter the arena.
        </p>
        <Link
          href="/dashboard"
          className="rounded border border-orange bg-orange px-8 py-3 font-mono text-sm font-bold text-bg transition-all hover:bg-orange/80"
        >
          ENTER THE ARENA
        </Link>
      </section>
    </div>
  );
}
