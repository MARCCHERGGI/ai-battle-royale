"""
Battle Royale Agent SDK
=======================

Quick start:

    from battleroyal import BattleAgent, Action, run
    from battleroyal.models import Observation

    class MyAgent(BattleAgent):
        name = "MyBot"

        def decide(self, obs: Observation) -> Action:
            if obs.adjacent_enemies():
                return Action.ATTACK
            if not obs.in_zone():
                return self.toward_zone_center(obs)
            return Action.WAIT

    if __name__ == "__main__":
        run(MyAgent())
"""
from battleroyal.agent  import BattleAgent
from battleroyal.models import Action, Observation, ActionResponse
from battleroyal.server import run, create_app
from battleroyal.config import config

__all__ = [
    "BattleAgent",
    "Action",
    "Observation",
    "ActionResponse",
    "run",
    "create_app",
    "config",
]
__version__ = "1.0.0"
