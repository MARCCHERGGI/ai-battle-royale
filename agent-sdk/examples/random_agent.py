"""
Random Agent
============
Picks a random valid action every tick.
Useful as a baseline to beat — if your bot can't beat random, keep thinking.

Accepts an optional seed for reproducibility.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import random
from battleroyal import BattleAgent, Action, run
from battleroyal.models import Observation


class RandomAgent(BattleAgent):
    name = "RandomBot"

    ALL_ACTIONS = list(Action)

    def __init__(self, seed: int | None = None):
        self._rng = random.Random(seed)

    def decide(self, obs: Observation) -> Action:
        return self._rng.choice(self.ALL_ACTIONS)


if __name__ == "__main__":
    run(RandomAgent())
