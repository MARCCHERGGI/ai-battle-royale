"""
Action constants and resolution logic.
Combat is deterministic given the RNG seed.
"""
from __future__ import annotations
from enum import Enum
import random
from engine.entities import AgentState, LootItem, Inventory

VISION_RADIUS = 7   # cells; agents can only see this far


class Action(str, Enum):
    MOVE_UP = "MOVE_UP"
    MOVE_DOWN = "MOVE_DOWN"
    MOVE_LEFT = "MOVE_LEFT"
    MOVE_RIGHT = "MOVE_RIGHT"
    ATTACK = "ATTACK"
    DEFEND = "DEFEND"
    LOOT = "LOOT"
    HEAL = "HEAL"
    WAIT = "WAIT"


VALID_ACTIONS = {a.value for a in Action}

LOOT_EFFECTS = {
    "medkit":          {"hp": 30},
    "weapon_upgrade":  {"attack": 5},
    "shield":          {"defense": 3},
    "energy_boost":    {"energy": 40},
}

HEAL_ENERGY_COST = 20
HEAL_HP_RESTORE = 20
ATTACK_ENERGY_COST = 5
MOVE_ENERGY_COST = 1


def resolve_move(agent: AgentState, action: Action, map_size: int) -> None:
    if agent.energy < MOVE_ENERGY_COST:
        return  # not enough energy — treat as WAIT

    dx, dy = 0, 0
    if action == Action.MOVE_UP:
        dy = -1
    elif action == Action.MOVE_DOWN:
        dy = 1
    elif action == Action.MOVE_LEFT:
        dx = -1
    elif action == Action.MOVE_RIGHT:
        dx = 1

    nx = max(0, min(map_size - 1, agent.x + dx))
    ny = max(0, min(map_size - 1, agent.y + dy))
    agent.x, agent.y = nx, ny
    agent.energy = max(0, agent.energy - MOVE_ENERGY_COST)


def resolve_attack(attacker: AgentState, all_agents: list[AgentState], rng: random.Random) -> None:
    """Attack a random adjacent alive enemy."""
    if attacker.energy < ATTACK_ENERGY_COST:
        return

    targets = [
        a for a in all_agents
        if a.alive and a.agent_id != attacker.agent_id
        and abs(a.x - attacker.x) <= 1 and abs(a.y - attacker.y) <= 1
    ]
    if not targets:
        return

    target = rng.choice(targets)
    effective_defense = target.defense * 2 if target.defending else target.defense
    damage = max(1, attacker.attack - effective_defense + rng.randint(-2, 2))
    target.hp -= damage
    attacker.energy = max(0, attacker.energy - ATTACK_ENERGY_COST)

    if target.hp <= 0:
        target.hp = 0
        target.alive = False


def resolve_loot(agent: AgentState, loot_items: list[LootItem]) -> None:
    """Pick up the first available loot at this position."""
    for item in loot_items:
        if not item.picked_up and item.x == agent.x and item.y == agent.y:
            item.picked_up = True
            effects = LOOT_EFFECTS.get(item.loot_type, {})
            if "hp" in effects:
                agent.hp = min(STARTING_HP_CAP, agent.hp + effects["hp"])
            if "attack" in effects:
                agent.attack += effects["attack"]
            if "defense" in effects:
                agent.defense += effects["defense"]
            if "energy" in effects:
                agent.energy = min(100, agent.energy + effects["energy"])
            # track in inventory
            inv = agent.inventory
            if item.loot_type == "medkit":
                inv.medkits += 1
            elif item.loot_type == "weapon_upgrade":
                inv.weapon_upgrades += 1
            elif item.loot_type == "shield":
                inv.shields += 1
            elif item.loot_type == "energy_boost":
                inv.energy_boosts += 1
            break  # one item per tick


def resolve_heal(agent: AgentState) -> None:
    if agent.energy >= HEAL_ENERGY_COST and agent.hp < STARTING_HP_CAP:
        agent.energy -= HEAL_ENERGY_COST
        agent.hp = min(STARTING_HP_CAP, agent.hp + HEAL_HP_RESTORE)


# Cap so weapon upgrades don't go to infinity
STARTING_HP_CAP = 150
