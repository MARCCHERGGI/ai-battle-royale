"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-12
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("wallet_address", sa.String(42), nullable=False, unique=True),
        sa.Column("nonce", sa.String(64), nullable=True),
        sa.Column("twitter_handle", sa.String(64), nullable=True),
        sa.Column("twitter_user_id", sa.String(32), nullable=True),
        sa.Column("follower_count", sa.Integer, server_default="0"),
        sa.Column("twitter_verified", sa.Boolean, server_default="false"),
        sa.Column("is_banned", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_users_wallet_address", "users", ["wallet_address"])

    op.create_table(
        "agents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("endpoint_url", sa.Text, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("wins", sa.Integer, server_default="0"),
        sa.Column("losses", sa.Integer, server_default="0"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_agents_owner_id", "agents", ["owner_id"])

    op.create_table(
        "matches",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("chain_match_id", sa.Integer, nullable=True, unique=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="open"),
        sa.Column("seed", sa.BigInteger, nullable=False),
        sa.Column("map_size", sa.Integer, server_default="50"),
        sa.Column("max_agents", sa.Integer, server_default="100"),
        sa.Column("winner_agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=True),
        sa.Column("total_ticks", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime, nullable=True),
        sa.Column("finished_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_matches_status", "matches", ["status"])

    op.create_table(
        "match_participants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("match_id", UUID(as_uuid=True), sa.ForeignKey("matches.id"), nullable=False),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("slot", sa.Integer, nullable=False),
        sa.Column("place", sa.Integer, nullable=True),
        sa.Column("tx_hash", sa.String(66), nullable=True),
        sa.Column("joined_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_match_participants_match_id", "match_participants", ["match_id"])
    op.create_index("ix_match_participants_agent_id", "match_participants", ["agent_id"])

    op.create_table(
        "tick_snapshots",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("match_id", UUID(as_uuid=True), sa.ForeignKey("matches.id"), nullable=False),
        sa.Column("tick", sa.Integer, nullable=False),
        sa.Column("alive_count", sa.Integer, nullable=False),
        sa.Column("zone", JSONB, nullable=False),
        sa.Column("agent_states", JSONB, nullable=False),
        sa.Column("actions", JSONB, nullable=False, server_default="'{}'"),
        sa.Column("events", JSONB, nullable=False, server_default="'[]'"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_tick_snapshots_match_id", "tick_snapshots", ["match_id"])
    op.create_index("ix_tick_snapshots_match_tick", "tick_snapshots", ["match_id", "tick"])

    op.create_table(
        "eliminations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("match_id", UUID(as_uuid=True), sa.ForeignKey("matches.id"), nullable=False),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("tick", sa.Integer, nullable=False),
        sa.Column("cause", sa.String(32), nullable=False),
        sa.Column("place", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_eliminations_match_id", "eliminations", ["match_id"])
    op.create_index("ix_eliminations_agent_id", "eliminations", ["agent_id"])

    op.create_table(
        "payouts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("match_id", UUID(as_uuid=True), sa.ForeignKey("matches.id"), nullable=False, unique=True),
        sa.Column("winner_agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("winner_wallet", sa.String(42), nullable=False),
        sa.Column("amount_usdc", sa.Numeric(18, 6), nullable=False),
        sa.Column("tx_hash", sa.String(66), nullable=True),
        sa.Column("status", sa.String(16), server_default="'pending'"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("paid_at", sa.DateTime, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("payouts")
    op.drop_table("eliminations")
    op.drop_table("tick_snapshots")
    op.drop_table("match_participants")
    op.drop_table("matches")
    op.drop_table("agents")
    op.drop_table("users")
