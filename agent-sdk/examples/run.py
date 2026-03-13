"""
Unified runner — start any example agent from the command line.

Usage:
    python examples/run.py aggressive         # port 9001
    python examples/run.py cautious           # port 9002
    python examples/run.py loot               # port 9003
    python examples/run.py random             # port 9004
    python examples/run.py aggressive --port 8888
"""
import sys, os, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from battleroyal import run
from aggressive_agent import AggressiveAgent
from cautious_agent    import CautiousAgent
from loot_first_agent  import LootFirstAgent
from random_agent      import RandomAgent

AGENTS = {
    "aggressive": (AggressiveAgent, 9001),
    "cautious":   (CautiousAgent,   9002),
    "loot":       (LootFirstAgent,  9003),
    "random":     (RandomAgent,     9004),
}

def main():
    parser = argparse.ArgumentParser(description="Start a Battle Royale example agent")
    parser.add_argument("agent", choices=list(AGENTS), help="Which agent to run")
    parser.add_argument("--port", type=int, default=None, help="Override port")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    args = parser.parse_args()

    AgentClass, default_port = AGENTS[args.agent]
    port = args.port or default_port
    run(AgentClass(), host=args.host, port=port)

if __name__ == "__main__":
    main()
