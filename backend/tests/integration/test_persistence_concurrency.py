import asyncio
import os

import pytest
from pydantic import HttpUrl
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.models import FundingCallRecord, FundingCallVersion
from app.domain.funding_call import FundingCallCandidate, RelevanceStatus
from app.services.persistence import ChangeStatus, persist_candidates

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


def make_candidate() -> FundingCallCandidate:
    return FundingCallCandidate(
        external_key="concurrent-call",
        source_code="STM",
        title="Concurrent funding call",
        source_url=HttpUrl("https://example.test/concurrent"),
        relevance_status=RelevanceStatus.RELEVANT,
        relevance_reason="STM business rule",
    )


async def test_concurrent_first_persistence_is_serialized_per_source() -> None:
    assert TEST_DATABASE_URL is not None
    engine = create_async_engine(TEST_DATABASE_URL)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.execute(text(TRUNCATE_SQL))

    candidate = make_candidate()

    async def persist_once() -> tuple[bool, ChangeStatus]:
        async with factory() as session:
            async with session.begin():
                result = await persist_candidates(session, [candidate])
        return result.baseline, result.outcomes[0].status

    try:
        results = await asyncio.gather(persist_once(), persist_once())

        statuses = sorted(status.value for _, status in results)
        baselines = sorted(baseline for baseline, _ in results)
        assert statuses == [ChangeStatus.NEW.value, ChangeStatus.UNCHANGED.value]
        assert baselines == [False, True]

        async with factory() as session:
            record_count = await session.scalar(
                select(func.count()).select_from(FundingCallRecord)
            )
            version_count = await session.scalar(
                select(func.count()).select_from(FundingCallVersion)
            )

        assert record_count == 1
        assert version_count == 1
    finally:
        async with engine.begin() as connection:
            await connection.execute(text(TRUNCATE_SQL))
        await engine.dispose()
