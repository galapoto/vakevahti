"""Add versioned structured funding case requirements.

Revision ID: 20260914_0011
Revises: 20260914_0010
Create Date: 2026-09-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260914_0011"
down_revision: str | None = "20260914_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "funding_case_requirements",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("funding_call_version", sa.Integer(), nullable=False),
        sa.Column("requirement_key", sa.String(length=64), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("certainty", sa.String(length=32), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column(
            "evidence",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["case_id"],
            ["funding_cases.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "case_id",
            "funding_call_version",
            "requirement_key",
            name="uq_funding_case_requirement_version_key",
        ),
    )
    op.create_index(
        "ix_funding_case_requirements_case_version",
        "funding_case_requirements",
        ["case_id", "funding_call_version"],
        unique=False,
    )
    op.create_index(
        "ix_funding_case_requirements_certainty",
        "funding_case_requirements",
        ["certainty", "category"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_funding_case_requirements_certainty",
        table_name="funding_case_requirements",
    )
    op.drop_index(
        "ix_funding_case_requirements_case_version",
        table_name="funding_case_requirements",
    )
    op.drop_table("funding_case_requirements")
