"""Create funding-call persistence tables.

Revision ID: 20260827_0001
Revises:
Create Date: 2026-08-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260827_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "source_states",
        sa.Column("source_code", sa.String(length=32), nullable=False),
        sa.Column("baseline_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_successful_scan_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("source_code"),
    )

    op.create_table(
        "funding_calls",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("source_code", sa.String(length=32), nullable=False),
        sa.Column("external_key", sa.String(length=256), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("application_opens_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("application_deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("description_text", sa.Text(), nullable=True),
        sa.Column("relevance_status", sa.String(length=32), nullable=False),
        sa.Column("relevance_reason", sa.Text(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("current_version", sa.Integer(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_code",
            "external_key",
            name="uq_funding_calls_source_external_key",
        ),
    )

    op.create_table(
        "funding_call_versions",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("funding_call_id", sa.BigInteger(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["funding_call_id"],
            ["funding_calls.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "funding_call_id",
            "version_number",
            name="uq_funding_call_versions_call_version",
        ),
    )


def downgrade() -> None:
    op.drop_table("funding_call_versions")
    op.drop_table("funding_calls")
    op.drop_table("source_states")
