import os
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import HttpUrl
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.case_models import FundingCaseArtifact
from app.domain.funding_call import Evidence, FundingCallCandidate, RelevanceStatus
from app.services.case_sync import ensure_cases_for_source_snapshot
from app.services.persistence import persist_candidates

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not TEST_DATABASE_URL,
        reason="TEST_DATABASE_URL is required for starter draft integration tests.",
    ),
]

TRUNCATE_SQL = (
    "TRUNCATE TABLE funding_case_tasks, funding_case_artifacts, funding_cases, "
    "funding_report_deliveries, funding_report_items, funding_reports, "
    "notification_outbox, source_scan_runs, funding_call_versions, funding_calls, "
    "source_states RESTART IDENTITY CASCADE"
)


def _candidate(description: str) -> FundingCallCandidate:
    return FundingCallCandidate(
        external_key="starter-draft-2026",
        source_code="STM",
        title="Digitaalisten palvelujen kehittämishaku",
        source_url=HttpUrl("https://example.test/stm/starter-draft-2026"),
        application_deadline_on=datetime(2026, 12, 20, tzinfo=UTC).date(),
        description_text=description,
        relevance_status=RelevanceStatus.RELEVANT,
        relevance_reason="Haku tukee VakeHyvän digitaalisten palvelujen kehittämistä.",
        evidence=(
            Evidence(
                section="Hakijat",
                text="Hyvinvointialueet voivat hakea avustusta.",
                source_url=HttpUrl("https://example.test/stm/starter-draft-2026#hakijat"),
            ),
        ),
    )


async def test_case_sync_generates_idempotent_versioned_starter_drafts() -> None:
    assert TEST_DATABASE_URL is not None
    engine = create_async_engine(TEST_DATABASE_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    first_seen = datetime(2026, 9, 14, 10, 30, tzinfo=UTC)

    try:
        async with engine.begin() as connection:
            await connection.execute(text(TRUNCATE_SQL))

        async with session_factory() as session:
            async with session.begin():
                await persist_candidates(
                    session,
                    [_candidate("Ensimmäinen lähdekuvaus.")],
                    observed_at=first_seen,
                )
                await ensure_cases_for_source_snapshot(
                    session,
                    source_code="STM",
                    observed_at=first_seen,
                )

        async with session_factory() as session:
            rows = list(
                (
                    await session.scalars(
                        select(FundingCaseArtifact)
                        .where(FundingCaseArtifact.source_app == "VAKEVAHTI_AUTOMATION")
                        .order_by(FundingCaseArtifact.artifact_type.asc())
                    )
                ).all()
            )
            assert len(rows) == 2
            assert {row.artifact_type for row in rows} == {
                "PROCESS_DESCRIPTION",
                "REPORTING",
            }
            assert {row.version for row in rows} == {1}
            assert {row.status for row in rows} == {"DRAFT"}
            assert all(row.artifact_metadata["requires_review"] is True for row in rows)
            process = next(row for row in rows if row.artifact_type == "PROCESS_DESCRIPTION")
            reporting = next(row for row in rows if row.artifact_type == "REPORTING")
            assert process.content_text is not None
            assert "Hyvinvointialueet voivat hakea avustusta" in process.content_text
            assert "Prosessin omistaja: Tarkistettava" in process.content_text
            assert reporting.content_text is not None
            assert "Pakolliset KPI:t/mittarit: Tarkistettava" in reporting.content_text

        repeated_at = first_seen + timedelta(hours=1)
        async with session_factory() as session:
            async with session.begin():
                await persist_candidates(
                    session,
                    [_candidate("Ensimmäinen lähdekuvaus.")],
                    observed_at=repeated_at,
                )
                await ensure_cases_for_source_snapshot(
                    session,
                    source_code="STM",
                    observed_at=repeated_at,
                )
            count = await session.scalar(
                select(func.count())
                .select_from(FundingCaseArtifact)
                .where(FundingCaseArtifact.source_app == "VAKEVAHTI_AUTOMATION")
            )
            assert count == 2

        changed_at = first_seen + timedelta(hours=2)
        async with session_factory() as session:
            async with session.begin():
                await persist_candidates(
                    session,
                    [_candidate("Päivitetty lähdekuvaus ja uusi vaatimus.")],
                    observed_at=changed_at,
                )
                await ensure_cases_for_source_snapshot(
                    session,
                    source_code="STM",
                    observed_at=changed_at,
                )
            rows = list(
                (
                    await session.scalars(
                        select(FundingCaseArtifact).where(
                            FundingCaseArtifact.source_app == "VAKEVAHTI_AUTOMATION"
                        )
                    )
                ).all()
            )
            assert len(rows) == 4
            assert {row.version for row in rows} == {1, 2}
            newest = [row for row in rows if row.version == 2]
            assert len(newest) == 2
            assert all(
                row.content_text is not None and "Päivitetty lähdekuvaus" in row.content_text
                for row in newest
            )
    finally:
        async with engine.begin() as connection:
            await connection.execute(text(TRUNCATE_SQL))
        await engine.dispose()
