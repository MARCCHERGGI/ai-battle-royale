"""
Pydantic models for the Battle Royale agent protocol.
These mirror exactly what the platform sends and expects.
"""
from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel


# ── Actions ───────────────────────────────────────────────────────────────────

class Action(str, Enum):
    MOVE_UP    = "MOVE_UP"
    MOVE_DOWN  = "MOVE_DOWN"
    MOVE_LEFT  = "MOVE_LEFT"
    MOVE_RIGHT = "MOVE_RIGHT"
    ATTACK     = "ATTACK"
    DEFEND     = "DEFEND"
    LOOT       = "LOOT"
    HEAL       = "HEAL"
    WAIT       = "WAIT"


# ── Observation (sent TO your agent each tick) ────────────────────────────────

class Inventory(BaseModel):
    medkits:         int = 0
    weapon_upgrades: int = 0
    shields:         int = 0
    energy_boosts:   int = 0


class SelfState(BaseModel):
    id:       str
    x:        int
    y:        int
    hp:       int
    energy:   int
    attack:   int
    defense:  int
    inventory: Inventory = Inventory()


class NearbyAgent(BaseModel):
    id: str
    x:  int
    y:  int
    hp: int


class NearbyLoot(BaseModel):
    id:   str
    type: str   # medkit | weapon_upgrade | shield | energy_boost
    x:    int
    y:    int


class Zone(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int

    def contains(self, x: int, y: int) -> bool:
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def center(self) -> tuple[int, int]:
        return (self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2

    def width(self) -> int:
        return self.x2 - self.x1 + 1

    def height(self) -> int:
        return self.y2 - self.y1 + 1


class Observation(BaseModel):
    """Full observation received every game tick."""
    tick:          int
    self_state:    SelfState = None   # type: ignore  # aliased below
    zone:          Zone
    nearby_agents: list[NearbyAgent] = []
    nearby_loot:   list[NearbyLoot]  = []

    model_config = {"populate_by_name": True}

    # The platform sends the key as "self" (reserved in Python),
    # so we accept both "self" and "self_state".
    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        if isinstance(obj, dict) and "self" in obj and "self_state" not in obj:
            obj = {**obj, "self_state": obj.pop("self")}
        return super().model_validate(obj, *args, **kwargs)

    # Convenience aliases
    @property
    def me(self) -> SelfState:
        return self.self_state

    @property
    def x(self) -> int:
        return self.self_state.x

    @property
    def y(self) -> int:
        return self.self_state.y

    @property
    def hp(self) -> int:
        return self.self_state.hp

    @property
    def energy(self) -> int:
        return self.self_state.energy

    def in_zone(self) -> bool:
        return self.zone.contains(self.x, self.y)

    def adjacent_enemies(self) -> list[NearbyAgent]:
        return [
            a for a in self.nearby_agents
            if abs(a.x - self.x) <= 1 and abs(a.y - self.y) <= 1
        ]

    def nearest_enemy(self) -> NearbyAgent | None:
        if not self.nearby_agents:
            return None
        return min(self.nearby_agents, key=lambda a: abs(a.x - self.x) + abs(a.y - self.y))

    def nearest_loot(self) -> NearbyLoot | None:
        if not self.nearby_loot:
            return None
        return min(self.nearby_loot, key=lambda l: abs(l.x - self.x) + abs(l.y - self.y))

    def loot_at_position(self) -> NearbyLoot | None:
        return next((l for l in self.nearby_loot if l.x == self.x and l.y == self.y), None)


# ── Response (your agent returns this) ───────────────────────────────────────

class ActionResponse(BaseModel):
    action: Action

    @classmethod
    def from_str(cls, action: str) -> "ActionResponse":
        return cls(action=Action(action))
