"""
Admin / operator endpoints — protected by OPERATOR_API_KEY.
Emergency pause, match cancellation, circuit breaker status.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_db
from backend.security import (
    require_operator_key, circuit_breaker,
    is_paused, set_paused,
)
from backend import crud

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_operator_key)])


@router.post("/pause")
async def pause_system():
    """Emergency pause — blocks all POST requests except admin endpoints."""
    set_paused(True)
    logger.warning("SYSTEM PAUSED by operator")
    return {"paused": True}


@router.post("/resume")
async def resume_system():
    """Resume after emergency pause."""
    set_paused(False)
    logger.warning("SYSTEM RESUMED by operator")
    return {"paused": False}


@router.get("/status")
async def system_status(db: AsyncSession = Depends(get_db)):
    """Operator dashboard: pause state, circuit breaker, active matches."""
    active = await crud.active_match_count(db)
    return {
        "paused": is_paused(),
        "active_matches": active,
        "circuit_breakers": circuit_breaker.status(),
    }


@router.post("/matches/{match_id}/cancel")
async def cancel_match(match_id: str, db: AsyncSession = Depends(get_db)):
    """Force-cancel a match (operator emergency action)."""
    import uuid
    match = await crud.get_match(db, uuid.UUID(match_id))
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.status == "finished":
        raise HTTPException(status_code=400, detail="Cannot cancel a finished match")
    await crud.set_match_status(db, uuid.UUID(match_id), "cancelled")
    logger.warning("Match %s force-cancelled by operator", match_id[:8])
    return {"match_id": match_id, "status": "cancelled"}
