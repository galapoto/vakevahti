"""Add lease-based notification outbox claiming.

Revision ID: 20260911_0005
Revises: 20260911_0004
Create Date: 2026-09-11
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260911_0005"
down_revision: str | None = "20260911_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "notification_outbox",
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "notification_outbox",
        sa.Column("claim_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "notification_outbox",
        sa.Column("claim_token", sa.Uuid(), nullable=True),
    )
    op.create_index(
        "ix_notification_outbox_status_claim_expiry",
        "notification_outbox",
        ["status", "claim_expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_notification_outbox_status_claim_expiry",
        table_name="notification_outbox",
    )
    op.drop_column("notification_outbox", "claim_token")
    op.drop_column("notification_outbox", "claim_expires_at")
    op.drop_column("notification_outbox", "claimed_at")
