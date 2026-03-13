"""
Async match runner — integrates the game engine with networked agents.
Persists every tick, action, and elimination to PostgreSQL.
"""
from __future__ import annotations
import asyncio
import logging
import random
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from engine.map import GameMap
from engine.entities import AgentState, LootItem
from engine.actions import (
    Action, VALID_ACTIONS, VISION_RADIUS,
    resolve_move, resolve_attack, resolve_loot, resolve_heal,
)
from backend.services.agent_caller import call_agent_endpoint
from backend.store import store
from backend.db import AsyncSessionLocal
from backend import crud

if TYPE_CHECKING:
    from backend.models import Agent

logger = logging.getLogger(__name__)

ENERGY_REGEN_PER_TICK = 3
ZONE_SHRINK_INTERVAL  = 20
ZONE_SHRINK_AMOUNT    = 2
ZONE_DAMAGE_PER_TICK  = 5
LOOT_DENSITY          = 0.04
TICK_INTERVAL         = 1.0
MAX_TICKS             = 2000
MAX_STRIKES           = 3
# Persist to DB every N ticks (1 = every tick, higher = fewer writes)
DB_PERSIST_EVERY      = 1


class NetworkMatchRunner:
    def __init__(
        self,
        match_id: str,
        agent_records: list,    # list[Agent ORM objects]
        seed: int,
        map_size: int,
    ):
        self.match_id    = match_id
        self.match_uuid  = uuid.UUID(match_id)
        self.seed        = seed
        self.rng         = random.Random(seed)
        self.map         = GameMap(size=map_size, rng=self.rng)

        self._records:   dict[str, object]     = {}   # agent_id_str -> ORM Agent
        self._states:    dict[str, AgentState] = {}
        self._strikes:   dict[str, int]        = {}
        self._strike_eliminated: set[str]      = set()
        self._loot:      list[LootItem]        = []

        self._tick              = 0
        self._recent_events:    list[str]  = []
        self._elimination_order: list[str] = []   # agent_id strings

        self._init_agents(agent_records)
        self._spawn_loot()

    # ── Setup ──────────────────────────────────────────────────────────────────

    def _init_agents(self, records: list) -> None:
        positions = self.map.spawn_positions(len(records))
        for i, rec in enumerate(records):
            aid = str(rec.id)
            x, y = positions[i]
            self._records[aid] = rec
            self._states[aid]  = AgentState(agent_id=aid, name=rec.name, x=x, y=y)
            self._strikes[aid] = 0

    def _spawn_loot(self) -> None:
        loot_types = ["medkit", "weapon_upgrade", "shield", "energy_boost"]
        count = max(10, int(self.map.size ** 2 * LOOT_DENSITY))
        seen: set = set()
        attempts = 0
        while len(seen) < count and attempts < count * 5:
            seen.add(self.map.random_position())
            attempts += 1
        for i, (x, y) in enumerate(seen):
            self._loot.append(LootItem(f"L{i}", self.rng.choice(loot_types), x, y))

    # ── Main loop ──────────────────────────────────────────────────────────────

    async def run(self) -> None:
        logger.info("[%s] START agents=%d seed=%d", self.match_id[:8], len(self._states), self.seed)

        async with AsyncSessionLocal() as db:
            await crud.set_match_status(
                db, self.match_uuid, "active",
                started_at=datetime.utcnow(),
            )
            await db.commit()

        while self._tick < MAX_TICKS:
            # Emergency pause check — pause the game loop, don't cancel
            from backend.security import is_paused
            if is_paused():
                logger.warning("[%s] Game loop paused at tick %d", self.match_id[:8], self._tick)
                while is_paused():
                    await asyncio.sleep(2.0)
                logger.warning("[%s] Game loop resumed at tick %d", self.match_id[:8], self._tick)

            alive = self._alive()
            if len(alive) <= 1:
                break
            self._tick += 1
            actions = await self._tick_step(alive)
            # Persist snapshot + update live cache
            await self._persist_tick(actions)
            if store._matches.get(self.match_id):
                await store.update_live_state(self.match_id, self._snapshot())
            await asyncio.sleep(TICK_INTERVAL)

        await self._finalize()

    async def _tick_step(self, alive: list[AgentState]) -> dict[str, str]:
        events: list[str] = []

        # Zone shrink
        if self._tick % ZONE_SHRINK_INTERVAL == 0:
            self.map.zone.shrink(ZONE_SHRINK_AMOUNT)
            events.append(f"Zone shrunk to {self.map.zone.to_dict()}")

        # Energy regen + reset defend flag
        for a in alive:
            a.defending = False
            a.energy = min(100, a.energy + ENERGY_REGEN_PER_TICK)

        # Concurrent HTTP calls
        tasks = [
            call_agent_endpoint(
                agent_id=a.agent_id,
                agent_name=a.name,
                endpoint_url=self._records[a.agent_id].endpoint_url,
                observation=self._build_obs(a),
                strikes=self._strikes,
                eliminated=self._strike_eliminated,
            )
            for a in alive
        ]
        raw = await asyncio.gather(*tasks)
        actions: dict[str, str] = {a.agent_id: act for a, act in zip(alive, raw)}

        # Strike-eliminated agents
        for aid in list(self._strike_eliminated):
            s = self._states.get(aid)
            if s and s.alive:
                s.alive = False
                s.eliminated_at_tick = self._tick
                self._elimination_order.append(aid)
                events.append(f"{s.name} eliminated by strikes")
                await self._save_elimination(aid, "strikes")

        # Phase 1: movement / defend / loot / heal
        for a in alive:
            if not a.alive:
                continue
            act_str = actions.get(a.agent_id, Action.WAIT.value)
            act = Action(act_str) if act_str in VALID_ACTIONS else Action.WAIT
            if act in (Action.MOVE_UP, Action.MOVE_DOWN, Action.MOVE_LEFT, Action.MOVE_RIGHT):
                resolve_move(a, act, self.map.size)
            elif act == Action.DEFEND:
                a.defending = True
            elif act == Action.LOOT:
                resolve_loot(a, self._loot)
            elif act == Action.HEAL:
                resolve_heal(a)

        # Phase 2: attacks
        all_states = list(self._states.values())
        for a in alive:
            if not a.alive:
                continue
            if actions.get(a.agent_id) == Action.ATTACK.value:
                resolve_attack(a, all_states, self.rng)

        # Check for combat eliminations (hp <= 0 from attacks)
        for a in alive:
            if a.hp <= 0 and a.alive:
                a.hp = 0
                a.alive = False
                a.eliminated_at_tick = self._tick
                self._elimination_order.append(a.agent_id)
                events.append(f"{a.name} eliminated by combat")
                await self._save_elimination(a.agent_id, "combat")

        # Zone damage
        zone = self.map.zone
        for a in alive:
            if not a.alive:
                continue
            if not zone.contains(a.x, a.y):
                a.hp -= ZONE_DAMAGE_PER_TICK
                if a.hp <= 0:
                    a.hp = 0
                    a.alive = False
                    a.eliminated_at_tick = self._tick
                    self._elimination_order.append(a.agent_id)
                    events.append(f"{a.name} eliminated by zone")
                    await self._save_elimination(a.agent_id, "zone")

        self._recent_events = events[-10:]

        if self._tick % 10 == 0 or events:
            logger.info(
                f"[{self.match_id[:8]}] tick={self._tick:4d} alive={len(self._alive()):3d}"
                + (f" | {'; '.join(events)}" if events else "")
            )

        return actions

    # ── DB persistence ─────────────────────────────────────────────────────────

    async def _persist_tick(self, actions: dict[str, str]) -> None:
        if self._tick % DB_PERSIST_EVERY != 0:
            return
        agent_states = {
            aid: {
                "agent_id": s.agent_id,
                "name": s.name,
                "x": s.x, "y": s.y,
                "hp": s.hp, "energy": s.energy,
                "alive": s.alive,
                "strikes": self._strikes.get(aid, 0),
            }
            for aid, s in self._states.items()
        }
        async with AsyncSessionLocal() as db:
            await crud.save_tick(
                db,
                match_id=self.match_uuid,
                tick=self._tick,
                alive_count=len(self._alive()),
                zone=self.map.zone.to_dict(),
                agent_states=agent_states,
                actions=actions,
                events=list(self._recent_events),
            )
            await db.commit()

    async def _save_elimination(self, agent_id_str: str, cause: str) -> None:
        place = len(self._states) - len(self._elimination_order) + 1
        async with AsyncSessionLocal() as db:
            await crud.save_elimination(
                db,
                match_id=self.match_uuid,
                agent_id=uuid.UUID(agent_id_str),
                tick=self._tick,
                cause=cause,
                place=place,
            )
            await db.commit()

    async def _finalize(self) -> None:
        alive = self._alive()
        total = len(self._states)

        # Assign placements: last eliminated = worst place, survivors = 1st
        # Elimination order is chronological — first eliminated gets worst place
        place = total
        for aid in self._elimination_order:
            self._states[aid].place = place
            place -= 1
        for a in alive:
            a.place = 1

        winner = alive[0] if alive else None
        winner_uuid = uuid.UUID(winner.agent_id) if winner else None

        # Consistency check: if multiple agents alive at MAX_TICKS, pick by HP then name
        if len(alive) > 1:
            alive.sort(key=lambda a: (-a.hp, a.name))
            winner = alive[0]
            winner_uuid = uuid.UUID(winner.agent_id)
            for i, a in enumerate(alive):
                a.place = i + 1
            logger.warning(
                "[%s] Multiple survivors at tick cap — winner by HP tiebreak: %s (HP=%d)",
                self.match_id[:8], winner.name, winner.hp,
            )

        async with AsyncSessionLocal() as db:
            from sqlalchemy import update as sa_update
            from backend.models import MatchParticipant

            # Update each participant's final place
            for s in self._states.values():
                await db.execute(
                    sa_update(MatchParticipant)
                    .where(
                        MatchParticipant.match_id == self.match_uuid,
                        MatchParticipant.agent_id == uuid.UUID(s.agent_id),
                    )
                    .values(place=s.place)
                )

            # Update win/loss records
            if winner_uuid:
                await crud.increment_agent_wins(db, winner_uuid)
            for aid, s in self._states.items():
                if uuid.UUID(aid) != winner_uuid:
                    await crud.increment_agent_losses(db, uuid.UUID(aid))

            # Finalize match row
            await crud.set_match_status(
                db, self.match_uuid, "finished",
                winner_agent_id=winner_uuid,
                total_ticks=self._tick,
                finished_at=datetime.utcnow(),
            )
            await db.commit()

        logger.info(
            "[%s] FINISHED winner=%s ticks=%d",
            self.match_id[:8],
            winner.name if winner else "none",
            self._tick,
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _alive(self) -> list[AgentState]:
        return [s for s in self._states.values() if s.alive]

    def _build_obs(self, agent: AgentState) -> dict:
        zone = self.map.zone
        nearby_agents = [
            {"id": a.agent_id, "x": a.x, "y": a.y, "hp": a.hp}
            for a in self._states.values()
            if a.alive and a.agent_id != agent.agent_id
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

    def _snapshot(self) -> dict:
        return {
            "tick": self._tick,
            "alive_count": len(self._alive()),
            "zone": self.map.zone.to_dict(),
            "agents": [
                {
                    "agent_id": s.agent_id, "name": s.name,
                    "x": s.x, "y": s.y, "hp": s.hp,
                    "energy": s.energy, "alive": s.alive,
                    "strikes": self._strikes.get(aid, 0),
                }
                for aid, s in self._states.items()
            ],
            "recent_events": self._recent_events,
        }
