"""
HTTP server that exposes your agent as /health and /act endpoints.
Uses FastAPI internally. You don't need to touch FastAPI directly.
"""
from __future__ import annotations
import logging
import os
import time
from typing import Any

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from battleroyal.agent import BattleAgent
from battleroyal.models import Action, ActionResponse, Observation
from battleroyal.config import config

logger = logging.getLogger(__name__)


def create_app(agent: BattleAgent) -> FastAPI:
    """
    Build and return the FastAPI app for an agent.
    Call this if you need to mount it in an existing ASGI app.
    """
    app = FastAPI(
        title=f"Battle Royale Agent — {agent.name}",
        docs_url="/docs",
    )

    start_time = time.time()
    tick_count = 0
    last_obs: dict[str, Any] = {}

    # ── GET /health ──────────────────────────────────────────────────────────

    @app.get("/health")
    async def health():
        """Platform pings this before a match starts."""
        return {
            "status": "ok",
            "agent":  agent.name,
            "uptime_seconds": round(time.time() - start_time, 1),
            "ticks_processed": tick_count,
        }

    # ── POST /act ────────────────────────────────────────────────────────────

    @app.post("/act")
    async def act(request: Request):
        """
        Receive a game tick observation, return an action.
        The platform expects: { "action": "MOVE_RIGHT" }
        """
        nonlocal tick_count, last_obs

        body = await request.json()
        last_obs = body

        try:
            obs = Observation.model_validate(body)
        except Exception as e:
            logger.error(f"[{agent.name}] Invalid observation: {e}")
            return JSONResponse({"action": Action.WAIT.value}, status_code=200)

        try:
            raw = agent.decide(obs)
            action = raw.value if isinstance(raw, Action) else str(raw)
            # Validate
            Action(action)
        except Exception as e:
            logger.error(f"[{agent.name}] decide() error: {e}")
            action = Action.WAIT.value

        tick_count += 1
        logger.debug(f"[{agent.name}] tick={obs.tick} pos=({obs.x},{obs.y}) hp={obs.hp} → {action}")
        return {"action": action}

    # ── GET /debug ────────────────────────────────────────────────────────────

    @app.get("/debug")
    async def debug():
        """Last observation received — useful for local debugging."""
        return {"agent": agent.name, "last_observation": last_obs}

    return app


def run(
    agent: BattleAgent,
    host: str | None = None,
    port: int | None = None,
    log_level: str | None = None,
) -> None:
    """
    Start the agent server. Blocks until killed.

    Args:
        agent:     Your BattleAgent subclass instance.
        host:      Bind address. Defaults to AGENT_HOST env var or "0.0.0.0".
        port:      Port number. Defaults to AGENT_PORT env var or 9000.
        log_level: "debug" | "info" | "warning". Defaults to AGENT_LOG_LEVEL or "info".
    """
    h = host      or config.host
    p = port      or config.port
    ll = log_level or config.log_level

    logging.basicConfig(
        level=getattr(logging, ll.upper(), logging.INFO),
        format="%(asctime)s  %(levelname)-7s  %(message)s",
        datefmt="%H:%M:%S",
    )

    app = create_app(agent)

    print(f"\n  Agent   : {agent.name}")
    print(f"  Endpoint: http://{h}:{p}")
    print(f"  Docs    : http://{h}:{p}/docs")
    print(f"  Health  : http://{h}:{p}/health")
    print(f"  Debug   : http://{h}:{p}/debug\n")

    uvicorn.run(app, host=h, port=p, log_level=ll)
