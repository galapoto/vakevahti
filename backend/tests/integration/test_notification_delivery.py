import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import HttpUrl
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import NotificationOutbox
from app.domain.funding_call import FundingCallCandidate, RelevanceStatus
from app.services.ingestion import ScanTrigger, run_source_ingestion
from app.services.notification_delivery import (
    StaleOutboxClaimError,
    claim_notification_intents,
    mark_notification_failed,
    mark_notification_sent,
)
from app.services.notification_outbox import OutboxStatus

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
    source_code = "STM"

    def __init__(self, keys: list[str]) -> None:
        self.keys = keys

    async def scan(self) -> list[FundingCallCandidate]:
        return [
            FundingCallCandidate(
                external_key=key,
                source_code=self.source_code,
                title=f"Call {key}",
                source_url=HttpUrl(f"https://example.test/{key}"),
                relevance_status=RelevanceStatus.RELEVANT,
                relevance_reason="STM calls are relevant by source rule",
            )
            for key in self.keys
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


async def _seed_pending_intent(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    observed_at: datetime,
) -> None:
    scanner = MutableScanner(["baseline"])
    await run_source_ingestion(
        scanner,
        session_factory,
        trigger=ScanTrigger.SCHEDULED,
        observed_at=observed_at,
    )
    scanner.keys = ["baseline", "new"]
    await run_source_ingestion(
        scanner,
        session_factory,
        trigger=ScanTrigger.SCHEDULED,
        observed_at=observed_at + timedelta(minutes=5),
    )


async def test_delivery_claim_failure_retry_and_sent_lifecycle(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    now = datetime(2026, 9, 11, 14, 0, tzinfo=UTC)
    await _seed_pending_intent(session_factory, observed_at=now - timedelta(hours=1))

    async with session_factory() as session:
        async with session.begin():
            claims = await claim_notification_intents(
                session,
                now=now,
                limit=10,
                lease_seconds=60,
            )
    assert len(claims) == 1
    first = claims[0]
    assert first.attempt_count == 1

    async with session_factory() as session:
        with pytest.raises(StaleOutboxClaimError):
            async with session.begin():
                await mark_notification_sent(
                    session,
                    outbox_id=first.id,
                    claim_token=uuid4(),
                    sent_at=now,
                )

    retry_at = now + timedelta(minutes=10)
    async with session_factory() as session:
        async with session.begin():
            await mark_notification_failed(
                session,
                outbox_id=first.id,
                claim_token=first.claim_token,
                error="temporary platform transport failure",
                next_attempt_at=retry_at,
            )

    async with session_factory() as session:
        async with session.begin():
            too_early = await claim_notification_intents(
                session,
                now=retry_at - timedelta(seconds=1),
            )
    assert too_early == ()

    async with session_factory() as session:
        async with session.begin():
            retry = await claim_notification_intents(session, now=retry_at)
    assert len(retry) == 1
    second = retry[0]
    assert second.attempt_count == 2
    assert second.claim_token != first.claim_token

    sent_at = retry_at + timedelta(seconds=5)
    async with session_factory() as session:
        async with session.begin():
            await mark_notification_sent(
                session,
                outbox_id=second.id,
                claim_token=second.claim_token,
                sent_at=sent_at,
            )

    async with session_factory() as session:
        row = await session.scalar(
            select(NotificationOutbox).where(NotificationOutbox.id == second.id)
        )
    assert row is not None
    assert row.status == OutboxStatus.SENT.value
    assert row.attempt_count == 2
    assert row.sent_at == sent_at
    assert row.last_error is None
    assert row.claim_token is None
    assert row.claim_expires_at is None


async def test_expired_processing_lease_can_be_reclaimed_safely(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    now = datetime(2026, 9, 11, 16, 0, tzinfo=UTC)
    await _seed_pending_intent(session_factory, observed_at=now - timedelta(hours=1))

    async with session_factory() as session:
        async with session.begin():
            first = (await claim_notification_intents(
                session,
                now=now,
                lease_seconds=60,
            ))[0]

    async with session_factory() as session:
        async with session.begin():
            before_expiry = await claim_notification_intents(
                session,
                now=now + timedelta(seconds=59),
            )
    assert before_expiry == ()

    async with session_factory() as session:
        async with session.begin():
            reclaimed = (await claim_notification_intents(
                session,
                now=now + timedelta(seconds=61),
                lease_seconds=60,
            ))[0]

    assert reclaimed.id == first.id
    assert reclaimed.attempt_count == 2
    assert reclaimed.claim_token != first.claim_token

    async with session_factory() as session:
        with pytest.raises(StaleOutboxClaimError):
            async with session.begin():
                await mark_notification_sent(
                    session,
                    outbox_id=first.id,
                    claim_token=first.claim_token,
                    sent_at=now + timedelta(seconds=62),
                )
