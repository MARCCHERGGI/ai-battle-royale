from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_db
from backend.schemas import LeaderboardEntry
from backend import crud

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("", response_model=list[LeaderboardEntry])
async def get_leaderboard(
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Global leaderboard ranked by wins, then losses (ascending), then games played."""
    rows = await crud.get_leaderboard(db, limit=limit)
    return [LeaderboardEntry(**r) for r in rows]
