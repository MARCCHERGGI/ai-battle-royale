"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { ArenaGrid } from "@/components/ArenaGrid";
import { EliminationFeed } from "@/components/EliminationFeed";
import { DemoEngine, type DemoConfig, type DemoTickResult } from "@/lib/demoEngine";
import Link from "next/link";

// ── Fake wallet generator ────────────────────────────────────────────────────

function randomWallet() {
  const hex = "0123456789abcdef";
  let addr = "0x";
  for (let i = 0; i < 40; i++) addr += hex[Math.floor(Math.random() * 16)];
  return addr;
}

function shortAddr(addr: string) {
  return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
}

// ── Strategy options ─────────────────────────────────────────────────────────

const STRATEGIES = [
  { id: "Aggressive", label: "Aggressive", desc: "Rush enemies, attack on sight" },
  { id: "Survivalist", label: "Survivalist", desc: "Stay in zone, heal when low" },
  { id: "Hunter", label: "Hunter", desc: "Target weakest enemy first" },
  { id: "Camper", label: "Camper", desc: "Defend position, attack only when close" },
  { id: "Random", label: "Random", desc: "Unpredictable chaos agent" },
];

// ── Steps ────────────────────────────────────────────────────────────────────

type Step = "connect" | "register" | "battle" | "result";

export default function DemoPage() {
  const [step, setStep] = useState<Step>("connect");
  const [wallet, setWallet] = useState("");
  const [agentName, setAgentName] = useState("");
  const [strategy, setStrategy] = useState("Aggressive");
  const [engine, setEngine] = useState<DemoEngine | null>(null);
  const [tickResult, setTickResult] = useState<DemoTickResult | null>(null);
  const [allEvents, setAllEvents] = useState<string[]>([]);
  const [speed, setSpeed] = useState(150); // ms per tick
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ── Step 1: Connect demo wallet ──────────────────────────────────────────
  const handleConnect = useCallback(() => {
    setWallet(randomWallet());
    setStep("register");
  }, []);

  // ── Step 2: Register agent ───────────────────────────────────────────────
  const handleRegister = useCallback(() => {
    if (!agentName.trim()) return;
    setStep("battle");

    const config: DemoConfig = {
      playerName: agentName.trim(),
      playerStrategy: strategy,
      botCount: 9, // 10 total
      mapSize: 50,
    };

    const eng = new DemoEngine(config);
    setEngine(eng);
    setAllEvents([]);
    setTickResult(null);
  }, [agentName, strategy]);

  // ── Step 3: Run the battle ───────────────────────────────────────────────
  useEffect(() => {
    if (step !== "battle" || !engine) return;

    intervalRef.current = setInterval(() => {
      const result = engine.step();
      setTickResult(result);
      if (result.events.length > 0) {
        setAllEvents(prev => [...result.events, ...prev].slice(0, 50));
      }
      if (result.finished) {
        if (intervalRef.current) clearInterval(intervalRef.current);
        setTimeout(() => setStep("result"), 1500);
      }
    }, speed);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [step, engine, speed]);

  // ── Restart ──────────────────────────────────────────────────────────────
  const handleRestart = useCallback(() => {
    setStep("connect");
    setWallet("");
    setAgentName("");
    setEngine(null);
    setTickResult(null);
    setAllEvents([]);
  }, []);

  // ── Replay with same agent ───────────────────────────────────────────────
  const handleReplay = useCallback(() => {
    setStep("battle");
    const config: DemoConfig = {
      playerName: agentName.trim(),
      playerStrategy: strategy,
      botCount: 9,
      mapSize: 50,
    };
    const eng = new DemoEngine(config);
    setEngine(eng);
    setAllEvents([]);
    setTickResult(null);
  }, [agentName, strategy]);

  return (
    <div className="relative">
      {/* Demo banner */}
      <div className="mb-6 rounded-lg border border-orange/30 bg-orange/5 px-4 py-3 text-center">
        <span className="font-mono text-xs text-orange">
          DEMO MODE — No real wallet or crypto needed. Everything runs in your browser.
        </span>
      </div>

      {/* ══════════════════════════════════════════════════════════════════════
          STEP 1: CONNECT DEMO WALLET
          ══════════════════════════════════════════════════════════════════════ */}
      {step === "connect" && (
        <div className="mx-auto max-w-lg text-center">
          <h1 className="mb-2 font-mono text-3xl font-bold text-text">
            TRY THE <span className="text-orange">ARENA</span>
          </h1>
          <p className="mb-8 font-mono text-sm text-muted">
            Experience AI Agent Battle Royale with a demo wallet. No MetaMask, no crypto, no setup.
          </p>

          <div className="mb-8 rounded-lg border border-border bg-card p-6">
            <div className="mb-4 text-4xl">
              <span className="inline-block rounded-full border-2 border-orange/40 bg-orange/10 p-4 font-mono text-2xl text-orange">
                1
              </span>
            </div>
            <h2 className="mb-2 font-mono text-lg font-bold text-text">Connect Demo Wallet</h2>
            <p className="mb-6 font-mono text-xs text-muted">
              We&apos;ll generate a fake wallet address for this demo session.
              In the real game, you&apos;d connect MetaMask or any Web3 wallet.
            </p>
            <button
              onClick={handleConnect}
              className="rounded border border-orange bg-orange/10 px-8 py-3 font-mono text-sm font-bold text-orange transition-all hover:bg-orange hover:text-bg"
            >
              CONNECT DEMO WALLET
            </button>
          </div>

          {/* Trust badges */}
          <div className="grid grid-cols-3 gap-3">
            <div className="rounded border border-border bg-card p-3 text-center">
              <div className="mb-1 font-mono text-lg text-green">&#x2713;</div>
              <div className="font-mono text-[10px] text-muted">Smart Contract<br />Verified</div>
            </div>
            <div className="rounded border border-border bg-card p-3 text-center">
              <div className="mb-1 font-mono text-lg text-green">&#x2713;</div>
              <div className="font-mono text-[10px] text-muted">Reentrancy<br />Protected</div>
            </div>
            <div className="rounded border border-border bg-card p-3 text-center">
              <div className="mb-1 font-mono text-lg text-green">&#x2713;</div>
              <div className="font-mono text-[10px] text-muted">OpenZeppelin<br />Standards</div>
            </div>
          </div>
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════════════════
          STEP 2: REGISTER AGENT
          ══════════════════════════════════════════════════════════════════════ */}
      {step === "register" && (
        <div className="mx-auto max-w-lg">
          <div className="mb-6 flex items-center gap-3">
            <div className="rounded border border-green/40 bg-green/10 px-3 py-1">
              <span className="font-mono text-xs text-green">Connected: {shortAddr(wallet)}</span>
            </div>
          </div>

          <div className="rounded-lg border border-border bg-card p-6">
            <div className="mb-4 text-center">
              <span className="inline-block rounded-full border-2 border-orange/40 bg-orange/10 p-4 font-mono text-2xl text-orange">
                2
              </span>
            </div>
            <h2 className="mb-4 text-center font-mono text-lg font-bold text-text">Register Your Agent</h2>

            {/* Agent name */}
            <label className="mb-1 block font-mono text-xs text-muted">Agent Name</label>
            <input
              value={agentName}
              onChange={(e) => setAgentName(e.target.value)}
              placeholder="e.g. DestroyerBot"
              maxLength={24}
              className="mb-4 w-full rounded border border-border bg-bg px-3 py-2 font-mono text-sm text-text placeholder:text-muted/50 focus:border-orange focus:outline-none"
            />

            {/* Strategy picker */}
            <label className="mb-2 block font-mono text-xs text-muted">Choose Strategy</label>
            <div className="mb-6 space-y-2">
              {STRATEGIES.map((s) => (
                <button
                  key={s.id}
                  onClick={() => setStrategy(s.id)}
                  className={`w-full rounded border px-3 py-2 text-left font-mono text-xs transition-all ${
                    strategy === s.id
                      ? "border-orange bg-orange/10 text-orange"
                      : "border-border bg-bg text-muted hover:border-text hover:text-text"
                  }`}
                >
                  <span className="font-bold">{s.label}</span>
                  <span className="ml-2 text-muted">&mdash; {s.desc}</span>
                </button>
              ))}
            </div>

            {/* Endpoint mock */}
            <div className="mb-6 rounded border border-border bg-bg p-3">
              <div className="font-mono text-[10px] text-muted">ENDPOINT (auto-generated for demo)</div>
              <div className="font-mono text-xs text-green">https://demo-agent.battleroyale.ai/{agentName.trim().toLowerCase().replace(/\s+/g, "-") || "your-agent"}/act</div>
            </div>

            <button
              onClick={handleRegister}
              disabled={!agentName.trim()}
              className="w-full rounded border border-orange bg-orange px-6 py-3 font-mono text-sm font-bold text-bg transition-all hover:bg-orange/80 disabled:opacity-30 disabled:cursor-not-allowed"
            >
              REGISTER &amp; ENTER MATCH
            </button>
          </div>
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════════════════
          STEP 3: LIVE BATTLE
          ══════════════════════════════════════════════════════════════════════ */}
      {(step === "battle" || step === "result") && tickResult && (
        <div>
          {/* Header */}
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded border border-green/40 bg-green/10 px-3 py-1">
                <span className="font-mono text-xs text-green">{shortAddr(wallet)}</span>
              </div>
              <div className={`rounded px-3 py-1 font-mono text-xs font-bold ${
                step === "result" ? "border border-orange bg-orange/10 text-orange" : "animate-pulse border border-red bg-red/10 text-red"
              }`}>
                {step === "result" ? "MATCH FINISHED" : "LIVE"}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <label className="font-mono text-[10px] text-muted">Speed:</label>
              <select
                value={speed}
                onChange={(e) => setSpeed(Number(e.target.value))}
                className="rounded border border-border bg-bg px-2 py-1 font-mono text-xs text-text"
              >
                <option value={300}>Slow</option>
                <option value={150}>Normal</option>
                <option value={60}>Fast</option>
                <option value={20}>Ultra</option>
              </select>
            </div>
          </div>

          {/* Stats bar */}
          <div className="mb-4 grid grid-cols-4 gap-3">
            <div className="rounded border border-border bg-card p-2 text-center">
              <div className="font-mono text-lg font-bold text-orange">{tickResult.state.tick}</div>
              <div className="font-mono text-[10px] text-muted">Tick</div>
            </div>
            <div className="rounded border border-border bg-card p-2 text-center">
              <div className="font-mono text-lg font-bold text-green">{tickResult.state.alive_count}</div>
              <div className="font-mono text-[10px] text-muted">Alive</div>
            </div>
            <div className="rounded border border-border bg-card p-2 text-center">
              <div className="font-mono text-lg font-bold text-red">{tickResult.state.total_agents - tickResult.state.alive_count}</div>
              <div className="font-mono text-[10px] text-muted">Eliminated</div>
            </div>
            <div className="rounded border border-border bg-card p-2 text-center">
              <div className="font-mono text-lg font-bold text-text">
                {tickResult.state.zone.x2 - tickResult.state.zone.x1 + 1}x{tickResult.state.zone.y2 - tickResult.state.zone.y1 + 1}
              </div>
              <div className="font-mono text-[10px] text-muted">Zone</div>
            </div>
          </div>

          {/* Arena + sidebar */}
          <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
            {/* Arena */}
            <div>
              <ArenaGrid state={tickResult.state} size={600} />
            </div>

            {/* Sidebar */}
            <div className="flex flex-col gap-4">
              {/* Agent list */}
              <div className="rounded-lg border border-border bg-card p-3">
                <h3 className="mb-2 font-mono text-xs uppercase tracking-widest text-muted">Agents</h3>
                <div className="max-h-[260px] space-y-1 overflow-y-auto">
                  {tickResult.state.agents
                    .sort((a, b) => (b.alive ? 1 : 0) - (a.alive ? 1 : 0) || b.hp - a.hp)
                    .map((a) => (
                    <div
                      key={a.agent_id}
                      className={`flex items-center justify-between rounded px-2 py-1 font-mono text-xs ${
                        a.agent_id === "player"
                          ? "border border-orange/30 bg-orange/5"
                          : ""
                      } ${!a.alive ? "opacity-40" : ""}`}
                    >
                      <span className={a.agent_id === "player" ? "text-orange font-bold" : "text-text"}>
                        {a.name}
                        {a.agent_id === "player" && " (YOU)"}
                      </span>
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 w-16 rounded-full bg-border">
                          <div
                            className={`h-full rounded-full ${
                              a.hp > 60 ? "bg-green" : a.hp > 30 ? "bg-yellow" : "bg-red"
                            }`}
                            style={{ width: `${Math.max(0, a.hp)}%` }}
                          />
                        </div>
                        <span className="w-8 text-right text-muted">{Math.max(0, a.hp)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Event feed */}
              <div className="h-[200px] rounded-lg border border-border bg-card p-3">
                <EliminationFeed events={allEvents} tick={tickResult.state.tick} />
              </div>
            </div>
          </div>

          {/* Result overlay */}
          {step === "result" && tickResult.winner && (
            <div className="mt-6 rounded-lg border border-orange/30 bg-card p-6 text-center">
              <h2 className="mb-2 font-mono text-2xl font-bold text-orange">
                {tickResult.winner === agentName.trim() ? "YOU WON!" : `${tickResult.winner} WINS!`}
              </h2>
              <p className="mb-4 font-mono text-sm text-muted">
                Match completed in {tickResult.state.tick} ticks
              </p>

              {/* Rankings */}
              <div className="mx-auto mb-6 max-w-sm">
                {tickResult.rankings.slice(0, 5).map((r) => (
                  <div
                    key={r.name}
                    className={`flex items-center justify-between border-b border-border px-3 py-2 font-mono text-xs ${
                      r.name === agentName.trim() ? "text-orange font-bold" : "text-text"
                    }`}
                  >
                    <span>#{r.place} {r.name}</span>
                    <span className="text-muted">
                      {r.eliminatedAt ? `tick ${r.eliminatedAt}` : "SURVIVED"}
                    </span>
                  </div>
                ))}
              </div>

              {/* Blockchain verification mock */}
              <div className="mx-auto mb-6 max-w-sm rounded border border-green/30 bg-green/5 p-3">
                <div className="mb-1 font-mono text-xs text-green">On-Chain Verification</div>
                <div className="font-mono text-[10px] text-muted">
                  In the real game, the winner&apos;s prize is settled on-chain via the BattleRoyale smart contract.
                  The winner calls <code className="text-blue">claimPrize()</code> to withdraw their winnings.
                </div>
              </div>

              <div className="flex items-center justify-center gap-3">
                <button
                  onClick={handleReplay}
                  className="rounded border border-orange bg-orange/10 px-6 py-3 font-mono text-sm font-bold text-orange transition-all hover:bg-orange hover:text-bg"
                >
                  PLAY AGAIN
                </button>
                <Link
                  href="/register"
                  className="rounded border border-border px-6 py-3 font-mono text-sm text-muted transition-all hover:border-text hover:text-text"
                >
                  REGISTER REAL AGENT
                </Link>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Loading state while engine initializes */}
      {step === "battle" && !tickResult && (
        <div className="py-20 text-center">
          <div className="mb-4 font-mono text-2xl text-orange animate-pulse">Initializing Arena...</div>
          <p className="font-mono text-sm text-muted">Spawning 10 agents on a 50x50 grid</p>
        </div>
      )}
    </div>
  );
}
