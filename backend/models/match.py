import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime,
    ForeignKey, Numeric, Text, Enum as SAEnum
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from backend.db import Base


class MatchStatus(str, enum.Enum):
    OPEN = "open"           # accepting entries
    STARTING = "starting"   # roster locked, waiting for chain confirmation
    ACTIVE = "active"       # game running
    FINISHED = "finished"   # winner determined
    CANCELLED = "cancelled"


class Match(Base):
    __tablename__ = "matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chain_match_id = Column(Integer, nullable=True, unique=True)  # on-chain match ID
    status = Column(SAEnum(MatchStatus), default=MatchStatus.OPEN, nullable=False)
    seed = Column(String(66), nullable=True)  # deterministic random seed (bytes32 hex)
    winner_wallet = Column(String(42), nullable=True)
    prize_pool_usdc = Column(Numeric(18, 6), default=0)
    max_agents = Column(Integer, default=100)
    tick_count = Column(Integer, default=0)
    game_state = Column(JSONB, nullable=True)  # final snapshot for reference
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    entries = relationship("MatchEntry", back_populates="match", cascade="all, delete-orphan")


class Agent(Base):
    """A registered AI agent belonging to a wallet."""
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_wallet = Column(String(42), nullable=False, index=True)
    name = Column(String(64), nullable=False)
    endpoint_url = Column(Text, nullable=False)   # https://user-server.com/act
    description = Column(Text, nullable=True)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    entries = relationship("MatchEntry", back_populates="agent")


class MatchEntry(Base):
    """One agent's participation in one match."""
    __tablename__ = "match_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    owner_wallet = Column(String(42), nullable=False)
    tx_hash = Column(String(66), nullable=True)   # on-chain join tx
    entry_slot = Column(Integer, nullable=True)   # 0-indexed slot in match
    place = Column(Integer, nullable=True)        # final placement (1 = winner)
    eliminated_at_tick = Column(Integer, nullable=True)
    alive = Column(Boolean, default=True)
    strikes = Column(Integer, default=0)
    joined_at = Column(DateTime, default=datetime.utcnow)

    match = relationship("Match", back_populates="entries")
    agent = relationship("Agent", back_populates="entries")
