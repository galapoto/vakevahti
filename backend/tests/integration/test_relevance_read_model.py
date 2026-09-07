import os
from datetime import UTC, datetime

import httpx
import pytest
from pydantic import HttpUrl
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.models import FundingCallRecord
from app.domain.funding_call import FundingCallCandidate, RelevanceStatus
from app.main import create_app
from app.services.persistence import persist_candidates

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not TEST_DATABASE_URL,
        reason="TEST_DATABASE_URL is required for PostgreSQL API integration tests.",
    ),
]

TRUNCATE_SQL = (
    "TRUNCATE TABLE source_scan_runs, funding_call_versions, funding_calls, "
    "source_states RESTART IDENTITY CASCADE"
)


def candidate(
    key: str,
    title: str,
    status: RelevanceStatus,
) -> FundingCallCandidate:
    return FundingCallCandidate(
        external_key=key,
        source_code="HAEAVUSTUKSIA",
        title=title,
        source_url=HttpUrl(f"https://example.test/hae/{key}"),
        relevance_status=status,
        relevance_reason=f"test relevance: {status.value}",
    )


async def test_not_relevant_current_rows_are_retained_but_hidden_from_operator_api() -> None:
    assert TEST_DATABASE_URL is not None
    engine = create_async_engine(TEST_DATABASE_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.execute(text(TRUNCATE_SQL))

    observed_at = datetime(2026, 9, 7, 8, 0, tzinfo=UTC)
    visible = candidate("visible", "Relevant grant", RelevanceStatus.RELEVANT)
    hidden = candidate("hidden", "Agriculture-only grant", RelevanceStatus.NOT_RELEVANT)

    try:
        async with session_factory() as session:
            async with session.begin():
                await persist_candidates(
                    session,
                    [visible, hidden],
                    observed_at=observed_at,
                )

        settings = Settings(
            database_url=TEST_DATABASE_URL,
            enabled_sources="HAEAVUSTUKSIA",
        )
        app = create_app(settings, session_factory=session_factory)
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            listing = await client.get("/api/funding-calls")
            assert listing.status_code == 200
            payload = listing.json()
            assert payload["total"] == 1
            assert [item["title"] for item in payload["items"]] == ["Relevant grant"]

            health = await client.get("/api/sources/health")
            assert health.status_code == 200
            assert health.json()["sources"][0]["current_call_count"] == 1

        async with session_factory() as session:
            stored_total = int(
                (await session.scalar(select(func.count()).select_from(FundingCallRecord)))
                or 0
            )
            hidden_id = await session.scalar(
                select(FundingCallRecord.id).where(
                    FundingCallRecord.external_key == "hidden"
                )
            )

        assert stored_total == 2
        assert hidden_id is not None

        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            hidden_detail = await client.get(f"/api/funding-calls/{hidden_id}")
            assert hidden_detail.status_code == 404
    finally:
        async with engine.begin() as connection:
            await connection.execute(text(TRUNCATE_SQL))
        await engine.dispose()
