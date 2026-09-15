"""Add immutable funding report approval decision events.

Revision ID: 20260915_0011
Revises: 20260914_0010
Create Date: 2026-09-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260915_0011"
down_revision: str | None = "20260914_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "funding_report_approval_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("report_id", sa.Uuid(), nullable=False),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("actor_id", sa.String(length=255), nullable=False),
        sa.Column("actor_display_name", sa.String(length=255), nullable=True),
        sa.Column("actor_source", sa.String(length=32), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["report_id"],
            ["funding_reports.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_funding_report_approval_events_report_decided",
        "funding_report_approval_events",
        ["report_id", "decided_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_funding_report_approval_events_report_decided",
        table_name="funding_report_approval_events",
    )
    op.drop_table("funding_report_approval_events")
