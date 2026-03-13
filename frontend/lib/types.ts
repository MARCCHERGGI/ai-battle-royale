// ── Shared TypeScript types ────────────────────────────────────────────────────

export type MatchStatus = "open" | "starting" | "active" | "finished" | "cancelled";

export interface Agent {
  agent_id: string;
  name: string;
  endpoint_url: string;
  owner_wallet: string;
  description?: string;
  wins: number;
  losses: number;
  games: number;
  win_rate: number;
  created_at: string;
}

export interface Participant {
  agent_id: string;
  agent_name: string;
  slot: number;
  place: number | null;
  joined_at: string;
}

export interface Match {
  match_id: string;
  status: MatchStatus;
  max_agents: number;
  map_size: number;
  seed: number;
  agent_count: number;
  participants: Participant[];
  winner_agent_id: string | null;
  total_ticks: number;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface MatchListItem {
  match_id: string;
  status: MatchStatus;
  max_agents: number;
  agent_count: number;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface LiveAgent {
  agent_id: string;
  name: string;
  x: number;
  y: number;
  hp: number;
  energy: number;
  alive: boolean;
  strikes: number;
}

export interface MatchState {
  match_id: string;
  status: MatchStatus;
  tick: number;
  alive_count: number;
  total_agents: number;
  zone: { x1: number; y1: number; x2: number; y2: number };
  agents: LiveAgent[];
  recent_events: string[];
}

export interface MatchResult {
  match_id: string;
  winner_id: string | null;
  winner_name: string | null;
  total_ticks: number;
  rankings: {
    place: number;
    agent_id: string;
    agent_name: string;
    eliminated_at_tick: number | null;
    hp_remaining: number;
  }[];
}

export interface LeaderboardEntry {
  rank: number;
  agent_id: string;
  name: string;
  wins: number;
  losses: number;
  games: number;
  win_rate: number;
  owner_wallet: string;
  twitter?: string;
}
