import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import HttpUrl
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import FundingCallRecord, FundingCallVersion, SourceScanRun
from app.domain.funding_call import FundingCallCandidate, RelevanceStatus
from app.services.ingestion import ScanRunStatus, ScanTrigger, run_source_ingestion

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not TEST_DATABASE_URL,
        reason="TEST_DATABASE_URL is required for PostgreSQL integration tests.",
    ),
]

TRUNCATE_SQL = (
    "TRUNCATE TABLE source_scan_runs, funding_call_versions, funding_calls, "
    "source_states RESTART IDENTITY CASCADE"
)


class RepeatableScanner:
    source_code = "EURA"

    async def scan(self) -> list[FundingCallCandidate]:
        return [
            FundingCallCandidate(
                external_key="eura-stable-call",
                source_code=self.source_code,
                title="Stable EURA call",
                source_url=HttpUrl("https://eura2021.fi/hakuilmoitukset/hakuilmoitus/test"),
                relevance_status=RelevanceStatus.RELEVANT,
                relevance_reason="Stable deterministic classification",
            )
        ]


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


async def test_repeated_source_ingestion_is_idempotent_and_fully_audited(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    first_seen = datetime(2026, 9, 11, 8, 0, tzinfo=UTC)
    second_seen = first_seen + timedelta(minutes=5)
    scanner = RepeatableScanner()

    first = await run_source_ingestion(
        scanner,
        session_factory,
        trigger=ScanTrigger.MANUAL_CLI,
        observed_at=first_seen,
    )
    second = await run_source_ingestion(
        scanner,
        session_factory,
        trigger=ScanTrigger.MANUAL_CLI,
        observed_at=second_seen,
    )

    assert first.persistence.baseline is True
    assert first.persistence.new_count == 1
    assert second.persistence.baseline is False
    assert second.persistence.new_count == 0
    assert second.persistence.unchanged_count == 1
    assert second.persistence.changed_count == 0

    async with session_factory() as session:
        record_count = await session.scalar(select(func.count()).select_from(FundingCallRecord))
        version_count = await session.scalar(
            select(func.count()).select_from(FundingCallVersion)
        )
        runs = (
            await session.scalars(
                select(SourceScanRun).order_by(SourceScanRun.started_at, SourceScanRun.id)
            )
        ).all()
        record = await session.scalar(
            select(FundingCallRecord).where(
                FundingCallRecord.external_key == "eura-stable-call"
            )
        )

    assert record_count == 1
    assert version_count == 1
    assert record is not None
    assert record.current_version == 1
    assert record.last_seen_at == second_seen
    assert len(runs) == 2
    assert [run.status for run in runs] == [
        ScanRunStatus.SUCCEEDED.value,
        ScanRunStatus.SUCCEEDED.value,
    ]
    assert runs[0].new_count == 1
    assert runs[0].unchanged_count == 0
    assert runs[1].new_count == 0
    assert runs[1].unchanged_count == 1
    assert runs[1].changed_count == 0
