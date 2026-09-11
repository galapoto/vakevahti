import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import HttpUrl
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import NotificationOutbox
from app.domain.funding_call import FundingCallCandidate, RelevanceStatus
from app.services.ingestion import ScanTrigger, run_source_ingestion
from app.services.notification_outbox import FundingNotificationEvent, OutboxStatus

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not TEST_DATABASE_URL,
        reason="TEST_DATABASE_URL is required for PostgreSQL integration tests.",
    ),
]

TRUNCATE_SQL = (
    "TRUNCATE TABLE notification_outbox, source_scan_runs, funding_call_versions, "
    "funding_calls, source_states RESTART IDENTITY CASCADE"
)


class MutableScanner:
    source_code = "EURA"

    def __init__(self, candidates: list[FundingCallCandidate]) -> None:
        self.candidates = candidates

    async def scan(self) -> list[FundingCallCandidate]:
        return self.candidates


def make_candidate(
    external_key: str,
    *,
    relevance: RelevanceStatus = RelevanceStatus.RELEVANT,
    description: str = "Stable content",
) -> FundingCallCandidate:
    return FundingCallCandidate(
        external_key=external_key,
        source_code="EURA",
        title=f"Funding call {external_key}",
        source_url=HttpUrl(f"https://example.test/{external_key}"),
        description_text=description,
        relevance_status=relevance,
        relevance_reason=f"Deterministic {relevance.value} decision",
    )


@pytest.fixture
async def session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
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


async def test_outbox_suppresses_baseline_and_deduplicates_repeated_scans(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    first_seen = datetime(2026, 9, 11, 9, 0, tzinfo=UTC)
    scanner = MutableScanner([make_candidate("known")])

    baseline = await run_source_ingestion(
        scanner,
        session_factory,
        trigger=ScanTrigger.SCHEDULED,
        observed_at=first_seen,
    )
    assert baseline.persistence.baseline is True
    assert baseline.persistence.outcomes[0].notification_eligible is False

    async with session_factory() as session:
        assert (
            await session.scalar(select(func.count()).select_from(NotificationOutbox))
        ) == 0

    scanner.candidates = [
        make_candidate("known"),
        make_candidate("new-relevant"),
        make_candidate("new-review", relevance=RelevanceStatus.NEEDS_REVIEW),
        make_candidate("new-excluded", relevance=RelevanceStatus.NOT_RELEVANT),
    ]
    second = await run_source_ingestion(
        scanner,
        session_factory,
        trigger=ScanTrigger.SCHEDULED,
        observed_at=first_seen + timedelta(hours=1),
    )

    eligibility = {
        outcome.external_key: outcome.notification_eligible
        for outcome in second.persistence.outcomes
    }
    assert eligibility == {
        "known": False,
        "new-relevant": True,
        "new-review": True,
        "new-excluded": False,
    }

    async with session_factory() as session:
        rows = (
            await session.scalars(select(NotificationOutbox).order_by(NotificationOutbox.id))
        ).all()

    assert len(rows) == 2
    assert {row.event_type for row in rows} == {
        FundingNotificationEvent.DISCOVERED.value,
        FundingNotificationEvent.REVIEW_REQUIRED.value,
    }
    assert all(row.status == OutboxStatus.PENDING.value for row in rows)
    assert all(row.attempt_count == 0 for row in rows)
    assert all(row.source_scan_run_id == second.run_id for row in rows)
    assert len({row.dedupe_key for row in rows}) == 2

    third = await run_source_ingestion(
        scanner,
        session_factory,
        trigger=ScanTrigger.SCHEDULED,
        observed_at=first_seen + timedelta(hours=2),
    )
    assert all(not outcome.notification_eligible for outcome in third.persistence.outcomes)

    async with session_factory() as session:
        assert (
            await session.scalar(select(func.count()).select_from(NotificationOutbox))
        ) == 2


async def test_material_change_creates_versioned_changed_event(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    first_seen = datetime(2026, 9, 11, 12, 0, tzinfo=UTC)
    scanner = MutableScanner([make_candidate("call-1")])
    await run_source_ingestion(
        scanner,
        session_factory,
        trigger=ScanTrigger.SCHEDULED,
        observed_at=first_seen,
    )

    scanner.candidates = [make_candidate("call-1", description="Updated content")]
    changed = await run_source_ingestion(
        scanner,
        session_factory,
        trigger=ScanTrigger.SCHEDULED,
        observed_at=first_seen + timedelta(hours=1),
    )
    assert changed.persistence.outcomes[0].notification_eligible is True

    async with session_factory() as session:
        row = await session.scalar(select(NotificationOutbox))

    assert row is not None
    assert row.event_type == FundingNotificationEvent.CHANGED.value
    assert row.funding_call_version == 2
    assert row.source_scan_run_id == changed.run_id
    assert row.payload["funding_call_version"] == 2
    assert row.payload["source_scan_run_id"] == str(changed.run_id)
