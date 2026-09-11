import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from pydantic import HttpUrl
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.report_schemas import FundingReportStatus, FundingReportUpdate
from app.db.models import SourceScanRun
from app.domain.funding_call import FundingCallCandidate, RelevanceStatus
from app.services.funding_reports import (
    create_automated_funding_report,
    submit_funding_report_for_approval,
    update_funding_report,
)
from app.services.persistence import persist_candidates

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not TEST_DATABASE_URL,
        reason="TEST_DATABASE_URL is required for automatic report integration tests.",
    ),
]

TRUNCATE_SQL = (
    "TRUNCATE TABLE funding_report_items, funding_reports, notification_outbox, "
    "source_scan_runs, funding_call_versions, funding_calls, source_states "
    "RESTART IDENTITY CASCADE"
)


def _candidate(*, title: str, reason: str) -> FundingCallCandidate:
    return FundingCallCandidate(
        external_key="auto-report-call",
        source_code="STM",
        title=title,
        source_url=HttpUrl("https://example.test/stm/auto-report-call"),
        application_deadline_at=datetime(2026, 10, 15, 13, 0, tzinfo=UTC),
        description_text="Automatic report integration test call",
        relevance_status=RelevanceStatus.RELEVANT,
        relevance_reason=reason,
    )


@pytest.fixture
async def session_factory() -> async_sessionmaker[AsyncSession]:
    assert TEST_DATABASE_URL is not None
    engine = create_async_engine(TEST_DATABASE_URL)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.execute(text(TRUNCATE_SQL))
    try:
        yield factory
    finally:
        async with engine.begin() as connection:
            await connection.execute(text(TRUNCATE_SQL))
        await engine.dispose()


async def _seed_changed_scan(
    factory: async_sessionmaker[AsyncSession],
) -> tuple[UUID, datetime]:
    baseline_at = datetime(2026, 9, 11, 8, 0, tzinfo=UTC)
    changed_at = baseline_at + timedelta(hours=1)
    run_id = uuid4()

    async with factory() as session:
        async with session.begin():
            await persist_candidates(
                session,
                [_candidate(title="Original title", reason="Original reason")],
                observed_at=baseline_at,
            )

        async with session.begin():
            session.add(
                SourceScanRun(
                    id=run_id,
                    source_code="STM",
                    trigger_type="SCHEDULED",
                    status="SUCCEEDED",
                    started_at=changed_at,
                    completed_at=changed_at,
                    baseline=False,
                    discovered_count=1,
                    new_count=0,
                    unchanged_count=0,
                    changed_count=1,
                    error_type=None,
                    error_message=None,
                )
            )
            await session.flush()
            result = await persist_candidates(
                session,
                [
                    _candidate(
                        title="Updated digital care funding call",
                        reason="Supports VakeHyvä digital service development.",
                    )
                ],
                observed_at=changed_at,
                source_scan_run_id=run_id,
            )
            assert result.changed_count == 1

    return run_id, changed_at


async def test_scan_events_create_one_unique_editable_automatic_report(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    run_id, changed_at = await _seed_changed_scan(session_factory)

    async with session_factory() as session:
        first = await create_automated_funding_report(
            session,
            scan_run_ids=(run_id,),
            recipient_emails=("coordinator@example.test", "self@example.test"),
            generated_at=changed_at,
        )
        assert first is not None
        assert first.origin.value == "AUTOMATED"
        assert first.automation_key is not None
        assert "Updated digital care funding call" in first.title
        assert "Updated digital care funding call" in (first.email_subject or "")
        assert "Miksi VakeHyvälle" in (first.email_body or "")
        assert first.recipient_emails == [
            "coordinator@example.test",
            "self@example.test",
        ]
        assert first.items[0].snapshot["event_type"] == "funding.opportunity.changed.v1"

        repeated = await create_automated_funding_report(
            session,
            scan_run_ids=(run_id,),
            recipient_emails=("ignored@example.test",),
            generated_at=changed_at + timedelta(minutes=5),
        )
        assert repeated is not None
        assert repeated.id == first.id

        submitted = await submit_funding_report_for_approval(session, first.id)
        assert submitted.status is FundingReportStatus.WAITING_APPROVAL

        edited = await update_funding_report(
            session,
            first.id,
            FundingReportUpdate(
                email_subject="Coordinator-edited subject",
                email_body="Coordinator-edited body",
                recipient_emails=["new-recipient@example.test"],
            ),
        )
        assert edited.status is FundingReportStatus.DRAFT
        assert edited.submitted_for_approval_at is None
        assert edited.email_subject == "Coordinator-edited subject"
        assert edited.recipient_emails == ["new-recipient@example.test"]


async def test_baseline_without_notification_events_creates_no_report(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    baseline_at = datetime(2026, 9, 11, 8, 0, tzinfo=UTC)
    run_id = uuid4()
    async with session_factory() as session:
        async with session.begin():
            session.add(
                SourceScanRun(
                    id=run_id,
                    source_code="STM",
                    trigger_type="SCHEDULED",
                    status="SUCCEEDED",
                    started_at=baseline_at,
                    completed_at=baseline_at,
                    baseline=True,
                    discovered_count=1,
                    new_count=1,
                    unchanged_count=0,
                    changed_count=0,
                    error_type=None,
                    error_message=None,
                )
            )
            await session.flush()
            await persist_candidates(
                session,
                [_candidate(title="Baseline call", reason="Relevant but baseline")],
                observed_at=baseline_at,
                source_scan_run_id=run_id,
            )

        report = await create_automated_funding_report(
            session,
            scan_run_ids=(run_id,),
            generated_at=baseline_at,
        )
        assert report is None
