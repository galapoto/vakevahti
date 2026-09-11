"""Add automated report composition and editable email fields.

Revision ID: 20260911_0007
Revises: 20260911_0006
Create Date: 2026-09-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260911_0007"
down_revision: str | None = "20260911_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "funding_reports",
        sa.Column(
            "origin",
            sa.String(length=32),
            nullable=False,
            server_default="MANUAL",
        ),
    )
    op.add_column(
        "funding_reports",
        sa.Column("automation_key", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "funding_reports",
        sa.Column("email_subject", sa.Text(), nullable=True),
    )
    op.add_column(
        "funding_reports",
        sa.Column("email_body", sa.Text(), nullable=True),
    )
    op.add_column(
        "funding_reports",
        sa.Column(
            "recipient_emails",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.create_unique_constraint(
        "uq_funding_reports_automation_key",
        "funding_reports",
        ["automation_key"],
    )
    op.alter_column("funding_reports", "origin", server_default=None)
    op.alter_column("funding_reports", "recipient_emails", server_default=None)


def downgrade() -> None:
    op.drop_constraint(
        "uq_funding_reports_automation_key",
        "funding_reports",
        type_="unique",
    )
    op.drop_column("funding_reports", "recipient_emails")
    op.drop_column("funding_reports", "email_body")
    op.drop_column("funding_reports", "email_subject")
    op.drop_column("funding_reports", "automation_key")
    op.drop_column("funding_reports", "origin")
