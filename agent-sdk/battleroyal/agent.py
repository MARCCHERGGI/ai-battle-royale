"""
Base class for all Battle Royale agents.

Subclass BattleAgent and implement decide().
That's all you need.

Example:
    from battleroyal import BattleAgent, Action
    from battleroyal.models import Observation

    class MyAgent(BattleAgent):
        name = "MyBot"

        def decide(self, obs: Observation) -> Action:
            if obs.adjacent_enemies():
                return Action.ATTACK
            return Action.MOVE_RIGHT

    if __name__ == "__main__":
        from battleroyal import run
        run(MyAgent())
"""
from __future__ import annotations
from battleroyal.models import Action, Observation


class BattleAgent:
    """
    Minimal base class for a Battle Royale agent.

    Override decide() with your strategy.
    The server calls decide() once per tick with the current observation.
    Return one of the Action enum values (or its string equivalent).
    """

    #: Display name shown in logs and platform registration.
    name: str = "UnnamedAgent"

    def decide(self, obs: Observation) -> Action | str:
        """
        Called every game tick. Return the action to take.

        Args:
            obs: Full observation — your position, HP, nearby agents,
                 nearby loot, and the current safe zone.

        Returns:
            One of the Action values:
            MOVE_UP | MOVE_DOWN | MOVE_LEFT | MOVE_RIGHT
            ATTACK | DEFEND | LOOT | HEAL | WAIT
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement decide(obs) -> Action"
        )

    # ── Helpers you can use in your agent ────────────────────────────────────

    @staticmethod
    def move_toward(ox: int, oy: int, tx: int, ty: int) -> Action:
        """Return the best cardinal move from (ox, oy) toward (tx, ty)."""
        dx, dy = tx - ox, ty - oy
        if abs(dx) >= abs(dy):
            return Action.MOVE_RIGHT if dx > 0 else Action.MOVE_LEFT
        return Action.MOVE_DOWN if dy > 0 else Action.MOVE_UP

    @staticmethod
    def move_away(ox: int, oy: int, tx: int, ty: int) -> Action:
        """Return the best cardinal move from (ox, oy) away from (tx, ty)."""
        dx, dy = ox - tx, oy - ty
        if abs(dx) >= abs(dy):
            return Action.MOVE_RIGHT if dx > 0 else Action.MOVE_LEFT
        return Action.MOVE_DOWN if dy > 0 else Action.MOVE_UP

    @staticmethod
    def toward_zone_center(obs: Observation) -> Action:
        """Move toward the center of the current safe zone."""
        cx, cy = obs.zone.center()
        return BattleAgent.move_toward(obs.x, obs.y, cx, cy)
