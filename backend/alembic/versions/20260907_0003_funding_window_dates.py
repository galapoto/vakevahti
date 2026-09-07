"""Preserve date-only funding window facts.

Revision ID: 20260907_0003
Revises: 20260830_0002
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260907_0003"
down_revision: str | None = "20260830_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "funding_calls",
        sa.Column("application_opens_on", sa.Date(), nullable=True),
    )
    op.add_column(
        "funding_calls",
        sa.Column("application_deadline_on", sa.Date(), nullable=True),
    )

    # Existing exact timestamps were parsed from Finnish source-local times. Preserve
    # their known local calendar date without changing the exact timestamp itself.
    op.execute(
        """
        UPDATE funding_calls
        SET application_opens_on =
            (application_opens_at AT TIME ZONE 'Europe/Helsinki')::date
        WHERE application_opens_at IS NOT NULL
          AND application_opens_on IS NULL
        """
    )
    op.execute(
        """
        UPDATE funding_calls
        SET application_deadline_on =
            (application_deadline_at AT TIME ZONE 'Europe/Helsinki')::date
        WHERE application_deadline_at IS NOT NULL
          AND application_deadline_on IS NULL
        """
    )

    op.create_index(
        "ix_funding_calls_source_snapshot_relevance",
        "funding_calls",
        ["source_code", "last_seen_at", "relevance_status"],
        unique=False,
    )
    op.create_index(
        "ix_funding_calls_deadline_on",
        "funding_calls",
        ["application_deadline_on"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_funding_calls_deadline_on", table_name="funding_calls")
    op.drop_index(
        "ix_funding_calls_source_snapshot_relevance",
        table_name="funding_calls",
    )
    op.drop_column("funding_calls", "application_deadline_on")
    op.drop_column("funding_calls", "application_opens_on")
