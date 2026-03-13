import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_db
from backend.config import settings
from backend.schemas import AgentRegisterRequest, AgentResponse
from backend.services.agent_caller import check_agent_health
from backend.security import validate_agent_url, rate_limit_register, rate_limit_global
from backend.models import Agent
from backend import crud

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


def _fmt(agent, wallet: str) -> AgentResponse:
    games = agent.wins + agent.losses
    return AgentResponse(
        agent_id=str(agent.id),
        name=agent.name,
        endpoint_url=agent.endpoint_url,
        owner_wallet=wallet,
        description=agent.description,
        wins=agent.wins,
        losses=agent.losses,
        games=games,
        win_rate=round(agent.wins / games * 100, 1) if games > 0 else 0,
        created_at=agent.created_at,
    )


def _parse_uuid(value: str, label: str = "ID") -> uuid.UUID:
    """Parse a string as UUID, raising 400 on invalid format."""
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail=f"Invalid {label} format")


@router.post(
    "", response_model=AgentResponse, status_code=201,
    dependencies=[Depends(rate_limit_register)],
)
async def register_agent(body: AgentRegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register an AI agent. Creates the user record if wallet is new."""
    # SSRF: validate endpoint URL resolves to a public IP
    try:
        validated_url = validate_agent_url(body.endpoint_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    user = await crud.get_or_create_user(db, body.wallet_address)

    # Per-wallet agent limit to prevent spam
    result = await db.execute(
        select(func.count()).select_from(Agent)
        .where(Agent.owner_id == user.id, Agent.is_active == True)
    )
    agent_count = result.scalar_one()
    if agent_count >= settings.MAX_AGENTS_PER_WALLET:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {settings.MAX_AGENTS_PER_WALLET} active agents per wallet",
        )

    agent = await crud.create_agent(
        db,
        owner_id=user.id,
        name=body.name,
        endpoint_url=validated_url,
        description=body.description,
    )
    logger.info("Agent registered: %s by wallet %s", agent.name, user.wallet_address)
    return _fmt(agent, user.wallet_address)


@router.get(
    "", response_model=list[AgentResponse],
    dependencies=[Depends(rate_limit_global)],
)
async def list_agents(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    agents = await crud.list_agents(db, limit=limit, offset=offset)
    return [_fmt(a, a.owner.wallet_address) for a in agents]


@router.get(
    "/{agent_id}", response_model=AgentResponse,
    dependencies=[Depends(rate_limit_global)],
)
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    aid = _parse_uuid(agent_id, "agent_id")
    agent = await crud.get_agent(db, aid)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return _fmt(agent, agent.owner.wallet_address)


@router.get(
    "/{agent_id}/ping",
    dependencies=[Depends(rate_limit_global)],
)
async def ping_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    """Check if the agent's HTTP endpoint is reachable."""
    aid = _parse_uuid(agent_id, "agent_id")
    agent = await crud.get_agent(db, aid)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    reachable = await check_agent_health(agent.endpoint_url)
    return {"agent_id": agent_id, "reachable": reachable, "endpoint": agent.endpoint_url}
