"""Add operational source scan audit table.

Revision ID: 20260830_0002
Revises: 20260827_0001
Create Date: 2026-08-30
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260830_0002"
down_revision: str | None = "20260827_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "source_scan_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_code", sa.String(length=32), nullable=False),
        sa.Column("trigger_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("baseline", sa.Boolean(), nullable=True),
        sa.Column("discovered_count", sa.Integer(), nullable=True),
        sa.Column("new_count", sa.Integer(), nullable=True),
        sa.Column("unchanged_count", sa.Integer(), nullable=True),
        sa.Column("changed_count", sa.Integer(), nullable=True),
        sa.Column("error_type", sa.String(length=255), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_source_scan_runs_source_started",
        "source_scan_runs",
        ["source_code", "started_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_source_scan_runs_source_started",
        table_name="source_scan_runs",
    )
    op.drop_table("source_scan_runs")
