import os
from datetime import UTC, datetime

import httpx
import pytest
from pydantic import HttpUrl
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
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


def make_candidate(
    external_key: str,
    status: RelevanceStatus,
) -> FundingCallCandidate:
    return FundingCallCandidate(
        external_key=external_key,
        source_code="HAEAVUSTUKSIA",
        title=f"Call {external_key}",
        source_url=HttpUrl(f"https://example.test/{external_key}"),
        relevance_status=status,
        relevance_reason=f"Classification: {status.value}",
    )


async def test_source_health_separates_confirmed_review_and_excluded_counts() -> None:
    assert TEST_DATABASE_URL is not None
    engine = create_async_engine(TEST_DATABASE_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.execute(text(TRUNCATE_SQL))

    try:
        observed_at = datetime(2026, 9, 11, 9, 0, tzinfo=UTC)
        candidates = [
            make_candidate("confirmed", RelevanceStatus.RELEVANT),
            make_candidate("review", RelevanceStatus.NEEDS_REVIEW),
            make_candidate("excluded", RelevanceStatus.NOT_RELEVANT),
        ]

        async with session_factory() as session:
            async with session.begin():
                await persist_candidates(
                    session,
                    candidates,
                    observed_at=observed_at,
                )

        settings = Settings(
            database_url=TEST_DATABASE_URL,
            enabled_sources="HAEAVUSTUKSIA",
        )
        application = create_app(settings, session_factory=session_factory)
        transport = httpx.ASGITransport(app=application)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            health_response = await client.get("/api/sources/health")
            assert health_response.status_code == 200
            source = health_response.json()["sources"][0]
            assert source["current_call_count"] == 2
            assert source["relevant_call_count"] == 1
            assert source["review_call_count"] == 1

            calls_response = await client.get("/api/funding-calls")
            assert calls_response.status_code == 200
            payload = calls_response.json()
            assert payload["total"] == 2
            assert {item["relevance_status"] for item in payload["items"]} == {
                "RELEVANT",
                "NEEDS_REVIEW",
            }

            confirmed_response = await client.get(
                "/api/funding-calls",
                params={"relevance_status": "RELEVANT"},
            )
            assert confirmed_response.status_code == 200
            confirmed = confirmed_response.json()
            assert confirmed["total"] == 1
            assert [item["title"] for item in confirmed["items"]] == ["Call confirmed"]

            review_response = await client.get(
                "/api/funding-calls",
                params={"relevance_status": "NEEDS_REVIEW"},
            )
            assert review_response.status_code == 200
            review = review_response.json()
            assert review["total"] == 1
            assert [item["title"] for item in review["items"]] == ["Call review"]

            excluded_filter = await client.get(
                "/api/funding-calls",
                params={"relevance_status": "NOT_RELEVANT"},
            )
            assert excluded_filter.status_code == 422
    finally:
        async with engine.begin() as connection:
            await connection.execute(text(TRUNCATE_SQL))
        await engine.dispose()
