"""
Game entities: AgentState and LootItem.
All mutable state lives here; the engine owns the instances.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


STARTING_HP = 100
STARTING_ENERGY = 100
STARTING_ATTACK = 10
STARTING_DEFENSE = 5


@dataclass
class Inventory:
    medkits: int = 0
    weapon_upgrades: int = 0
    shields: int = 0
    energy_boosts: int = 0

    def has_medkit(self) -> bool:
        return self.medkits > 0

    def has_energy_boost(self) -> bool:
        return self.energy_boosts > 0

    def has_shield(self) -> bool:
        return self.shields > 0


@dataclass
class AgentState:
    agent_id: str
    name: str
    x: int
    y: int
    hp: int = STARTING_HP
    energy: int = STARTING_ENERGY
    attack: int = STARTING_ATTACK
    defense: int = STARTING_DEFENSE
    inventory: Inventory = field(default_factory=Inventory)
    alive: bool = True
    defending: bool = False         # set for one tick when DEFEND is chosen
    strikes: int = 0                # timeout / invalid action counter
    place: Optional[int] = None     # final placement; 1 = winner
    eliminated_at_tick: Optional[int] = None

    def is_in_zone(self, zone_x1: int, zone_y1: int, zone_x2: int, zone_y2: int) -> bool:
        return zone_x1 <= self.x <= zone_x2 and zone_y1 <= self.y <= zone_y2

    def to_observation(self, tick: int, zone: dict, nearby_agents: list, nearby_loot: list) -> dict:
        """Return what the agent can see — local view only, no global state."""
        return {
            "tick": tick,
            "self": {
                "id": self.agent_id,
                "x": self.x,
                "y": self.y,
                "hp": self.hp,
                "energy": self.energy,
                "attack": self.attack,
                "defense": self.defense,
                "inventory": {
                    "medkits": self.inventory.medkits,
                    "weapon_upgrades": self.inventory.weapon_upgrades,
                    "shields": self.inventory.shields,
                    "energy_boosts": self.inventory.energy_boosts,
                },
            },
            "zone": zone,
            "nearby_agents": nearby_agents,   # agents within vision radius
            "nearby_loot": nearby_loot,        # loot within vision radius
        }


@dataclass
class LootItem:
    loot_id: str
    loot_type: str   # medkit | weapon_upgrade | shield | energy_boost
    x: int
    y: int
    picked_up: bool = False
