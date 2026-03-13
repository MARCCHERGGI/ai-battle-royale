/**
 * API client — wired to backend at NEXT_PUBLIC_API_URL.
 * Falls back to mock data when NEXT_PUBLIC_USE_MOCK=true or fetch fails.
 */
import type {
  Agent, Match, MatchListItem, MatchState, MatchResult, LeaderboardEntry,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true";

// ── HTTP helper ───────────────────────────────────────────────────────────────

async function req<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export async function getNonce(wallet: string) {
  if (USE_MOCK) return { nonce: "mock-nonce", message: "Sign in to Battle Royale.\nNonce: mock-nonce" };
  return req<{ nonce: string; message: string }>("/auth/nonce", {
    method: "POST",
    body: JSON.stringify({ wallet_address: wallet }),
  });
}

export async function verifySignature(wallet: string, signature: string) {
  if (USE_MOCK) return { token: "mock-token", user_id: "mock-user" };
  return req<{ token: string; user_id: string }>("/auth/verify", {
    method: "POST",
    body: JSON.stringify({ wallet_address: wallet, signature }),
  });
}

// ── Agents ────────────────────────────────────────────────────────────────────

export async function registerAgent(data: {
  wallet_address: string;
  name: string;
  endpoint_url: string;
  description?: string;
}): Promise<Agent> {
  if (USE_MOCK) return MOCK.agents[0];
  return req<Agent>("/agents", { method: "POST", body: JSON.stringify(data) });
}

export async function listAgents(): Promise<Agent[]> {
  if (USE_MOCK) return MOCK.agents;
  return req<Agent[]>("/agents");
}

export async function getAgent(id: string): Promise<Agent> {
  if (USE_MOCK) return MOCK.agents.find((a) => a.agent_id === id) ?? MOCK.agents[0];
  return req<Agent>(`/agents/${id}`);
}

export async function pingAgent(id: string): Promise<{ reachable: boolean }> {
  if (USE_MOCK) return { reachable: true };
  return req<{ reachable: boolean }>(`/agents/${id}/ping`);
}

// ── Matches ───────────────────────────────────────────────────────────────────

export async function createMatch(data: {
  max_agents: number;
  map_size: number;
  seed?: number;
}): Promise<Match> {
  if (USE_MOCK) return MOCK.match;
  return req<Match>("/matches", { method: "POST", body: JSON.stringify(data) });
}

export async function listMatches(status?: string): Promise<MatchListItem[]> {
  if (USE_MOCK) return MOCK.matchList;
  const q = status ? `?status=${status}` : "";
  return req<MatchListItem[]>(`/matches${q}`);
}

export async function getMatch(id: string): Promise<Match> {
  if (USE_MOCK) return MOCK.match;
  return req<Match>(`/matches/${id}`);
}

export async function joinMatch(matchId: string, agentId: string, txHash?: string) {
  if (USE_MOCK) return { slot: 0 };
  return req(`/matches/${matchId}/join`, {
    method: "POST",
    body: JSON.stringify({ agent_id: agentId, tx_hash: txHash }),
  });
}

export async function startMatch(matchId: string) {
  if (USE_MOCK) return { status: "starting" };
  return req(`/matches/${matchId}/start`, { method: "POST" });
}

export async function getMatchState(matchId: string): Promise<MatchState> {
  if (USE_MOCK) return MOCK.matchState;
  return req<MatchState>(`/matches/${matchId}/state`);
}

export async function getMatchResult(matchId: string): Promise<MatchResult> {
  if (USE_MOCK) return MOCK.matchResult;
  return req<MatchResult>(`/matches/${matchId}/result`);
}

// ── Leaderboard ───────────────────────────────────────────────────────────────

export async function getLeaderboard(limit = 50): Promise<LeaderboardEntry[]> {
  if (USE_MOCK) return MOCK.leaderboard;
  return req<LeaderboardEntry[]>(`/leaderboard?limit=${limit}`);
}

// ── Mock data ──────────────────────────────────────────────────────────────────

const MOCK = {
  agents: Array.from({ length: 8 }, (_, i) => ({
    agent_id: `agent-${i}`,
    name: ["AggressorBot", "SurvivalistAI", "LooterPrime", "CowardMC", "ZoneHugger",
           "RandomWalk", "DefenderX", "ApexPredator"][i],
    endpoint_url: `http://localhost:900${i}`,
    owner_wallet: `0x${i.toString().padStart(40, "a")}`,
    description: "A battle-hardened AI agent.",
    wins: Math.floor(Math.random() * 20),
    losses: Math.floor(Math.random() * 30),
    games: 0,
    win_rate: 0,
    created_at: new Date().toISOString(),
  })).map((a) => ({ ...a, games: a.wins + a.losses, win_rate: a.wins / (a.wins + a.losses + 1) * 100 })),

  matchList: Array.from({ length: 6 }, (_, i) => ({
    match_id: `match-${i}`,
    status: (["open", "active", "finished", "open", "active", "finished"] as const)[i],
    max_agents: 20,
    agent_count: [3, 12, 20, 7, 18, 20][i],
    created_at: new Date(Date.now() - i * 3600_000).toISOString(),
    started_at: i > 0 ? new Date().toISOString() : null,
    finished_at: i === 2 || i === 5 ? new Date().toISOString() : null,
  })),

  match: {
    match_id: "match-0",
    status: "open" as const,
    max_agents: 20,
    map_size: 50,
    seed: 42,
    agent_count: 3,
    participants: [],
    winner_agent_id: null,
    total_ticks: 0,
    created_at: new Date().toISOString(),
    started_at: null,
    finished_at: null,
  },

  matchState: {
    match_id: "match-0",
    status: "active" as const,
    tick: 47,
    alive_count: 14,
    total_agents: 20,
    zone: { x1: 4, y1: 4, x2: 45, y2: 45 },
    agents: Array.from({ length: 20 }, (_, i) => ({
      agent_id: `agent-${i}`,
      name: `Bot_${String(i).padStart(3, "0")}`,
      x: Math.floor(Math.random() * 50),
      y: Math.floor(Math.random() * 50),
      hp: i < 14 ? Math.floor(40 + Math.random() * 60) : 0,
      energy: Math.floor(Math.random() * 100),
      alive: i < 14,
      strikes: 0,
    })),
    recent_events: [
      "Bot_011 eliminated by zone",
      "Zone shrunk to {x1:4,y1:4,x2:45,y2:45}",
      "Bot_006 eliminated by zone",
      "Bot_007 eliminated by combat",
    ],
  },

  matchResult: {
    match_id: "match-2",
    winner_id: "agent-3",
    winner_name: "CowardMC",
    total_ticks: 242,
    rankings: Array.from({ length: 20 }, (_, i) => ({
      place: i + 1,
      agent_id: `agent-${i}`,
      agent_name: `Bot_${String(i).padStart(3, "0")}`,
      eliminated_at_tick: i === 0 ? null : 242 - i * 10,
      hp_remaining: i === 0 ? 75 : 0,
    })),
  },

  leaderboard: Array.from({ length: 20 }, (_, i) => ({
    rank: i + 1,
    agent_id: `agent-${i}`,
    name: ["AggressorBot", "SurvivalistAI", "LooterPrime", "CowardMC", "ZoneHugger",
           "RandomWalk", "DefenderX", "ApexPredator"][i % 8],
    wins: 20 - i,
    losses: i + 2,
    games: 22 + i,
    win_rate: ((20 - i) / (22 + i)) * 100,
    owner_wallet: `0x${i.toString().padStart(40, "a")}`,
    twitter: i < 5 ? `@bot_player_${i}` : undefined,
  })),
};
