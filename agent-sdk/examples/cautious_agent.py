"""
Cautious Agent
==============
Priority: heal > stay in zone > flee enemies > defend when cornered

Strategy:
  1. Heal when HP is low and energy allows.
  2. Stay in the safe zone — always.
  3. Flee from any visible enemy.
  4. DEFEND if an enemy is adjacent (can't flee).
  5. Otherwise wait and regenerate energy.

Strength : high survival rate, low zone damage
Weakness : never initiates combat, can be hunted down
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from battleroyal import BattleAgent, Action, run
from battleroyal.models import Observation

HP_HEAL_THRESHOLD     = 50   # heal if HP below this
ENERGY_HEAL_THRESHOLD = 20   # only heal if we have enough energy
HP_DEFEND_THRESHOLD   = 30   # defend instead of flee when very low HP


class CautiousAgent(BattleAgent):
    name = "CautiousBot"

    def decide(self, obs: Observation) -> Action:
        me = obs.me

        # 1. Heal when hurt and have enough energy
        if me.hp < HP_HEAL_THRESHOLD and me.energy >= ENERGY_HEAL_THRESHOLD:
            return Action.HEAL

        # 2. Always stay in zone first
        if not obs.in_zone():
            return self.toward_zone_center(obs)

        # 3. React to nearby enemies
        enemies = obs.nearby_agents
        if enemies:
            closest = obs.nearest_enemy()
            adjacent = obs.adjacent_enemies()

            # Cornered and critically low HP — defend
            if adjacent and me.hp < HP_DEFEND_THRESHOLD:
                return Action.DEFEND

            # Flee from the closest enemy
            if closest:
                flee_action = self.move_away(obs.x, obs.y, closest.x, closest.y)

                # Make sure fleeing doesn't leave the zone
                proposed_x, proposed_y = _apply_move(obs.x, obs.y, flee_action)
                if obs.zone.contains(proposed_x, proposed_y):
                    return flee_action

                # Fleeing would leave zone — just defend instead
                return Action.DEFEND

        # 4. Drift toward zone center to stay safe as zone shrinks
        cx, cy = obs.zone.center()
        if abs(obs.x - cx) > 5 or abs(obs.y - cy) > 5:
            return self.toward_zone_center(obs)

        # 5. Regen energy by waiting
        return Action.WAIT


def _apply_move(x: int, y: int, action: Action) -> tuple[int, int]:
    return {
        Action.MOVE_UP:    (x,     y - 1),
        Action.MOVE_DOWN:  (x,     y + 1),
        Action.MOVE_LEFT:  (x - 1, y),
        Action.MOVE_RIGHT: (x + 1, y),
    }.get(action, (x, y))


if __name__ == "__main__":
    run(CautiousAgent())
