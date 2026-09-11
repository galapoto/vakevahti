"""Add durable Funding notification outbox.

Revision ID: 20260911_0004
Revises: 20260907_0003
Create Date: 2026-09-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260911_0004"
down_revision: str | None = "20260907_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "notification_outbox",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("dedupe_key", sa.String(length=512), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("funding_call_id", sa.BigInteger(), nullable=False),
        sa.Column("funding_call_version", sa.Integer(), nullable=False),
        sa.Column("source_scan_run_id", sa.Uuid(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["funding_call_id"], ["funding_calls.id"]),
        sa.ForeignKeyConstraint(["source_scan_run_id"], ["source_scan_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dedupe_key", name="uq_notification_outbox_dedupe_key"),
    )
    op.create_index(
        "ix_notification_outbox_status_next_attempt",
        "notification_outbox",
        ["status", "next_attempt_at", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_notification_outbox_scan_run",
        "notification_outbox",
        ["source_scan_run_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_notification_outbox_scan_run", table_name="notification_outbox")
    op.drop_index(
        "ix_notification_outbox_status_next_attempt",
        table_name="notification_outbox",
    )
    op.drop_table("notification_outbox")
