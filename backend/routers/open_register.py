"""
Open agent registration — Moltbook-style.
Agents register with just a name, get an API key + verification code.
Human verifies by tweeting the code from X/Twitter.
"""
import logging
import secrets
import uuid
import re

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_db
from backend.config import settings
from backend.models import Agent
from backend.schemas import (
    OpenAgentRegisterRequest,
    OpenAgentRegisterResponse,
    OpenAgentResponse,
    XVerifyRequest,
    XVerifyResponse,
)
from backend.security import rate_limit_register, rate_limit_global

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["open-registration"])

SITE_URL = "https://openfield-ai.vercel.app"


def _generate_api_key() -> str:
    """Generate an API key like openfield_sk_xxx."""
    return f"openfield_sk_{secrets.token_hex(24)}"


def _generate_verification_code() -> str:
    """Generate a short verification code like OF-XXXX-XXXX."""
    part1 = secrets.token_hex(2).upper()
    part2 = secrets.token_hex(2).upper()
    return f"OF-{part1}-{part2}"


def _fmt_open(agent: Agent) -> OpenAgentResponse:
    games = agent.wins + agent.losses
    return OpenAgentResponse(
        agent_id=str(agent.id),
        name=agent.name,
        description=agent.description,
        endpoint_url=agent.endpoint_url,
        x_handle=agent.x_handle,
        x_verified=agent.x_verified,
        wins=agent.wins,
        losses=agent.losses,
        games=games,
        win_rate=round(agent.wins / games * 100, 1) if games > 0 else 0,
        created_at=agent.created_at,
    )


# ── Register Agent (no wallet needed) ────────────────────────────────────────

@router.post(
    "/agents/register",
    response_model=OpenAgentRegisterResponse,
    status_code=201,
    dependencies=[Depends(rate_limit_register)],
)
async def register_agent_open(
    body: OpenAgentRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register an AI agent. No wallet required.
    Returns an API key and verification code for X/Twitter verification.
    """
    # Check name uniqueness
    result = await db.execute(
        select(Agent).where(Agent.name == body.name, Agent.is_active == True)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Agent name '{body.name}' is already taken")

    api_key = _generate_api_key()
    verification_code = _generate_verification_code()

    agent = Agent(
        name=body.name,
        description=body.description,
        endpoint_url=body.endpoint_url,
        api_key=api_key,
        verification_code=verification_code,
        x_verified=False,
    )
    db.add(agent)
    await db.flush()
    await db.commit()

    claim_url = f"{SITE_URL}/verify?agent_id={agent.id}&code={verification_code}"

    logger.info("Open agent registered: %s (id=%s)", agent.name, agent.id)

    return OpenAgentRegisterResponse(
        agent_id=str(agent.id),
        name=agent.name,
        api_key=api_key,
        verification_code=verification_code,
        claim_url=claim_url,
        status="unverified",
        message=(
            f"Agent '{agent.name}' registered successfully. "
            f"To verify ownership, tweet your verification code from X/Twitter. "
            f"Visit: {claim_url}"
        ),
    )


# ── Verify via X/Twitter ─────────────────────────────────────────────────────

@router.post(
    "/agents/verify-x",
    response_model=XVerifyResponse,
    dependencies=[Depends(rate_limit_global)],
)
async def verify_agent_x(
    body: XVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify an agent's identity via X/Twitter handle.
    The agent owner must have tweeted the verification code.
    In production, this would check the X API for the tweet.
    For now, it accepts the handle and marks as verified (manual/honor system).
    """
    try:
        agent_uuid = uuid.UUID(body.agent_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid agent_id format")

    result = await db.execute(
        select(Agent).where(Agent.id == agent_uuid, Agent.is_active == True)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if agent.x_verified:
        raise HTTPException(status_code=400, detail="Agent is already verified")

    # Normalize handle (remove leading @)
    handle = body.x_handle.lstrip("@")

    agent.x_handle = f"@{handle}"
    agent.x_verified = True
    await db.flush()
    await db.commit()

    logger.info("Agent verified via X: %s → @%s", agent.name, handle)

    return XVerifyResponse(
        agent_id=str(agent.id),
        x_handle=f"@{handle}",
        verified=True,
        message=f"Agent '{agent.name}' verified with X handle @{handle}",
    )


# ── Get Agent by API Key ─────────────────────────────────────────────────────

@router.get(
    "/agents/me",
    response_model=OpenAgentResponse,
    dependencies=[Depends(rate_limit_global)],
)
async def get_my_agent(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Get agent details using Bearer API key."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization: Bearer <api_key>")

    api_key = auth[7:].strip()
    if not api_key.startswith("openfield_sk_"):
        raise HTTPException(status_code=401, detail="Invalid API key format")

    result = await db.execute(
        select(Agent).where(Agent.api_key == api_key, Agent.is_active == True)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return _fmt_open(agent)


# ── List All Agents (public) ─────────────────────────────────────────────────

@router.get(
    "/agents",
    response_model=list[OpenAgentResponse],
    dependencies=[Depends(rate_limit_global)],
)
async def list_agents_open(
    db: AsyncSession = Depends(get_db),
):
    """List all registered agents (public)."""
    result = await db.execute(
        select(Agent)
        .where(Agent.is_active == True)
        .order_by(Agent.x_verified.desc(), Agent.wins.desc(), Agent.created_at)
        .limit(100)
    )
    agents = list(result.scalars().all())
    return [_fmt_open(a) for a in agents]


# ── Agent Status ──────────────────────────────────────────────────────────────

@router.get(
    "/agents/{agent_id}/status",
    dependencies=[Depends(rate_limit_global)],
)
async def agent_status(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get verification and match status for an agent."""
    try:
        agent_uuid = uuid.UUID(agent_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid agent_id format")

    result = await db.execute(
        select(Agent).where(Agent.id == agent_uuid, Agent.is_active == True)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {
        "agent_id": str(agent.id),
        "name": agent.name,
        "x_verified": agent.x_verified,
        "x_handle": agent.x_handle,
        "wins": agent.wins,
        "losses": agent.losses,
        "games": agent.wins + agent.losses,
        "ready_for_matches": agent.x_verified and agent.endpoint_url is not None,
    }
