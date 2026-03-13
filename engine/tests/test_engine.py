"""
Tests for the BattleRoyaleEngine.
Run with: python -m pytest engine/tests/ -v
"""
import pytest
from engine.engine import BattleRoyaleEngine
from engine.bots import (
    RandomBot, AggressiveBot, CowardBot, LooterBot, SurvivalistBot
)
from engine.actions import Action, VALID_ACTIONS
from engine.map import Zone


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_bots(count: int, seed: int = 0):
    classes = [RandomBot, AggressiveBot, CowardBot, LooterBot, SurvivalistBot]
    return [(classes[i % len(classes)](seed + i), f"Bot_{i}") for i in range(count)]


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_single_winner():
    """A match must always produce exactly one winner."""
    bots = make_bots(10, seed=42)
    engine = BattleRoyaleEngine(agents=bots, seed=42, map_size=20)
    result = engine.run()
    assert result.winner_id is not None
    assert result.winner_name is not None


def test_determinism():
    """Same seed must produce identical results."""
    bots_a = make_bots(10, seed=7)
    bots_b = make_bots(10, seed=7)
    r1 = BattleRoyaleEngine(agents=bots_a, seed=7, map_size=20).run()
    r2 = BattleRoyaleEngine(agents=bots_b, seed=7, map_size=20).run()
    assert r1.winner_name == r2.winner_name
    assert r1.total_ticks == r2.total_ticks
    assert [r["name"] for r in r1.rankings] == [r["name"] for r in r2.rankings]


def test_different_seeds_can_differ():
    """Different seeds should (usually) produce different outcomes."""
    bots_a = make_bots(10, seed=1)
    bots_b = make_bots(10, seed=2)
    r1 = BattleRoyaleEngine(agents=bots_a, seed=1, map_size=20).run()
    r2 = BattleRoyaleEngine(agents=bots_b, seed=2, map_size=20).run()
    # Not guaranteed, but very likely with 10 bots
    assert (r1.winner_name != r2.winner_name) or (r1.total_ticks != r2.total_ticks)


def test_rankings_are_complete():
    """Rankings must include every agent exactly once."""
    bots = make_bots(5, seed=99)
    result = BattleRoyaleEngine(agents=bots, seed=99, map_size=15).run()
    assert len(result.rankings) == 5
    names = {r["name"] for r in result.rankings}
    assert names == {f"Bot_{i}" for i in range(5)}


def test_rankings_have_valid_places():
    """Places must be 1..N with place 1 being the winner."""
    bots = make_bots(5, seed=11)
    result = BattleRoyaleEngine(agents=bots, seed=11, map_size=15).run()
    places = sorted(r["place"] for r in result.rankings)
    assert places == list(range(1, 6))
    winner_rank = next(r for r in result.rankings if r["place"] == 1)
    assert winner_rank["name"] == result.winner_name


def test_zone_shrinks_over_time():
    """Zone must shrink as ticks advance."""
    bots = make_bots(20, seed=5)
    logs = []
    engine = BattleRoyaleEngine(
        agents=bots,
        seed=5,
        map_size=30,
        zone_shrink_interval=5,
        tick_callback=lambda log: logs.append(log),
    )
    engine.run()
    zones = [l.zone for l in logs]
    widths = [z["x2"] - z["x1"] for z in zones]
    # Width should decrease at some point
    assert min(widths) < max(widths)


def test_tick_logs_are_ordered():
    bots = make_bots(8, seed=3)
    result = BattleRoyaleEngine(agents=bots, seed=3, map_size=20).run()
    ticks = [l.tick for l in result.tick_logs]
    assert ticks == list(range(1, len(ticks) + 1))


def test_large_match():
    """100 agents should complete without error."""
    bots = make_bots(100, seed=0)
    result = BattleRoyaleEngine(agents=bots, seed=0, map_size=50).run()
    assert result.winner_id is not None
    assert len(result.rankings) == 100


def test_zone_shrink_logic():
    z = Zone(0, 0, 49, 49)
    z.shrink(2)
    assert z.x1 == 2 and z.y1 == 2
    assert z.x2 == 47 and z.y2 == 47


def test_all_bots_produce_valid_actions():
    """Every bot strategy must return only valid action strings."""
    obs = {
        "tick": 1,
        "self": {"id": "x", "x": 25, "y": 25, "hp": 80, "energy": 80,
                 "attack": 10, "defense": 5,
                 "inventory": {"medkits": 0, "weapon_upgrades": 0, "shields": 0, "energy_boosts": 0}},
        "zone": {"x1": 5, "y1": 5, "x2": 45, "y2": 45},
        "nearby_agents": [{"id": "y", "x": 26, "y": 25, "hp": 50}],
        "nearby_loot": [{"id": "l1", "type": "medkit", "x": 25, "y": 26}],
    }
    from engine.bots import ALL_BOT_CLASSES
    for BotClass in ALL_BOT_CLASSES:
        bot = BotClass()
        action = bot.decide_action(obs)
        assert action in VALID_ACTIONS, f"{BotClass.name} returned invalid action: {action}"
