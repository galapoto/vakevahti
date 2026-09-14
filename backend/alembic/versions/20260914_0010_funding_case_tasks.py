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


def _backfill_task(
    *,
    task_key: str,
    title: str,
    detail: str,
    completed_sql: str,
) -> None:
    op.execute(
        sa.text(
            f"""
            INSERT INTO funding_case_tasks (
                case_id,
                task_key,
                title,
                detail,
                status,
                due_on,
                created_at,
                updated_at,
                completed_at
            )
            SELECT
                c.id,
                :task_key,
                :title,
                :detail,
                CASE WHEN {completed_sql} THEN 'COMPLETED' ELSE 'OPEN' END,
                COALESCE(f.application_deadline_on, f.application_deadline_at::date),
                c.created_at,
                c.updated_at,
                CASE WHEN {completed_sql} THEN c.updated_at ELSE NULL END
            FROM funding_cases AS c
            JOIN funding_calls AS f ON f.id = c.funding_call_id
            WHERE c.status = 'OPEN'
            ON CONFLICT (case_id, task_key) DO NOTHING
            """
        ).bindparams(task_key=task_key, title=title, detail=detail)
    )


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

    _backfill_task(
        task_key="ELIGIBILITY_REVIEW",
        title="Varmista hakukelpoisuus",
        detail="Tarkista VakeHyvän hakukelpoisuus ja rahoitushaun rajaukset.",
        completed_sql="f.relevance_status = 'RELEVANT'",
    )
    _backfill_task(
        task_key="PROCESS_DESCRIPTION",
        title="Valmistele prosessikuvaus",
        detail="Liitä tai hyväksy caselle valmistelun prosessikuvaus.",
        completed_sql=(
            "EXISTS (SELECT 1 FROM funding_case_artifacts a "
            "WHERE a.case_id = c.id AND a.artifact_type = 'PROCESS_DESCRIPTION' "
            "AND a.status = 'APPROVED')"
        ),
    )
    _backfill_task(
        task_key="REPORTING_PLAN",
        title="Valmistele raportointisuunnitelma",
        detail="Liitä tai hyväksy caselle rahoituksen raportointisuunnitelma.",
        completed_sql=(
            "EXISTS (SELECT 1 FROM funding_case_artifacts a "
            "WHERE a.case_id = c.id AND a.artifact_type = 'REPORTING' "
            "AND a.status = 'APPROVED')"
        ),
    )
    _backfill_task(
        task_key="FUNDING_REPORT_REVIEW",
        title="Tarkista rahoitusraportti ja sähköpostipaketti",
        detail="Tarkista rahoitusraportti, vastaanottajat ja mukaan valitut aineistot.",
        completed_sql=(
            "EXISTS (SELECT 1 FROM funding_case_artifacts a "
            "WHERE a.case_id = c.id AND a.artifact_type = 'FUNDING_REPORT' "
            "AND a.status = 'APPROVED')"
        ),
    )


def downgrade() -> None:
    op.drop_index(
        "ix_funding_case_tasks_case_status_due",
        table_name="funding_case_tasks",
    )
    op.drop_table("funding_case_tasks")
