"""
Aggressive Agent
================
Priority: attack > chase enemy > move to zone center > wait

Strategy:
  1. If an enemy is adjacent — ATTACK immediately.
  2. If enemies are visible — charge toward the closest one.
  3. If outside the zone — move to zone center.
  4. Otherwise — WAIT and conserve energy.

Strength : high kill count
Weakness : dies to zone damage when chasing enemies too far
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from battleroyal import BattleAgent, Action, run
from battleroyal.models import Observation


class AggressiveAgent(BattleAgent):
    name = "AggressiveBot"

    def decide(self, obs: Observation) -> Action:
        # 1. Attack adjacent enemies immediately
        if obs.adjacent_enemies():
            return Action.ATTACK

        # 2. Chase nearest visible enemy
        target = obs.nearest_enemy()
        if target:
            return self.move_toward(obs.x, obs.y, target.x, target.y)

        # 3. Stay in zone
        if not obs.in_zone():
            return self.toward_zone_center(obs)

        # 4. Nothing to do
        return Action.WAIT


if __name__ == "__main__":
    run(AggressiveAgent())
