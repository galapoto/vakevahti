import os
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import HttpUrl
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.requirement_models import FundingCaseRequirement
from app.domain.funding_call import Evidence, FundingCallCandidate, RelevanceStatus
from app.services.case_sync import ensure_cases_for_source_snapshot
from app.services.persistence import persist_candidates

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not TEST_DATABASE_URL,
        reason="TEST_DATABASE_URL is required for requirement integration tests.",
    ),
]

TRUNCATE_SQL = (
    "TRUNCATE TABLE funding_case_requirements, funding_case_tasks, "
    "funding_case_artifacts, funding_cases, funding_report_deliveries, "
    "funding_report_items, funding_reports, notification_outbox, source_scan_runs, "
    "funding_call_versions, funding_calls, source_states RESTART IDENTITY CASCADE"
)


def _candidate(description: str, evidence_text: str) -> FundingCallCandidate:
    return FundingCallCandidate(
        external_key="requirements-2026",
        source_code="STM",
        title="Rakenteisten rahoitusvaatimusten testihaku",
        source_url=HttpUrl("https://example.test/stm/requirements-2026"),
        application_deadline_on=datetime(2026, 12, 22, tzinfo=UTC).date(),
        description_text=description,
        relevance_status=RelevanceStatus.RELEVANT,
        relevance_reason="Hyvinvointialue kuuluu hakijaryhmään.",
        evidence=(
            Evidence(
                section="Hakuehdot",
                text=evidence_text,
                source_url=HttpUrl("https://example.test/stm/requirements-2026#ehdot"),
            ),
        ),
    )


async def test_requirement_projection_is_idempotent_and_versioned() -> None:
    assert TEST_DATABASE_URL is not None
    engine = create_async_engine(TEST_DATABASE_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    first_seen = datetime(2026, 9, 14, 11, 0, tzinfo=UTC)

    try:
        async with engine.begin() as connection:
            await connection.execute(text(TRUNCATE_SQL))

        first = _candidate(
            "Hakuilmoitus sisältää budjetin ja raportointivaatimuksia.",
            "Hakemukseen kuuluu pakollinen liite. Päätös hyväksytään ennen maksatusta.",
        )
        async with session_factory() as session:
            async with session.begin():
                await persist_candidates(session, [first], observed_at=first_seen)
                await ensure_cases_for_source_snapshot(
                    session,
                    source_code="STM",
                    observed_at=first_seen,
                )

        async with session_factory() as session:
            rows = list(
                (
                    await session.scalars(
                        select(FundingCaseRequirement).where(
                            FundingCaseRequirement.funding_call_version == 1
                        )
                    )
                ).all()
            )
            assert len(rows) == 6
            by_key = {row.requirement_key: row for row in rows}
            assert by_key["ELIGIBILITY"].certainty == "EVIDENCE_FOUND"
            assert by_key["APPLICATION_DEADLINE"].certainty == "CONFIRMED"
            assert by_key["REQUIRED_DOCUMENTS"].certainty == "EVIDENCE_FOUND"
            assert by_key["BUDGET_AND_COFUNDING"].certainty == "EVIDENCE_FOUND"
            assert by_key["APPROVALS_AND_DECISIONS"].certainty == "EVIDENCE_FOUND"
            assert by_key["REPORTING_OBLIGATIONS"].certainty == "EVIDENCE_FOUND"

        repeated_at = first_seen + timedelta(hours=1)
        async with session_factory() as session:
            async with session.begin():
                await persist_candidates(session, [first], observed_at=repeated_at)
                await ensure_cases_for_source_snapshot(
                    session,
                    source_code="STM",
                    observed_at=repeated_at,
                )
            count = await session.scalar(select(func.count()).select_from(FundingCaseRequirement))
            assert count == 6

        changed_at = first_seen + timedelta(hours=2)
        changed = _candidate(
            "Päivitetty hakuilmoitus ilman rakenteisesti tunnistettavaa budjettiehtoa.",
            "Hakemuksen vaatimukset on tarkistettava lähteestä.",
        )
        async with session_factory() as session:
            async with session.begin():
                await persist_candidates(session, [changed], observed_at=changed_at)
                await ensure_cases_for_source_snapshot(
                    session,
                    source_code="STM",
                    observed_at=changed_at,
                )
            rows = list((await session.scalars(select(FundingCaseRequirement))).all())
            assert len(rows) == 12
            newest = [row for row in rows if row.funding_call_version == 2]
            assert len(newest) == 6
            newest_by_key = {row.requirement_key: row for row in newest}
            assert newest_by_key["BUDGET_AND_COFUNDING"].certainty == "EVIDENCE_FOUND"
            assert newest_by_key["REQUIRED_DOCUMENTS"].certainty == "REVIEW_REQUIRED"
            assert newest_by_key["REPORTING_OBLIGATIONS"].certainty == "REVIEW_REQUIRED"
    finally:
        async with engine.begin() as connection:
            await connection.execute(text(TRUNCATE_SQL))
        await engine.dispose()
