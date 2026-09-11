"""Add persisted funding report drafts and report items.

Revision ID: 20260911_0006
Revises: 20260911_0005
Create Date: 2026-09-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260911_0006"
down_revision: str | None = "20260911_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "funding_reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_for_approval_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_funding_reports_status_updated",
        "funding_reports",
        ["status", "updated_at"],
        unique=False,
    )

    op.create_table(
        "funding_report_items",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("report_id", sa.Uuid(), nullable=False),
        sa.Column("funding_call_id", sa.BigInteger(), nullable=False),
        sa.Column("funding_call_version", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["funding_call_id"],
            ["funding_calls.id"],
        ),
        sa.ForeignKeyConstraint(
            ["report_id"],
            ["funding_reports.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "report_id",
            "funding_call_id",
            name="uq_funding_report_items_report_call",
        ),
        sa.UniqueConstraint(
            "report_id",
            "position",
            name="uq_funding_report_items_report_position",
        ),
    )
    op.create_index(
        "ix_funding_report_items_report_position",
        "funding_report_items",
        ["report_id", "position"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_funding_report_items_report_position",
        table_name="funding_report_items",
    )
    op.drop_table("funding_report_items")
    op.drop_index("ix_funding_reports_status_updated", table_name="funding_reports")
    op.drop_table("funding_reports")
