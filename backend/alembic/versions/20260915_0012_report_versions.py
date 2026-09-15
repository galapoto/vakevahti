"""Add explicit immutable funding report version lineage.

Revision ID: 20260915_0012
Revises: 20260915_0011
Create Date: 2026-09-15
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260915_0012"
down_revision: str | None = "20260915_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "funding_reports",
        sa.Column("version_number", sa.Integer(), server_default="1", nullable=False),
    )
    op.add_column(
        "funding_reports",
        sa.Column("supersedes_report_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_funding_reports_supersedes_report_id",
        "funding_reports",
        "funding_reports",
        ["supersedes_report_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_unique_constraint(
        "uq_funding_reports_supersedes_report_id",
        "funding_reports",
        ["supersedes_report_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_funding_reports_supersedes_report_id",
        "funding_reports",
        type_="unique",
    )
    op.drop_constraint(
        "fk_funding_reports_supersedes_report_id",
        "funding_reports",
        type_="foreignkey",
    )
    op.drop_column("funding_reports", "supersedes_report_id")
    op.drop_column("funding_reports", "version_number")
