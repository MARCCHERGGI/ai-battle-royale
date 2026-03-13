"""
5 dummy bot strategies for testing.
Each implements: decide_action(observation: dict) -> str
"""
from __future__ import annotations
import random
from engine.actions import Action, VISION_RADIUS


class BaseBot:
    """Abstract base. Real user agents implement this interface via HTTP."""
    name: str = "BaseBot"

    def decide_action(self, obs: dict) -> str:
        raise NotImplementedError


# ── 1. Random Bot ─────────────────────────────────────────────────────────────

class RandomBot(BaseBot):
    """Picks a uniformly random action every tick."""
    name = "RandomBot"

    def __init__(self, seed: int | None = None):
        self._rng = random.Random(seed)

    def decide_action(self, obs: dict) -> str:
        return self._rng.choice(list(Action)).value


# ── 2. Aggressive Bot ─────────────────────────────────────────────────────────

class AggressiveBot(BaseBot):
    """Always attacks if someone is adjacent, otherwise charges toward nearest enemy."""
    name = "AggressiveBot"

    def __init__(self, seed: int | None = None):
        self._rng = random.Random(seed)

    def decide_action(self, obs: dict) -> str:
        me = obs["self"]
        nearby = obs["nearby_agents"]

        adjacent = [a for a in nearby if abs(a["x"] - me["x"]) <= 1 and abs(a["y"] - me["y"]) <= 1]
        if adjacent:
            return Action.ATTACK.value

        if nearby:
            # move toward closest enemy
            target = min(nearby, key=lambda a: abs(a["x"] - me["x"]) + abs(a["y"] - me["y"]))
            return _move_toward(me, target)

        return Action.WAIT.value


# ── 3. Coward Bot ─────────────────────────────────────────────────────────────

class CowardBot(BaseBot):
    """Runs away from enemies, heals when hurt, loots when safe."""
    name = "CowardBot"

    def __init__(self, seed: int | None = None):
        self._rng = random.Random(seed)

    def decide_action(self, obs: dict) -> str:
        me = obs["self"]
        nearby = obs["nearby_agents"]

        if me["hp"] < 40 and me["energy"] >= 20:
            return Action.HEAL.value

        if obs["nearby_loot"] and not nearby:
            return Action.LOOT.value

        if nearby:
            # flee from closest
            target = min(nearby, key=lambda a: abs(a["x"] - me["x"]) + abs(a["y"] - me["y"]))
            return _move_away(me, target, obs)

        return _move_to_zone_center(me, obs["zone"])


# ── 4. Looter Bot ─────────────────────────────────────────────────────────────

class LooterBot(BaseBot):
    """Prioritizes looting, fights only when cornered."""
    name = "LooterBot"

    def __init__(self, seed: int | None = None):
        self._rng = random.Random(seed)

    def decide_action(self, obs: dict) -> str:
        me = obs["self"]
        nearby = obs["nearby_agents"]
        loot = obs["nearby_loot"]

        if loot:
            # move toward nearest loot
            target = min(loot, key=lambda l: abs(l["x"] - me["x"]) + abs(l["y"] - me["y"]))
            if target["x"] == me["x"] and target["y"] == me["y"]:
                return Action.LOOT.value
            return _move_toward(me, target)

        adjacent = [a for a in nearby if abs(a["x"] - me["x"]) <= 1 and abs(a["y"] - me["y"]) <= 1]
        if adjacent:
            return Action.ATTACK.value

        return _move_to_zone_center(me, obs["zone"])


# ── 5. Zone-Aware Survivalist ─────────────────────────────────────────────────

class SurvivalistBot(BaseBot):
    """Stays inside the zone, defends when low HP, attacks opportunistically."""
    name = "SurvivalistBot"

    def __init__(self, seed: int | None = None):
        self._rng = random.Random(seed)

    def decide_action(self, obs: dict) -> str:
        me = obs["self"]
        zone = obs["zone"]
        nearby = obs["nearby_agents"]

        # Stay in zone
        if not _in_zone(me, zone):
            return _move_to_zone_center(me, zone)

        if me["hp"] < 50:
            return Action.DEFEND.value

        adjacent = [a for a in nearby if abs(a["x"] - me["x"]) <= 1 and abs(a["y"] - me["y"]) <= 1]
        if adjacent:
            return Action.ATTACK.value

        if obs["nearby_loot"]:
            return Action.LOOT.value

        return Action.WAIT.value


# ── Helpers ───────────────────────────────────────────────────────────────────

def _move_toward(me: dict, target: dict) -> str:
    dx = target["x"] - me["x"]
    dy = target["y"] - me["y"]
    if abs(dx) >= abs(dy):
        return Action.MOVE_RIGHT.value if dx > 0 else Action.MOVE_LEFT.value
    return Action.MOVE_DOWN.value if dy > 0 else Action.MOVE_UP.value


def _move_away(me: dict, target: dict, obs: dict) -> str:
    dx = me["x"] - target["x"]
    dy = me["y"] - target["y"]
    if abs(dx) >= abs(dy):
        return Action.MOVE_RIGHT.value if dx > 0 else Action.MOVE_LEFT.value
    return Action.MOVE_DOWN.value if dy > 0 else Action.MOVE_UP.value


def _move_to_zone_center(me: dict, zone: dict) -> str:
    cx = (zone["x1"] + zone["x2"]) // 2
    cy = (zone["y1"] + zone["y2"]) // 2
    return _move_toward(me, {"x": cx, "y": cy})


def _in_zone(me: dict, zone: dict) -> bool:
    return zone["x1"] <= me["x"] <= zone["x2"] and zone["y1"] <= me["y"] <= zone["y2"]


ALL_BOT_CLASSES = [RandomBot, AggressiveBot, CowardBot, LooterBot, SurvivalistBot]
