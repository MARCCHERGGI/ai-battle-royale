"""
Runnable example — simulates a full match and prints results.
Usage:
    python run_simulation.py                  # 20 agents, default seed
    python run_simulation.py --agents 100     # scale up
    python run_simulation.py --seed 1337      # specific seed
"""
import argparse
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from engine.engine import BattleRoyaleEngine
from engine.bots import ALL_BOT_CLASSES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)


def build_agents(count: int, seed: int):
    agents = []
    for i in range(count):
        BotClass = ALL_BOT_CLASSES[i % len(ALL_BOT_CLASSES)]
        name = f"{BotClass.name}_{i:03d}"
        agents.append((BotClass(seed=seed + i), name))
    return agents


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agents", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--map-size", type=int, default=50)
    parser.add_argument("--verbose-ticks", action="store_true")
    args = parser.parse_args()

    if args.verbose_ticks:
        logging.getLogger().setLevel(logging.DEBUG)

    print(f"\n{'='*60}")
    print(f"  AI AGENT BATTLE ROYALE  |  {args.agents} agents  |  seed={args.seed}")
    print(f"  Map: {args.map_size}x{args.map_size}")
    print(f"{'='*60}\n")

    agents = build_agents(args.agents, args.seed)

    last_tick_log = {"tick": 0, "alive": 0}

    def on_tick(log):
        # Print a summary line every 10 ticks or on important events
        if log.tick % 10 == 0 or log.events:
            print(f"  Tick {log.tick:4d}  |  Alive: {log.alive_count:3d}  "
                  f"|  Zone: {log.zone['x1']},{log.zone['y1']} to {log.zone['x2']},{log.zone['y2']}"
                  + (f"  |  {'; '.join(log.events)}" if log.events else ""))
        last_tick_log["tick"] = log.tick
        last_tick_log["alive"] = log.alive_count

    engine = BattleRoyaleEngine(
        agents=agents,
        seed=args.seed,
        map_size=args.map_size,
        tick_callback=on_tick,
    )

    result = engine.run()

    print(f"\n{'='*60}")
    print(f"  MATCH OVER  |  {result.total_ticks} ticks")
    print(f"  WINNER: {result.winner_name} (id={result.winner_id})")
    print(f"{'='*60}")
    print(f"\n  Final Rankings:")
    print(f"  {'Place':>5}  {'Name':<30}  {'Elim Tick':>10}  {'HP':>5}")
    print(f"  {'-'*55}")
    for r in result.rankings:
        elim = str(r["eliminated_at_tick"]) if r["eliminated_at_tick"] else "SURVIVED"
        print(f"  {r['place']:>5}  {r['name']:<30}  {elim:>10}  {r['hp_remaining']:>5}")
    print()


if __name__ == "__main__":
    main()
