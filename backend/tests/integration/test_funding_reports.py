import os
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from pydantic import HttpUrl
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

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
        reason="TEST_DATABASE_URL is required for funding report integration tests.",
    ),
]

TRUNCATE_SQL = (
    "TRUNCATE TABLE funding_report_items, funding_reports, notification_outbox, "
    "source_scan_runs, funding_call_versions, funding_calls, source_states "
    "RESTART IDENTITY CASCADE"
)


def make_candidate(*, external_key: str, title: str, days: int) -> FundingCallCandidate:
    observed_at = datetime(2026, 9, 11, 8, 0, tzinfo=UTC)
    return FundingCallCandidate(
        external_key=external_key,
        source_code="STM",
        title=title,
        source_url=HttpUrl(f"https://example.test/stm/{external_key}"),
        application_deadline_at=observed_at + timedelta(days=days),
        description_text=f"Details for {title}",
        relevance_status=RelevanceStatus.RELEVANT,
        relevance_reason=f"{title} supports a VakeHyvä development objective.",
    )


@pytest.fixture
async def report_api() -> tuple[
    httpx.AsyncClient,
    async_sessionmaker[AsyncSession],
]:
    assert TEST_DATABASE_URL is not None
    engine = create_async_engine(TEST_DATABASE_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.execute(text(TRUNCATE_SQL))

    settings = Settings(
        database_url=TEST_DATABASE_URL,
        enabled_sources="STM",
        enable_report_write_routes=True,
    )
    application = create_app(settings, session_factory=session_factory)
    transport = httpx.ASGITransport(app=application)

    try:
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            yield client, session_factory
    finally:
        async with engine.begin() as connection:
            await connection.execute(text(TRUNCATE_SQL))
        await engine.dispose()


async def seed_calls(
    session_factory: async_sessionmaker[AsyncSession],
) -> list[int]:
    observed_at = datetime(2026, 9, 11, 8, 0, tzinfo=UTC)
    candidates = [
        make_candidate(external_key="report-one", title="Report call one", days=10),
        make_candidate(external_key="report-two", title="Report call two", days=20),
    ]
    async with session_factory() as session:
        async with session.begin():
            await persist_candidates(session, candidates, observed_at=observed_at)
        result = await session.execute(
            select(FundingCallRecord).order_by(FundingCallRecord.id.asc())
        )
        return [record.id for record in result.scalars()]


async def test_report_draft_snapshots_calls_and_submits_idempotently(
    report_api: tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = report_api
    call_ids = await seed_calls(session_factory)

    created = await client.post(
        "/api/reports",
        json={
            "title": "VakeHyvän rahoitusraportti",
            "notes": "Tarkista omistajuus ennen valmistelun käynnistämistä.",
            "funding_call_ids": call_ids,
        },
    )
    assert created.status_code == 201
    payload = created.json()
    assert payload["status"] == "DRAFT"
    assert [item["funding_call_id"] for item in payload["items"]] == call_ids
    assert payload["items"][0]["snapshot"]["title"] == "Report call one"
    assert payload["items"][0]["snapshot"]["relevance_reason"].startswith(
        "Report call one"
    )

    report_id = payload["id"]
    fetched = await client.get(f"/api/reports/{report_id}")
    assert fetched.status_code == 200
    assert fetched.json()["notes"].startswith("Tarkista omistajuus")

    submitted = await client.post(f"/api/reports/{report_id}/submit")
    assert submitted.status_code == 200
    submitted_payload = submitted.json()
    assert submitted_payload["status"] == "WAITING_APPROVAL"
    assert submitted_payload["submitted_for_approval_at"] is not None

    repeated = await client.post(f"/api/reports/{report_id}/submit")
    assert repeated.status_code == 200
    assert repeated.json()["submitted_for_approval_at"] == submitted_payload[
        "submitted_for_approval_at"
    ]


async def test_report_creation_rejects_missing_call_ids(
    report_api: tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = report_api

    response = await client.post(
        "/api/reports",
        json={"funding_call_ids": [123456]},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == {"missing_funding_call_ids": [123456]}
