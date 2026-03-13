"""
Loot-First Agent
================
Priority: loot > upgrade > survive > fight only when forced

Strategy:
  1. Pick up loot at current position immediately.
  2. Move toward the best visible loot.
     Prioritises weapon_upgrade > shield > medkit > energy_boost
  3. Stay in zone.
  4. Fight only if cornered (enemy is adjacent).
  5. Heal if hurt and not near loot.

Strength : strong late-game thanks to accumulated upgrades
Weakness : slow start, vulnerable while looting in early ticks
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from battleroyal import BattleAgent, Action, run
from battleroyal.models import Observation, NearbyLoot

# How much we value each loot type (higher = more attractive)
LOOT_PRIORITY = {
    "weapon_upgrade": 4,
    "shield":         3,
    "medkit":         2,
    "energy_boost":   1,
}


class LootFirstAgent(BattleAgent):
    name = "LooterBot"

    def decide(self, obs: Observation) -> Action:
        me = obs.me

        # 1. Pick up loot we're already standing on
        if obs.loot_at_position():
            return Action.LOOT

        # 2. Go to the most valuable visible loot
        target_loot = _best_loot(obs)
        if target_loot:
            # Standing on it — pick up
            if target_loot.x == obs.x and target_loot.y == obs.y:
                return Action.LOOT
            # Move toward it (but stay in zone)
            move = self.move_toward(obs.x, obs.y, target_loot.x, target_loot.y)
            return move

        # 3. Stay in zone
        if not obs.in_zone():
            return self.toward_zone_center(obs)

        # 4. Fight if cornered
        if obs.adjacent_enemies():
            return Action.ATTACK

        # 5. Heal if hurt
        if me.hp < 60 and me.energy >= 20:
            return Action.HEAL

        # 6. Drift toward zone center to encounter more loot
        return self.toward_zone_center(obs)


def _best_loot(obs: Observation) -> NearbyLoot | None:
    if not obs.nearby_loot:
        return None

    def score(loot: NearbyLoot) -> float:
        priority = LOOT_PRIORITY.get(loot.type, 0)
        dist = abs(loot.x - obs.x) + abs(loot.y - obs.y)
        # Higher priority, shorter distance = better score
        return priority * 10 - dist

    return max(obs.nearby_loot, key=score)


if __name__ == "__main__":
    run(LootFirstAgent())
