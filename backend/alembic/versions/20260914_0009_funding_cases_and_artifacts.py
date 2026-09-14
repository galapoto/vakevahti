"""Add stable funding cases and versioned cross-app artifacts.

Revision ID: 20260914_0009
Revises: 20260911_0008
Create Date: 2026-09-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260914_0009"
down_revision: str | None = "20260911_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "funding_cases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("funding_call_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["funding_call_id"],
            ["funding_calls.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("funding_call_id", name="uq_funding_cases_funding_call"),
    )
    op.create_index(
        "ix_funding_cases_status_updated",
        "funding_cases",
        ["status", "updated_at"],
        unique=False,
    )

    # Backfill existing employee-visible opportunities with stable IDs. PostgreSQL's
    # built-in md5 is used only as a deterministic identifier transform, not for security.
    op.execute(
        """
        INSERT INTO funding_cases (id, funding_call_id, status, created_at, updated_at)
        SELECT
            md5('vakevahti-case:' || source_code || ':' || external_key)::uuid,
            id,
            'OPEN',
            first_seen_at,
            last_seen_at
        FROM funding_calls
        WHERE relevance_status IN ('RELEVANT', 'NEEDS_REVIEW')
        ON CONFLICT (funding_call_id) DO NOTHING
        """
    )

    op.create_table(
        "funding_case_artifacts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("source_app", sa.String(length=64), nullable=False),
        sa.Column("artifact_type", sa.String(length=64), nullable=False),
        sa.Column("external_artifact_id", sa.String(length=256), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("content_url", sa.Text(), nullable=True),
        sa.Column("content_text", sa.Text(), nullable=True),
        sa.Column("mime_type", sa.String(length=128), nullable=True),
        sa.Column("checksum", sa.String(length=64), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["case_id"],
            ["funding_cases.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "case_id",
            "source_app",
            "artifact_type",
            "external_artifact_id",
            "version",
            name="uq_funding_case_artifact_version",
        ),
    )
    op.create_index(
        "ix_funding_case_artifacts_case_type_status",
        "funding_case_artifacts",
        ["case_id", "artifact_type", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_funding_case_artifacts_case_type_status",
        table_name="funding_case_artifacts",
    )
    op.drop_table("funding_case_artifacts")
    op.drop_index("ix_funding_cases_status_updated", table_name="funding_cases")
    op.drop_table("funding_cases")
