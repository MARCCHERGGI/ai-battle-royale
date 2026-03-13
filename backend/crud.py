"""
Database operations (CRUD).
All functions take an AsyncSession and return ORM objects.
"""
from __future__ import annotations
import secrets
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func, update, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models import User, Agent, Match, MatchParticipant, TickSnapshot, Elimination, Payout


# ── Users ──────────────────────────────────────────────────────────────────────

async def get_or_create_user(db: AsyncSession, wallet: str) -> User:
    result = await db.execute(select(User).where(User.wallet_address == wallet.lower()))
    user = result.scalar_one_or_none()
    if not user:
        user = User(wallet_address=wallet.lower(), nonce=secrets.token_hex(16))
        db.add(user)
        await db.flush()
    return user


async def get_user_by_wallet(db: AsyncSession, wallet: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.wallet_address == wallet.lower()))
    return result.scalar_one_or_none()


async def refresh_nonce(db: AsyncSession, user: User) -> str:
    user.nonce = secrets.token_hex(16)
    await db.flush()
    return user.nonce


async def update_user_twitter(
    db: AsyncSession, user: User,
    handle: str, twitter_user_id: str, follower_count: int, verified: bool,
) -> User:
    user.twitter_handle = handle
    user.twitter_user_id = twitter_user_id
    user.follower_count = follower_count
    user.twitter_verified = verified
    await db.flush()
    return user


# ── Agents ─────────────────────────────────────────────────────────────────────

async def create_agent(
    db: AsyncSession,
    owner_id: uuid.UUID,
    name: str,
    endpoint_url: str,
    description: Optional[str] = None,
) -> Agent:
    agent = Agent(owner_id=owner_id, name=name, endpoint_url=endpoint_url, description=description)
    db.add(agent)
    await db.flush()
    return agent


async def get_agent(db: AsyncSession, agent_id: uuid.UUID) -> Optional[Agent]:
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.is_active == True)
        .options(selectinload(Agent.owner))
    )
    return result.scalar_one_or_none()


async def list_agents(db: AsyncSession, limit: int = 100, offset: int = 0) -> list[Agent]:
    result = await db.execute(
        select(Agent).where(Agent.is_active == True)
        .options(selectinload(Agent.owner))
        .order_by(desc(Agent.wins), Agent.created_at)
        .limit(limit).offset(offset)
    )
    return list(result.scalars().all())


async def increment_agent_wins(db: AsyncSession, agent_id: uuid.UUID) -> None:
    await db.execute(update(Agent).where(Agent.id == agent_id).values(wins=Agent.wins + 1))


async def increment_agent_losses(db: AsyncSession, agent_id: uuid.UUID) -> None:
    await db.execute(update(Agent).where(Agent.id == agent_id).values(losses=Agent.losses + 1))


# ── Matches ────────────────────────────────────────────────────────────────────

async def create_match(
    db: AsyncSession, seed: int, map_size: int, max_agents: int
) -> Match:
    match = Match(seed=seed, map_size=map_size, max_agents=max_agents)
    db.add(match)
    await db.flush()
    return match


async def get_match(db: AsyncSession, match_id: uuid.UUID) -> Optional[Match]:
    result = await db.execute(
        select(Match).where(Match.id == match_id)
        .options(selectinload(Match.participants).selectinload(MatchParticipant.agent))
    )
    return result.scalar_one_or_none()


async def list_matches(
    db: AsyncSession, status: Optional[str] = None, limit: int = 50, offset: int = 0
) -> list[Match]:
    q = select(Match).options(selectinload(Match.participants))
    if status:
        q = q.where(Match.status == status)
    q = q.order_by(desc(Match.created_at)).limit(limit).offset(offset)
    result = await db.execute(q)
    return list(result.scalars().all())


async def join_match(
    db: AsyncSession, match: Match, agent: Agent, tx_hash: Optional[str] = None
) -> MatchParticipant:
    # Guard: duplicate join
    result = await db.execute(
        select(MatchParticipant).where(
            MatchParticipant.match_id == match.id,
            MatchParticipant.agent_id == agent.id,
        )
    )
    if result.scalar_one_or_none():
        raise ValueError("Agent already in this match")

    slot = len(match.participants)
    participant = MatchParticipant(
        match_id=match.id,
        agent_id=agent.id,
        slot=slot,
        tx_hash=tx_hash,
    )
    db.add(participant)
    await db.flush()
    return participant


async def set_match_status(
    db: AsyncSession, match_id: uuid.UUID, status: str, **kwargs
) -> None:
    await db.execute(
        update(Match).where(Match.id == match_id).values(status=status, **kwargs)
    )


# ── Tick Snapshots ─────────────────────────────────────────────────────────────

async def save_tick(
    db: AsyncSession,
    match_id: uuid.UUID,
    tick: int,
    alive_count: int,
    zone: dict,
    agent_states: dict,
    actions: dict,
    events: list[str],
) -> TickSnapshot:
    snapshot = TickSnapshot(
        match_id=match_id,
        tick=tick,
        alive_count=alive_count,
        zone=zone,
        agent_states=agent_states,
        actions=actions,
        events=events,
    )
    db.add(snapshot)
    await db.flush()
    return snapshot


async def get_tick(
    db: AsyncSession, match_id: uuid.UUID, tick: int
) -> Optional[TickSnapshot]:
    result = await db.execute(
        select(TickSnapshot).where(
            TickSnapshot.match_id == match_id,
            TickSnapshot.tick == tick,
        )
    )
    return result.scalar_one_or_none()


async def get_latest_tick(db: AsyncSession, match_id: uuid.UUID) -> Optional[TickSnapshot]:
    result = await db.execute(
        select(TickSnapshot)
        .where(TickSnapshot.match_id == match_id)
        .order_by(desc(TickSnapshot.tick))
        .limit(1)
    )
    return result.scalar_one_or_none()


# ── Eliminations ───────────────────────────────────────────────────────────────

async def save_elimination(
    db: AsyncSession,
    match_id: uuid.UUID,
    agent_id: uuid.UUID,
    tick: int,
    cause: str,
    place: int,
) -> Elimination:
    elim = Elimination(
        match_id=match_id,
        agent_id=agent_id,
        tick=tick,
        cause=cause,
        place=place,
    )
    db.add(elim)
    await db.flush()
    return elim


# ── Payouts ────────────────────────────────────────────────────────────────────

async def create_payout(
    db: AsyncSession,
    match_id: uuid.UUID,
    winner_agent_id: uuid.UUID,
    winner_wallet: str,
    amount_usdc: float,
) -> Payout:
    payout = Payout(
        match_id=match_id,
        winner_agent_id=winner_agent_id,
        winner_wallet=winner_wallet,
        amount_usdc=amount_usdc,
    )
    db.add(payout)
    await db.flush()
    return payout


# ── Leaderboard ────────────────────────────────────────────────────────────────

async def get_leaderboard(db: AsyncSession, limit: int = 50) -> list[dict]:
    """Ranked by wins desc, losses asc, games played desc."""
    result = await db.execute(
        select(
            Agent.id,
            Agent.name,
            Agent.wins,
            Agent.losses,
            (Agent.wins + Agent.losses).label("games"),
            User.wallet_address,
            User.twitter_handle,
        )
        .join(User, Agent.owner_id == User.id)
        .where(Agent.is_active == True)
        .order_by(desc(Agent.wins), Agent.losses, desc(Agent.wins + Agent.losses))
        .limit(limit)
    )
    rows = result.all()
    return [
        {
            "rank": i + 1,
            "agent_id": str(r.id),
            "name": r.name,
            "wins": r.wins,
            "losses": r.losses,
            "games": r.games,
            "win_rate": round(r.wins / r.games * 100, 1) if r.games > 0 else 0,
            "owner_wallet": r.wallet_address,
            "twitter": r.twitter_handle,
        }
        for i, r in enumerate(rows)
    ]


async def active_match_count(db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count()).select_from(Match).where(Match.status == "active")
    )
    return result.scalar_one()
