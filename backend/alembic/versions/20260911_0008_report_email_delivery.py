"""Add durable funding-report email delivery queue.

Revision ID: 20260911_0008
Revises: 20260911_0007
Create Date: 2026-09-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260911_0008"
down_revision: str | None = "20260911_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "funding_report_deliveries",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("report_id", sa.Uuid(), nullable=False),
        sa.Column("dedupe_key", sa.String(length=256), nullable=False),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column(
            "recipient_emails",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("subject", sa.Text(), nullable=False),
        sa.Column("body_text", sa.Text(), nullable=False),
        sa.Column("body_html", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("claim_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("claim_token", sa.Uuid(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["report_id"],
            ["funding_reports.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "dedupe_key",
            name="uq_funding_report_deliveries_dedupe_key",
        ),
    )
    op.create_index(
        "ix_funding_report_deliveries_status_next_attempt",
        "funding_report_deliveries",
        ["status", "next_attempt_at", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_funding_report_deliveries_claim_expiry",
        "funding_report_deliveries",
        ["status", "claim_expires_at"],
        unique=False,
    )
    op.create_index(
        "ix_funding_report_deliveries_report",
        "funding_report_deliveries",
        ["report_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_funding_report_deliveries_report",
        table_name="funding_report_deliveries",
    )
    op.drop_index(
        "ix_funding_report_deliveries_claim_expiry",
        table_name="funding_report_deliveries",
    )
    op.drop_index(
        "ix_funding_report_deliveries_status_next_attempt",
        table_name="funding_report_deliveries",
    )
    op.drop_table("funding_report_deliveries")
