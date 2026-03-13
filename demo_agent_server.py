"""
Demo agent server — runs on a different port and responds to /act requests.
This simulates what a real user's agent service would look like.

Usage:
    python demo_agent_server.py --port 9001 --strategy survivalist
    python demo_agent_server.py --port 9002 --strategy aggressive

Strategies: random | aggressive | coward | looter | survivalist
"""
import argparse
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from engine.bots import RandomBot, AggressiveBot, CowardBot, LooterBot, SurvivalistBot

BOTS = {
    "random": RandomBot,
    "aggressive": AggressiveBot,
    "coward": CowardBot,
    "looter": LooterBot,
    "survivalist": SurvivalistBot,
}

app = FastAPI(title="Demo Agent Server")
_bot = None


class ActRequest(BaseModel):
    tick: int
    model_config = {"extra": "allow"}  # accept full observation


@app.get("/health")
def health():
    return {"status": "ok", "strategy": _bot.name}


@app.post("/act")
def act(body: ActRequest):
    obs = body.model_dump()
    action = _bot.decide_action(obs)
    return {"action": action}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=9001)
    parser.add_argument("--strategy", default="survivalist", choices=list(BOTS))
    args = parser.parse_args()

    _bot = BOTS[args.strategy](seed=args.port)
    print(f"[Demo Agent] strategy={args.strategy} port={args.port}")
    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="warning")
