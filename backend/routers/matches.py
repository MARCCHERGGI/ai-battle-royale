import asyncio
import logging
import secrets
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_db, AsyncSessionLocal
from backend.config import settings
from backend.schemas import (
    MatchCreateRequest, MatchJoinRequest,
    MatchResponse, MatchListItem, MatchStateResponse,
    MatchResultResponse, ParticipantResponse, TickResponse,
)
from backend.store import store   # in-memory live cache
from backend.services.match_runner import NetworkMatchRunner
from backend.security import rate_limit_write, rate_limit_global
from backend import crud

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/matches", tags=["matches"])

_running_tasks: dict[str, asyncio.Task] = {}

VALID_STATUSES = {"open", "starting", "active", "finished", "cancelled"}


def _parse_uuid(value: str, label: str = "ID") -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail=f"Invalid {label} format")


# ── Create ─────────────────────────────────────────────────────────────────────

@router.post(
    "", response_model=MatchResponse, status_code=201,
    dependencies=[Depends(rate_limit_write)],
)
async def create_match(body: MatchCreateRequest, db: AsyncSession = Depends(get_db)):
    # Limit concurrent active matches to prevent resource exhaustion
    active = await crud.active_match_count(db)
    if active >= settings.MAX_CONCURRENT_MATCHES:
        raise HTTPException(
            status_code=429,
            detail=f"Too many active matches ({active}). Wait for one to finish.",
        )

    # Use cryptographically random seed if not provided (prevents seed prediction)
    seed = body.seed if body.seed is not None else secrets.randbelow(2**31)
    match = await crud.create_match(db, seed=seed, map_size=body.map_size, max_agents=body.max_agents)
    logger.info("Match created: %s (seed=%d, max=%d)", str(match.id)[:8], seed, body.max_agents)
    return _fmt_match(match)


# ── List ───────────────────────────────────────────────────────────────────────

@router.get(
    "", response_model=list[MatchListItem],
    dependencies=[Depends(rate_limit_global)],
)
async def list_matches(
    status: str | None = Query(None, description="open | active | finished"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    # Validate status filter
    if status and status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {sorted(VALID_STATUSES)}")

    matches = await crud.list_matches(db, status=status, limit=limit, offset=offset)
    return [
        MatchListItem(
            match_id=str(m.id),
            status=m.status,
            max_agents=m.max_agents,
            agent_count=len(m.participants),
            created_at=m.created_at,
            started_at=m.started_at,
            finished_at=m.finished_at,
        )
        for m in matches
    ]


# ── Detail ─────────────────────────────────────────────────────────────────────

@router.get(
    "/{match_id}", response_model=MatchResponse,
    dependencies=[Depends(rate_limit_global)],
)
async def get_match(match_id: str, db: AsyncSession = Depends(get_db)):
    mid = _parse_uuid(match_id, "match_id")
    match = await crud.get_match(db, mid)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return _fmt_match(match)


# ── Join ───────────────────────────────────────────────────────────────────────

@router.post(
    "/{match_id}/join",
    dependencies=[Depends(rate_limit_write)],
)
async def join_match(match_id: str, body: MatchJoinRequest, db: AsyncSession = Depends(get_db)):
    mid = _parse_uuid(match_id, "match_id")
    match = await crud.get_match(db, mid)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.status != "open":
        raise HTTPException(status_code=400, detail=f"Match not open (status: {match.status})")
    if len(match.participants) >= match.max_agents:
        raise HTTPException(status_code=400, detail="Match is full")

    aid = _parse_uuid(body.agent_id, "agent_id")
    agent = await crud.get_agent(db, aid)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Prevent banned users from joining
    if agent.owner and agent.owner.is_banned:
        raise HTTPException(status_code=403, detail="Account is banned")

    try:
        participant = await crud.join_match(db, match, agent, tx_hash=body.tx_hash)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    logger.info("Agent %s joined match %s (slot %d)", agent.name, match_id[:8], participant.slot)
    return {
        "match_id": match_id,
        "agent_id": body.agent_id,
        "agent_name": agent.name,
        "slot": participant.slot,
    }


# ── Start ──────────────────────────────────────────────────────────────────────

@router.post(
    "/{match_id}/start",
    dependencies=[Depends(rate_limit_write)],
)
async def start_match(match_id: str, db: AsyncSession = Depends(get_db)):
    mid = _parse_uuid(match_id, "match_id")
    match = await crud.get_match(db, mid)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.status != "open":
        raise HTTPException(status_code=400, detail=f"Match not open (status: {match.status})")
    if len(match.participants) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 agents")

    # Eager-load agent records
    agents = [p.agent for p in match.participants]

    await crud.set_match_status(db, mid, "starting")

    task = asyncio.create_task(
        _run_match_bg(match_id, agents, match.seed, match.map_size)
    )
    _running_tasks[match_id] = task

    logger.info("Match %s starting with %d agents", match_id[:8], len(agents))
    return {"match_id": match_id, "status": "starting", "agent_count": len(agents)}


# ── Live state (poll) ──────────────────────────────────────────────────────────

@router.get(
    "/{match_id}/state", response_model=MatchStateResponse,
    dependencies=[Depends(rate_limit_global)],
)
async def get_state(match_id: str, db: AsyncSession = Depends(get_db)):
    mid = _parse_uuid(match_id, "match_id")
    match = await crud.get_match(db, mid)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    # Try in-memory cache first (fastest for active matches)
    cached = store._matches.get(match_id)
    live = cached.live_state if cached else None

    if not live:
        # Fall back to latest tick in DB
        snap = await crud.get_latest_tick(db, mid)
        if snap:
            live = {
                "tick": snap.tick,
                "alive_count": snap.alive_count,
                "zone": snap.zone,
                "agents": list(snap.agent_states.values()) if isinstance(snap.agent_states, dict) else [],
                "recent_events": snap.events,
            }

    live = live or {}
    return MatchStateResponse(
        match_id=match_id,
        status=match.status,
        tick=live.get("tick", 0),
        alive_count=live.get("alive_count", len(match.participants)),
        total_agents=len(match.participants),
        zone=live.get("zone", {}),
        agents=live.get("agents", []),
        recent_events=live.get("recent_events", []),
    )


# ── Tick replay ────────────────────────────────────────────────────────────────

@router.get(
    "/{match_id}/ticks/{tick}", response_model=TickResponse,
    dependencies=[Depends(rate_limit_global)],
)
async def get_tick(match_id: str, tick: int, db: AsyncSession = Depends(get_db)):
    mid = _parse_uuid(match_id, "match_id")
    if tick < 0 or tick > 2000:
        raise HTTPException(status_code=400, detail="Tick out of range (0-2000)")
    snap = await crud.get_tick(db, mid, tick)
    if not snap:
        raise HTTPException(status_code=404, detail=f"Tick {tick} not found")
    return TickResponse(
        tick=snap.tick,
        alive_count=snap.alive_count,
        zone=snap.zone,
        agent_states=snap.agent_states,
        actions=snap.actions,
        events=snap.events,
    )


# ── Result ─────────────────────────────────────────────────────────────────────

@router.get(
    "/{match_id}/result", response_model=MatchResultResponse,
    dependencies=[Depends(rate_limit_global)],
)
async def get_result(match_id: str, db: AsyncSession = Depends(get_db)):
    mid = _parse_uuid(match_id, "match_id")
    match = await crud.get_match(db, mid)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.status != "finished":
        raise HTTPException(status_code=400, detail=f"Match not finished (status: {match.status})")

    # Build rankings from participants
    rankings = sorted(
        [
            {
                "place": p.place,
                "agent_id": str(p.agent_id),
                "agent_name": p.agent.name,
                "slot": p.slot,
            }
            for p in match.participants
        ],
        key=lambda r: r["place"] or 9999,
    )

    winner_name = None
    if match.winner_agent_id:
        winner_p = next((p for p in match.participants if p.agent_id == match.winner_agent_id), None)
        winner_name = winner_p.agent.name if winner_p else None

    return MatchResultResponse(
        match_id=match_id,
        winner_id=str(match.winner_agent_id) if match.winner_agent_id else None,
        winner_name=winner_name,
        total_ticks=match.total_ticks,
        rankings=rankings,
    )


# ── Internal helpers ───────────────────────────────────────────────────────────

async def _run_match_bg(match_id: str, agents, seed: int, map_size: int):
    """Background task — owns its own DB session."""
    try:
        runner = NetworkMatchRunner(
            match_id=match_id,
            agent_records=agents,
            seed=seed,
            map_size=map_size,
        )
        await runner.run()
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"[Match {match_id[:8]}] crashed: {e}", exc_info=True)
        async with AsyncSessionLocal() as db:
            await crud.set_match_status(db, uuid.UUID(match_id), "cancelled")
            await db.commit()
    finally:
        _running_tasks.pop(match_id, None)


def _fmt_match(match) -> MatchResponse:
    participants = [
        ParticipantResponse(
            agent_id=str(p.agent_id),
            agent_name=p.agent.name if p.agent else "?",
            slot=p.slot,
            place=p.place,
            joined_at=p.joined_at,
        )
        for p in (match.participants or [])
    ]
    return MatchResponse(
        match_id=str(match.id),
        status=match.status,
        max_agents=match.max_agents,
        map_size=match.map_size,
        seed=match.seed,
        agent_count=len(match.participants or []),
        participants=participants,
        winner_agent_id=str(match.winner_agent_id) if match.winner_agent_id else None,
        total_ticks=match.total_ticks,
        created_at=match.created_at,
        started_at=match.started_at,
        finished_at=match.finished_at,
    )
