/**
 * Client-side Battle Royale simulation engine for the demo.
 * Runs entirely in the browser — no backend needed.
 */
import type { LiveAgent, MatchState } from "./types";

// ── Bot strategies ──────────────────────────────────────────────────────────

type Action = "MOVE_UP" | "MOVE_DOWN" | "MOVE_LEFT" | "MOVE_RIGHT" | "ATTACK" | "DEFEND" | "HEAL" | "WAIT";

const STRATEGIES: Record<string, (agent: DemoAgent, nearby: DemoAgent[], zone: Zone) => Action> = {
  Aggressive: (self, nearby, zone) => {
    const target = nearby.find(a => a.alive && a.id !== self.id);
    if (target && dist(self, target) <= 2) return "ATTACK";
    if (target) return moveToward(self, target);
    return moveTowardCenter(self, zone);
  },
  Survivalist: (self, nearby, zone) => {
    if (self.hp < 40) return "HEAL";
    if (!inZone(self, zone)) return moveTowardCenter(self, zone);
    const threat = nearby.find(a => a.alive && a.id !== self.id && dist(self, a) <= 3);
    if (threat) return "DEFEND";
    return moveTowardCenter(self, zone);
  },
  Hunter: (self, nearby, zone) => {
    const weakest = nearby
      .filter(a => a.alive && a.id !== self.id)
      .sort((a, b) => a.hp - b.hp)[0];
    if (weakest && dist(self, weakest) <= 2) return "ATTACK";
    if (weakest) return moveToward(self, weakest);
    return moveTowardCenter(self, zone);
  },
  Camper: (self, nearby, zone) => {
    if (self.hp < 60) return "HEAL";
    if (!inZone(self, zone)) return moveTowardCenter(self, zone);
    const close = nearby.find(a => a.alive && a.id !== self.id && dist(self, a) <= 1);
    if (close) return "ATTACK";
    return "DEFEND";
  },
  Random: (self, nearby, zone) => {
    if (!inZone(self, zone)) return moveTowardCenter(self, zone);
    const actions: Action[] = ["MOVE_UP", "MOVE_DOWN", "MOVE_LEFT", "MOVE_RIGHT", "ATTACK", "DEFEND", "HEAL", "WAIT"];
    return actions[Math.floor(Math.random() * actions.length)];
  },
};

// ── Types ────────────────────────────────────────────────────────────────────

interface DemoAgent {
  id: string;
  name: string;
  strategy: string;
  x: number;
  y: number;
  hp: number;
  maxHp: number;
  energy: number;
  attack: number;
  defense: number;
  alive: boolean;
  eliminatedAt: number | null;
}

interface Zone {
  x1: number; y1: number; x2: number; y2: number;
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function dist(a: { x: number; y: number }, b: { x: number; y: number }) {
  return Math.abs(a.x - b.x) + Math.abs(a.y - b.y);
}

function inZone(a: { x: number; y: number }, z: Zone) {
  return a.x >= z.x1 && a.x <= z.x2 && a.y >= z.y1 && a.y <= z.y2;
}

function moveToward(self: DemoAgent, target: { x: number; y: number }): Action {
  const dx = target.x - self.x;
  const dy = target.y - self.y;
  if (Math.abs(dx) >= Math.abs(dy)) return dx > 0 ? "MOVE_RIGHT" : "MOVE_LEFT";
  return dy > 0 ? "MOVE_DOWN" : "MOVE_UP";
}

function moveTowardCenter(self: DemoAgent, zone: Zone): Action {
  const cx = Math.floor((zone.x1 + zone.x2) / 2);
  const cy = Math.floor((zone.y1 + zone.y2) / 2);
  return moveToward(self, { x: cx, y: cy });
}

function clamp(v: number, min: number, max: number) {
  return Math.max(min, Math.min(max, v));
}

// ── Bot presets ──────────────────────────────────────────────────────────────

const BOT_PRESETS = [
  { name: "AggressorBot", strategy: "Aggressive" },
  { name: "SurvivalistAI", strategy: "Survivalist" },
  { name: "HunterX", strategy: "Hunter" },
  { name: "CamperKing", strategy: "Camper" },
  { name: "RandomChaos", strategy: "Random" },
  { name: "BlitzBot", strategy: "Aggressive" },
  { name: "TankMaster", strategy: "Survivalist" },
  { name: "ShadowHunter", strategy: "Hunter" },
  { name: "FortressAI", strategy: "Camper" },
  { name: "WildCard", strategy: "Random" },
];

// ── Engine ───────────────────────────────────────────────────────────────────

export interface DemoConfig {
  playerName: string;
  playerStrategy: string;
  botCount: number;
  mapSize: number;
}

export interface DemoTickResult {
  state: MatchState;
  events: string[];
  finished: boolean;
  winner: string | null;
  rankings: { place: number; name: string; eliminatedAt: number | null }[];
}

export class DemoEngine {
  private agents: DemoAgent[] = [];
  private zone: Zone;
  private tick = 0;
  private mapSize: number;
  private events: string[] = [];
  private eliminationOrder: string[] = [];
  private readonly ZONE_SHRINK_INTERVAL = 15;
  private readonly ZONE_DAMAGE = 8;
  private readonly MAX_TICKS = 200;

  constructor(config: DemoConfig) {
    this.mapSize = config.mapSize;
    this.zone = { x1: 0, y1: 0, x2: config.mapSize - 1, y2: config.mapSize - 1 };

    // Player agent
    this.agents.push({
      id: "player",
      name: config.playerName,
      strategy: config.playerStrategy,
      x: Math.floor(Math.random() * config.mapSize),
      y: Math.floor(Math.random() * config.mapSize),
      hp: 100,
      maxHp: 100,
      energy: 100,
      attack: 12,
      defense: 5,
      alive: true,
      eliminatedAt: null,
    });

    // Bot agents
    const bots = BOT_PRESETS.slice(0, config.botCount);
    bots.forEach((bot, i) => {
      this.agents.push({
        id: `bot-${i}`,
        name: bot.name,
        strategy: bot.strategy,
        x: Math.floor(Math.random() * config.mapSize),
        y: Math.floor(Math.random() * config.mapSize),
        hp: 100,
        maxHp: 100,
        energy: 100,
        attack: 8 + Math.floor(Math.random() * 8),
        defense: 3 + Math.floor(Math.random() * 6),
        alive: true,
        eliminatedAt: null,
      });
    });
  }

  /** Advance one tick. Returns the new state. */
  step(): DemoTickResult {
    this.tick++;
    this.events = [];

    // Zone shrink
    if (this.tick % this.ZONE_SHRINK_INTERVAL === 0) {
      const shrink = 2;
      this.zone = {
        x1: Math.min(this.zone.x1 + shrink, Math.floor(this.mapSize / 2) - 2),
        y1: Math.min(this.zone.y1 + shrink, Math.floor(this.mapSize / 2) - 2),
        x2: Math.max(this.zone.x2 - shrink, Math.floor(this.mapSize / 2) + 2),
        y2: Math.max(this.zone.y2 - shrink, Math.floor(this.mapSize / 2) + 2),
      };
      this.events.push(`Zone shrunk to (${this.zone.x1},${this.zone.y1})-(${this.zone.x2},${this.zone.y2})`);
    }

    // Zone damage
    for (const a of this.agents) {
      if (!a.alive) continue;
      if (!inZone(a, this.zone)) {
        a.hp -= this.ZONE_DAMAGE;
        if (a.hp <= 0) {
          a.hp = 0;
          a.alive = false;
          a.eliminatedAt = this.tick;
          this.eliminationOrder.push(a.id);
          this.events.push(`${a.name} eliminated by zone`);
        }
      }
    }

    // Agent actions
    const alive = this.agents.filter(a => a.alive);
    for (const agent of alive) {
      const nearby = alive.filter(a => dist(a, agent) <= 7);
      const strategyFn = STRATEGIES[agent.strategy] || STRATEGIES.Random;
      const action = strategyFn(agent, nearby, this.zone);

      switch (action) {
        case "MOVE_UP":    agent.y = clamp(agent.y - 1, 0, this.mapSize - 1); break;
        case "MOVE_DOWN":  agent.y = clamp(agent.y + 1, 0, this.mapSize - 1); break;
        case "MOVE_LEFT":  agent.x = clamp(agent.x - 1, 0, this.mapSize - 1); break;
        case "MOVE_RIGHT": agent.x = clamp(agent.x + 1, 0, this.mapSize - 1); break;
        case "ATTACK": {
          const targets = alive.filter(a => a.id !== agent.id && dist(a, agent) <= 2);
          if (targets.length > 0) {
            const target = targets[0];
            const dmg = Math.max(1, agent.attack - target.defense + Math.floor(Math.random() * 5));
            target.hp -= dmg;
            if (target.hp <= 0) {
              target.hp = 0;
              target.alive = false;
              target.eliminatedAt = this.tick;
              this.eliminationOrder.push(target.id);
              this.events.push(`${target.name} eliminated by ${agent.name}`);
            }
          }
          break;
        }
        case "DEFEND":
          // Temporary defense boost (simplified)
          break;
        case "HEAL":
          agent.hp = Math.min(agent.maxHp, agent.hp + 10);
          break;
        case "WAIT":
          break;
      }
    }

    // Check for winner
    const stillAlive = this.agents.filter(a => a.alive);
    const finished = stillAlive.length <= 1 || this.tick >= this.MAX_TICKS;

    let winner: string | null = null;
    if (finished && stillAlive.length === 1) {
      winner = stillAlive[0].name;
    } else if (finished && stillAlive.length > 1) {
      // Tiebreak: highest HP
      stillAlive.sort((a, b) => b.hp - a.hp);
      winner = stillAlive[0].name;
    }

    // Build rankings
    const rankings = this.agents
      .map(a => ({
        name: a.name,
        eliminatedAt: a.eliminatedAt,
        alive: a.alive,
        hp: a.hp,
      }))
      .sort((a, b) => {
        if (a.alive && !b.alive) return -1;
        if (!a.alive && b.alive) return 1;
        if (a.alive && b.alive) return b.hp - a.hp;
        return (b.eliminatedAt ?? 0) - (a.eliminatedAt ?? 0);
      })
      .map((a, i) => ({
        place: i + 1,
        name: a.name,
        eliminatedAt: a.eliminatedAt,
      }));

    // Build MatchState
    const state: MatchState = {
      match_id: "demo",
      status: finished ? "finished" : "active",
      tick: this.tick,
      alive_count: stillAlive.length,
      total_agents: this.agents.length,
      zone: { ...this.zone },
      agents: this.agents.map(a => ({
        agent_id: a.id,
        name: a.name,
        x: a.x,
        y: a.y,
        hp: a.hp,
        energy: a.energy,
        alive: a.alive,
        strikes: 0,
      })),
      recent_events: [...this.events],
    };

    return { state, events: this.events, finished, winner, rankings };
  }
}
