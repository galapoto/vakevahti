import os
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import HttpUrl
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

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


def make_candidate(
    *,
    external_key: str,
    title: str = "Initial title",
    description_text: str | None = None,
) -> FundingCallCandidate:
    return FundingCallCandidate(
        external_key=external_key,
        source_code="STM",
        title=title,
        source_url=HttpUrl("https://example.test/call"),
        description_text=description_text,
        relevance_status=RelevanceStatus.RELEVANT,
        relevance_reason="STM business rule",
    )


@pytest.fixture
async def db_session() -> AsyncSession:
    assert TEST_DATABASE_URL is not None
    engine = create_async_engine(TEST_DATABASE_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.execute(
            text(
                "TRUNCATE TABLE funding_call_versions, funding_calls, source_states "
                "RESTART IDENTITY CASCADE"
            )
        )

    async with session_factory() as session:
        yield session

    await engine.dispose()


async def test_baseline_repeat_change_and_new_are_idempotent(
    db_session: AsyncSession,
) -> None:
    day_one = datetime(2026, 8, 27, 9, 0, tzinfo=UTC)
    first = make_candidate(external_key="call-1", description_text="Original")

    async with db_session.begin():
        baseline = await persist_candidates(db_session, [first], observed_at=day_one)

    assert baseline.baseline is True
    assert baseline.outcomes[0].status is ChangeStatus.NEW
    assert baseline.outcomes[0].notification_eligible is False

    async with db_session.begin():
        repeated = await persist_candidates(
            db_session,
            [first],
            observed_at=day_one + timedelta(hours=1),
        )

    assert repeated.baseline is False
    assert repeated.outcomes[0].status is ChangeStatus.UNCHANGED
    assert repeated.outcomes[0].notification_eligible is False

    changed = make_candidate(external_key="call-1", description_text="Updated")
    async with db_session.begin():
        changed_result = await persist_candidates(
            db_session,
            [changed],
            observed_at=day_one + timedelta(hours=2),
        )

    assert changed_result.outcomes[0].status is ChangeStatus.CHANGED
    assert changed_result.outcomes[0].notification_eligible is True

    second = make_candidate(external_key="call-2", title="New funding call")
    async with db_session.begin():
        new_result = await persist_candidates(
            db_session,
            [changed, second],
            observed_at=day_one + timedelta(hours=3),
        )

    assert [outcome.status for outcome in new_result.outcomes] == [
        ChangeStatus.UNCHANGED,
        ChangeStatus.NEW,
    ]
    assert new_result.outcomes[1].notification_eligible is True

    record_count = await db_session.scalar(select(func.count()).select_from(FundingCallRecord))
    version_count = await db_session.scalar(select(func.count()).select_from(FundingCallVersion))

    assert record_count == 2
    assert version_count == 3

    stored = await db_session.scalar(
        select(FundingCallRecord).where(FundingCallRecord.external_key == "call-1")
    )
    assert stored is not None
    assert stored.current_version == 2
    assert stored.description_text == "Updated"
