"""
Core game engine — fully deterministic given a seed.

Usage:
    from engine.engine import BattleRoyaleEngine
    from engine.bots import AggressiveBot, CowardBot

    agents = [(AggressiveBot(), "Alice"), (CowardBot(), "Bob"), ...]
    engine = BattleRoyaleEngine(agents=agents, seed=42, map_size=50)
    result = engine.run()
"""
from __future__ import annotations

import random
import uuid
import logging
from dataclasses import dataclass, field
from typing import Callable, Optional

from engine.entities import AgentState, LootItem, Inventory
from engine.map import GameMap, Zone
from engine.actions import (
    Action, VALID_ACTIONS, VISION_RADIUS,
    resolve_move, resolve_attack, resolve_loot, resolve_heal,
)

logger = logging.getLogger(__name__)

# ── Config defaults ────────────────────────────────────────────────────────────
ZONE_SHRINK_INTERVAL = 20   # ticks
ZONE_DAMAGE_PER_TICK = 5
ZONE_SHRINK_AMOUNT = 2      # cells per shrink event
ENERGY_REGEN_PER_TICK = 3
LOOT_DENSITY = 0.04         # fraction of map tiles that start with loot
MAX_STRIKES = 3
MAX_TICKS = 2000            # hard cap to prevent infinite loops


@dataclass
class TickLog:
    tick: int
    alive_count: int
    zone: dict
    events: list[str] = field(default_factory=list)


@dataclass
class MatchResult:
    winner_id: Optional[str]
    winner_name: Optional[str]
    total_ticks: int
    rankings: list[dict]   # [{place, agent_id, name, eliminated_at_tick}]
    tick_logs: list[TickLog]


class BattleRoyaleEngine:
    """
    Runs a full battle royale match.

    `agents` is a list of (bot_instance, display_name) tuples.
    Any object with a `decide_action(obs: dict) -> str` method works.
    """

    def __init__(
        self,
        agents: list[tuple],
        seed: int | str = 0,
        map_size: int = 50,
        zone_shrink_interval: int = ZONE_SHRINK_INTERVAL,
        zone_damage: int = ZONE_DAMAGE_PER_TICK,
        max_ticks: int = MAX_TICKS,
        tick_callback: Optional[Callable[[TickLog], None]] = None,
    ):
        self.seed = seed
        self.rng = random.Random(seed)
        self.map = GameMap(size=map_size, rng=self.rng)
        self.zone_shrink_interval = zone_shrink_interval
        self.zone_damage = zone_damage
        self.max_ticks = max_ticks
        self.tick_callback = tick_callback  # optional live observer hook

        self._bot_instances: list = []
        self._agent_states: list[AgentState] = []
        self._loot: list[LootItem] = []
        self._tick = 0
        self._tick_logs: list[TickLog] = []
        self._elimination_order: list[AgentState] = []  # in order eliminated

        self._init_agents(agents)
        self._spawn_loot()

    # ── Setup ──────────────────────────────────────────────────────────────────

    def _init_agents(self, agents: list[tuple]) -> None:
        positions = self.map.spawn_positions(len(agents))
        for i, (bot, name) in enumerate(agents):
            agent_id = str(uuid.uuid4())[:8]
            x, y = positions[i]
            state = AgentState(agent_id=agent_id, name=name, x=x, y=y)
            self._bot_instances.append(bot)
            self._agent_states.append(state)

    def _spawn_loot(self) -> None:
        loot_types = ["medkit", "weapon_upgrade", "shield", "energy_boost"]
        total_cells = self.map.size ** 2
        loot_count = max(10, int(total_cells * LOOT_DENSITY))
        positions = set()
        attempts = 0
        while len(positions) < loot_count and attempts < loot_count * 5:
            x, y = self.map.random_position()
            positions.add((x, y))
            attempts += 1
        for i, (x, y) in enumerate(positions):
            loot_type = self.rng.choice(loot_types)
            self._loot.append(LootItem(loot_id=f"loot_{i}", loot_type=loot_type, x=x, y=y))

    # ── Main loop ──────────────────────────────────────────────────────────────

    def run(self) -> MatchResult:
        logger.info(f"Match started | seed={self.seed} | agents={len(self._agent_states)} | map={self.map.size}x{self.map.size}")

        while self._tick < self.max_ticks:
            alive = self._alive_agents()
            if len(alive) <= 1:
                break

            self._tick += 1
            self._run_tick(alive)

        return self._build_result()

    def _run_tick(self, alive: list[AgentState]) -> None:
        events: list[str] = []

        # 1. Shrink zone
        if self._tick % self.zone_shrink_interval == 0 and self._tick > 0:
            self.map.zone.shrink(ZONE_SHRINK_AMOUNT)
            events.append(f"Zone shrunk to {self.map.zone.to_dict()}")

        # 2. Reset per-tick state
        for agent in alive:
            agent.defending = False
            agent.energy = min(100, agent.energy + ENERGY_REGEN_PER_TICK)

        # 3. Collect actions from all agents
        actions: dict[str, str] = {}
        for agent, bot in zip(self._agent_states, self._bot_instances):
            if not agent.alive:
                continue
            obs = self._build_observation(agent)
            raw = self._call_bot(bot, obs, agent)
            actions[agent.agent_id] = raw

        # 4. Resolve actions phase 1: movement + defend + loot + heal
        for agent in alive:
            action = actions.get(agent.agent_id, Action.WAIT.value)
            act = Action(action) if action in VALID_ACTIONS else Action.WAIT

            if act in (Action.MOVE_UP, Action.MOVE_DOWN, Action.MOVE_LEFT, Action.MOVE_RIGHT):
                resolve_move(agent, act, self.map.size)
            elif act == Action.DEFEND:
                agent.defending = True
            elif act == Action.LOOT:
                resolve_loot(agent, self._loot)
            elif act == Action.HEAL:
                resolve_heal(agent)

        # 5. Resolve actions phase 2: attacks
        for agent in alive:
            if not agent.alive:
                continue
            action = actions.get(agent.agent_id, Action.WAIT.value)
            if action == Action.ATTACK.value:
                resolve_attack(agent, self._agent_states, self.rng)

        # 6. Apply zone damage
        zone = self.map.zone
        for agent in alive:
            if not agent.alive:
                continue
            if not zone.contains(agent.x, agent.y):
                agent.hp -= self.zone_damage
                if agent.hp <= 0:
                    agent.hp = 0
                    agent.alive = False
                    events.append(f"{agent.name} eliminated by zone")

        # 7. Mark newly dead
        for agent in alive:
            if not agent.alive and agent.eliminated_at_tick is None:
                agent.eliminated_at_tick = self._tick
                self._elimination_order.append(agent)

        alive_count = len(self._alive_agents())
        log = TickLog(
            tick=self._tick,
            alive_count=alive_count,
            zone=zone.to_dict(),
            events=events,
        )
        self._tick_logs.append(log)

        if self.tick_callback:
            self.tick_callback(log)

        logger.debug(f"Tick {self._tick:4d} | alive={alive_count:3d} | zone={zone.to_dict()}")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _alive_agents(self) -> list[AgentState]:
        return [a for a in self._agent_states if a.alive]

    def _call_bot(self, bot, obs: dict, agent: AgentState) -> str:
        """Call bot.decide_action; on any error count a strike and return WAIT."""
        try:
            action = bot.decide_action(obs)
            if action not in VALID_ACTIONS:
                raise ValueError(f"Invalid action: {action}")
            agent.strikes = 0  # reset on valid action
            return action
        except Exception as e:
            agent.strikes += 1
            if agent.strikes >= MAX_STRIKES:
                agent.alive = False
                logger.warning(f"{agent.name} eliminated after {MAX_STRIKES} strikes ({e})")
            else:
                logger.debug(f"{agent.name} strike {agent.strikes}: {e}")
            return Action.WAIT.value

    def _build_observation(self, agent: AgentState) -> dict:
        zone = self.map.zone
        nearby_agents = [
            {
                "id": a.agent_id,
                "x": a.x,
                "y": a.y,
                "hp": a.hp,
            }
            for a in self._agent_states
            if a.alive
            and a.agent_id != agent.agent_id
            and abs(a.x - agent.x) <= VISION_RADIUS
            and abs(a.y - agent.y) <= VISION_RADIUS
        ]
        nearby_loot = [
            {"id": l.loot_id, "type": l.loot_type, "x": l.x, "y": l.y}
            for l in self._loot
            if not l.picked_up
            and abs(l.x - agent.x) <= VISION_RADIUS
            and abs(l.y - agent.y) <= VISION_RADIUS
        ]
        return agent.to_observation(self._tick, zone.to_dict(), nearby_agents, nearby_loot)

    def _build_result(self) -> MatchResult:
        alive = self._alive_agents()
        total_agents = len(self._agent_states)

        # Assign final placements
        # Winner(s) get place 1; eliminated agents rank from last to first
        place = total_agents
        for elim in self._elimination_order:
            elim.place = place
            place -= 1

        for a in alive:
            a.place = 1

        rankings = sorted(
            [
                {
                    "place": a.place,
                    "agent_id": a.agent_id,
                    "name": a.name,
                    "eliminated_at_tick": a.eliminated_at_tick,
                    "hp_remaining": a.hp if a.alive else 0,
                }
                for a in self._agent_states
            ],
            key=lambda r: (r["place"] or 9999),
        )

        winner = alive[0] if alive else None
        return MatchResult(
            winner_id=winner.agent_id if winner else None,
            winner_name=winner.name if winner else None,
            total_ticks=self._tick,
            rankings=rankings,
            tick_logs=self._tick_logs,
        )
