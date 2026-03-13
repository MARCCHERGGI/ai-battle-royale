"""
In-memory store — thread-safe via asyncio.Lock.
Suitable for single-process MVP. Replace with PostgreSQL for production.
"""
from __future__ import annotations
import asyncio
import uuid
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class AgentRecord:
    agent_id: str
    name: str
    endpoint_url: str
    owner_id: str
    description: Optional[str]
    wins: int = 0
    losses: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MatchRecord:
    match_id: str
    status: str             # open | starting | active | finished | cancelled
    max_agents: int
    map_size: int
    seed: int
    agent_ids: list[str]    # ordered join list
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    # Populated after match finishes
    winner_agent_id: Optional[str] = None
    result: Optional[dict] = None
    # Live state (updated each tick by the runner)
    live_state: Optional[dict] = None


class Store:
    def __init__(self):
        self._agents: dict[str, AgentRecord] = {}
        self._matches: dict[str, MatchRecord] = {}
        self._lock = asyncio.Lock()

    # ── Agents ─────────────────────────────────────────────────────────────────

    async def create_agent(self, name: str, endpoint_url: str, owner_id: str, description: Optional[str]) -> AgentRecord:
        async with self._lock:
            agent_id = str(uuid.uuid4())
            rec = AgentRecord(
                agent_id=agent_id,
                name=name,
                endpoint_url=endpoint_url,
                owner_id=owner_id,
                description=description,
            )
            self._agents[agent_id] = rec
            return rec

    async def get_agent(self, agent_id: str) -> Optional[AgentRecord]:
        return self._agents.get(agent_id)

    async def list_agents(self) -> list[AgentRecord]:
        return list(self._agents.values())

    async def increment_wins(self, agent_id: str) -> None:
        async with self._lock:
            if agent_id in self._agents:
                self._agents[agent_id].wins += 1

    async def increment_losses(self, agent_id: str) -> None:
        async with self._lock:
            if agent_id in self._agents:
                self._agents[agent_id].losses += 1

    # ── Matches ────────────────────────────────────────────────────────────────

    async def create_match(self, max_agents: int, map_size: int, seed: int) -> MatchRecord:
        async with self._lock:
            match_id = str(uuid.uuid4())
            rec = MatchRecord(
                match_id=match_id,
                status="open",
                max_agents=max_agents,
                map_size=map_size,
                seed=seed,
                agent_ids=[],
            )
            self._matches[match_id] = rec
            return rec

    async def get_match(self, match_id: str) -> Optional[MatchRecord]:
        return self._matches.get(match_id)

    async def list_matches(self) -> list[MatchRecord]:
        return list(self._matches.values())

    async def join_match(self, match_id: str, agent_id: str) -> MatchRecord:
        async with self._lock:
            match = self._matches[match_id]
            if agent_id in match.agent_ids:
                raise ValueError("Agent already joined this match")
            if len(match.agent_ids) >= match.max_agents:
                raise ValueError("Match is full")
            if match.status != "open":
                raise ValueError(f"Match is not open (status: {match.status})")
            match.agent_ids.append(agent_id)
            return match

    async def update_match_status(self, match_id: str, status: str, **kwargs) -> None:
        async with self._lock:
            match = self._matches[match_id]
            match.status = status
            for k, v in kwargs.items():
                setattr(match, k, v)

    async def update_live_state(self, match_id: str, state: dict) -> None:
        # No lock needed — single writer (match runner task)
        if match_id in self._matches:
            self._matches[match_id].live_state = state

    async def active_match_count(self) -> int:
        return sum(1 for m in self._matches.values() if m.status == "active")


# Global singleton
store = Store()
