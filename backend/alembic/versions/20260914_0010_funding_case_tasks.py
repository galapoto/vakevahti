"""Add automatically maintained funding case workflow tasks.

Revision ID: 20260914_0010
Revises: 20260914_0009
Create Date: 2026-09-14
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260914_0010"
down_revision: str | None = "20260914_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "funding_case_tasks",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("task_key", sa.String(length=64), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("due_on", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["case_id"],
            ["funding_cases.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_id", "task_key", name="uq_funding_case_task_key"),
    )
    op.create_index(
        "ix_funding_case_tasks_case_status_due",
        "funding_case_tasks",
        ["case_id", "status", "due_on"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_funding_case_tasks_case_status_due",
        table_name="funding_case_tasks",
    )
    op.drop_table("funding_case_tasks")
