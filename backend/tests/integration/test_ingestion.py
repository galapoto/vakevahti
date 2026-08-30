import os
from collections.abc import AsyncIterator

import pytest
from pydantic import HttpUrl
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import FundingCallRecord, SourceScanRun
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


class FakeScanner:
    source_code = "STM"

    def __init__(
        self,
        *,
        candidates: list[FundingCallCandidate] | None = None,
        error: Exception | None = None,
    ) -> None:
        self._candidates = candidates or []
        self._error = error

    async def scan(self) -> list[FundingCallCandidate]:
        if self._error is not None:
            raise self._error
        return self._candidates


def make_candidate(external_key: str = "call-1") -> FundingCallCandidate:
    return FundingCallCandidate(
        external_key=external_key,
        source_code="STM",
        title="Audited funding call",
        source_url=HttpUrl("https://example.test/funding-call"),
        description_text="Funding-call details",
        relevance_status=RelevanceStatus.RELEVANT,
        relevance_reason="STM business rule",
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


async def test_successful_ingestion_is_audited(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    result = await run_source_ingestion(
        FakeScanner(candidates=[make_candidate()]),
        session_factory,
        trigger=ScanTrigger.MANUAL_CLI,
    )

    assert result.persistence.baseline is True
    assert result.persistence.new_count == 1

    async with session_factory() as session:
        run = await session.get(SourceScanRun, result.run_id)
        assert run is not None
        assert run.status == ScanRunStatus.SUCCEEDED.value
        assert run.trigger_type == ScanTrigger.MANUAL_CLI.value
        assert run.discovered_count == 1
        assert run.new_count == 1
        assert run.unchanged_count == 0
        assert run.changed_count == 0
        assert run.baseline is True
        assert run.completed_at is not None
        assert run.error_type is None

        record_count = await session.scalar(
            select(func.count()).select_from(FundingCallRecord)
        )
        assert record_count == 1


async def test_failed_source_scan_is_audited_without_funding_mutation(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    with pytest.raises(RuntimeError, match="source unavailable"):
        await run_source_ingestion(
            FakeScanner(error=RuntimeError("source unavailable")),
            session_factory,
            trigger=ScanTrigger.SCHEDULED,
        )

    async with session_factory() as session:
        run = await session.scalar(select(SourceScanRun))
        assert run is not None
        assert run.status == ScanRunStatus.FAILED.value
        assert run.trigger_type == ScanTrigger.SCHEDULED.value
        assert run.error_type == "RuntimeError"
        assert run.error_message == "source unavailable"
        assert run.discovered_count is None
        assert run.completed_at is not None

        record_count = await session.scalar(
            select(func.count()).select_from(FundingCallRecord)
        )
        assert record_count == 0
