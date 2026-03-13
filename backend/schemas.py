"""All Pydantic models for request/response validation."""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from engine.actions import VALID_ACTIONS


# ── Auth / Wallet ──────────────────────────────────────────────────────────────

class WalletNonceRequest(BaseModel):
    wallet_address: str = Field(..., pattern=r"^0x[0-9a-fA-F]{40}$")


class WalletNonceResponse(BaseModel):
    wallet_address: str
    nonce: str
    message: str   # SIWE-style message to sign


class WalletVerifyRequest(BaseModel):
    wallet_address: str
    signature: str


class WalletSessionResponse(BaseModel):
    wallet_address: str
    user_id: str
    token: str             # JWT (stub — implement signing in production)
    twitter_linked: bool
    follower_count: int


class TwitterLinkRequest(BaseModel):
    wallet_address: str = Field(..., pattern=r"^0x[0-9a-fA-F]{40}$")
    twitter_handle: str = Field(..., min_length=1, max_length=64, pattern=r"^@?[\w]+$")
    twitter_user_id: str = Field(..., min_length=1, max_length=32, pattern=r"^\d+$")
    follower_count: int = Field(..., ge=0, le=999_999_999)
    verified: bool = False


# ── Agent ──────────────────────────────────────────────────────────────────────

class AgentRegisterRequest(BaseModel):
    wallet_address: str = Field(..., pattern=r"^0x[0-9a-fA-F]{40}$")
    name: str = Field(..., min_length=1, max_length=64, pattern=r"^[\w\s\-\.]+$")
    endpoint_url: str = Field(..., max_length=512)
    description: Optional[str] = Field(None, max_length=256)

    @field_validator("endpoint_url")
    @classmethod
    def must_be_http(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("endpoint_url must start with http:// or https://")
        if len(v) < 10:
            raise ValueError("endpoint_url too short")
        return v.rstrip("/")


class AgentResponse(BaseModel):
    agent_id: str
    name: str
    endpoint_url: str
    owner_wallet: str
    description: Optional[str]
    wins: int
    losses: int
    games: int
    win_rate: float
    created_at: datetime


# ── Match ──────────────────────────────────────────────────────────────────────

class MatchCreateRequest(BaseModel):
    max_agents: int = Field(default=100, ge=2, le=100)
    map_size: int = Field(default=50, ge=10, le=100)
    seed: Optional[int] = Field(None, ge=0, le=2**31 - 1)


class MatchJoinRequest(BaseModel):
    agent_id: str = Field(..., min_length=36, max_length=36)
    tx_hash: Optional[str] = Field(None, max_length=66, pattern=r"^(0x[0-9a-fA-F]{64})?$")


class ParticipantResponse(BaseModel):
    agent_id: str
    agent_name: str
    slot: int
    place: Optional[int]
    joined_at: datetime


class MatchResponse(BaseModel):
    match_id: str
    status: str
    max_agents: int
    map_size: int
    seed: int
    agent_count: int
    participants: list[ParticipantResponse]
    winner_agent_id: Optional[str]
    total_ticks: int
    created_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]


class MatchListItem(BaseModel):
    match_id: str
    status: str
    max_agents: int
    agent_count: int
    created_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]


# ── Live state (polled) ────────────────────────────────────────────────────────

class MatchStateResponse(BaseModel):
    match_id: str
    status: str
    tick: int
    alive_count: int
    total_agents: int
    zone: dict
    agents: list[dict]
    recent_events: list[str]


class MatchResultResponse(BaseModel):
    match_id: str
    winner_id: Optional[str]
    winner_name: Optional[str]
    total_ticks: int
    rankings: list[dict]


# ── Tick replay ────────────────────────────────────────────────────────────────

class TickResponse(BaseModel):
    tick: int
    alive_count: int
    zone: dict
    agent_states: dict
    actions: dict
    events: list[str]


# ── Leaderboard ────────────────────────────────────────────────────────────────

class LeaderboardEntry(BaseModel):
    rank: int
    agent_id: str
    name: str
    wins: int
    losses: int
    games: int
    win_rate: float
    owner_wallet: str
    twitter: Optional[str]


# ── Agent protocol ─────────────────────────────────────────────────────────────

class ActionPayload(BaseModel):
    action: str

    @field_validator("action")
    @classmethod
    def must_be_valid(cls, v: str) -> str:
        if v not in VALID_ACTIONS:
            raise ValueError(f"Invalid action '{v}'. Must be one of: {sorted(VALID_ACTIONS)}")
        return v


# ── Health ─────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
    active_matches: int
    db: str = "ok"
