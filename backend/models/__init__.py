"""
SQLAlchemy ORM models — all tables in one place for easy Alembic detection.
"""
from __future__ import annotations
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger, Boolean, DateTime, ForeignKey,
    Integer, Numeric, String, Text, func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db import Base


# ── Users (wallet-based) ───────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_address: Mapped[str] = mapped_column(String(42), unique=True, nullable=False, index=True)
    nonce: Mapped[str | None] = mapped_column(String(64), nullable=True)          # SIWE challenge nonce
    twitter_handle: Mapped[str | None] = mapped_column(String(64), nullable=True)
    twitter_user_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    follower_count: Mapped[int] = mapped_column(Integer, default=0)
    twitter_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    agents: Mapped[list["Agent"]] = relationship("Agent", back_populates="owner", cascade="all, delete-orphan")


# ── Agents ─────────────────────────────────────────────────────────────────────

class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    endpoint_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # API-key auth (Moltbook-style registration)
    api_key: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)
    verification_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    x_handle: Mapped[str | None] = mapped_column(String(64), nullable=True)
    x_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    owner: Mapped["User"] = relationship("User", back_populates="agents")
    participations: Mapped[list["MatchParticipant"]] = relationship("MatchParticipant", back_populates="agent")
    eliminations: Mapped[list["Elimination"]] = relationship("Elimination", back_populates="agent")
    payouts: Mapped[list["Payout"]] = relationship("Payout", back_populates="winner_agent")


# ── Matches ────────────────────────────────────────────────────────────────────

class Match(Base):
    __tablename__ = "matches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chain_match_id: Mapped[int | None] = mapped_column(Integer, nullable=True, unique=True)
    status: Mapped[str] = mapped_column(String(16), default="open", nullable=False, index=True)
    # open | starting | active | finished | cancelled
    seed: Mapped[int] = mapped_column(BigInteger, nullable=False)
    map_size: Mapped[int] = mapped_column(Integer, default=50)
    max_agents: Mapped[int] = mapped_column(Integer, default=100)
    winner_agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=True)
    total_ticks: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    participants: Mapped[list["MatchParticipant"]] = relationship("MatchParticipant", back_populates="match", cascade="all, delete-orphan")
    ticks: Mapped[list["TickSnapshot"]] = relationship("TickSnapshot", back_populates="match", cascade="all, delete-orphan")
    eliminations: Mapped[list["Elimination"]] = relationship("Elimination", back_populates="match", cascade="all, delete-orphan")
    payout: Mapped["Payout | None"] = relationship("Payout", back_populates="match", uselist=False)


# ── Match Participants ─────────────────────────────────────────────────────────

class MatchParticipant(Base):
    __tablename__ = "match_participants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False, index=True)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False, index=True)
    slot: Mapped[int] = mapped_column(Integer, nullable=False)           # 0-indexed join order
    place: Mapped[int | None] = mapped_column(Integer, nullable=True)    # 1 = winner
    tx_hash: Mapped[str | None] = mapped_column(String(66), nullable=True)  # on-chain entry tx
    joined_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    match: Mapped["Match"] = relationship("Match", back_populates="participants")
    agent: Mapped["Agent"] = relationship("Agent", back_populates="participations")


# ── Tick Snapshots ─────────────────────────────────────────────────────────────

class TickSnapshot(Base):
    """One row per game tick. Stores full state + all actions as JSONB."""
    __tablename__ = "tick_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    match_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False, index=True)
    tick: Mapped[int] = mapped_column(Integer, nullable=False)
    alive_count: Mapped[int] = mapped_column(Integer, nullable=False)
    zone: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # {agent_id: {x, y, hp, energy, alive, ...}}
    agent_states: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # {agent_id: "MOVE_RIGHT"}
    actions: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # ["AgentX eliminated by zone", ...]
    events: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    match: Mapped["Match"] = relationship("Match", back_populates="ticks")


# ── Eliminations ───────────────────────────────────────────────────────────────

class Elimination(Base):
    __tablename__ = "eliminations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False, index=True)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False, index=True)
    tick: Mapped[int] = mapped_column(Integer, nullable=False)
    cause: Mapped[str] = mapped_column(String(32), nullable=False)   # zone | combat | strikes
    place: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    match: Mapped["Match"] = relationship("Match", back_populates="eliminations")
    agent: Mapped["Agent"] = relationship("Agent", back_populates="eliminations")


# ── Payouts ────────────────────────────────────────────────────────────────────

class Payout(Base):
    __tablename__ = "payouts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False, unique=True)
    winner_agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    winner_wallet: Mapped[str] = mapped_column(String(42), nullable=False)
    amount_usdc: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    tx_hash: Mapped[str | None] = mapped_column(String(66), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending | paid | failed
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    match: Mapped["Match"] = relationship("Match", back_populates="payout")
    winner_agent: Mapped["Agent"] = relationship("Agent", back_populates="payouts")
