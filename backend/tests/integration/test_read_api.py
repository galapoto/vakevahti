import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import httpx
import pytest
from pydantic import HttpUrl
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.models import SourceScanRun
from app.domain.funding_call import FundingCallCandidate, RelevanceStatus
from app.main import create_app
from app.services.ingestion import ScanRunStatus, ScanTrigger
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
    *,
    source_code: str,
    external_key: str,
    title: str,
    deadline: datetime | None = None,
) -> FundingCallCandidate:
    return FundingCallCandidate(
        external_key=external_key,
        source_code=source_code,
        title=title,
        source_url=HttpUrl(f"https://example.test/{source_code.lower()}/{external_key}"),
        application_deadline_at=deadline,
        description_text=f"Details for {title}",
        relevance_status=RelevanceStatus.RELEVANT,
        relevance_reason=f"{source_code} business rule",
    )


@pytest.fixture
async def api_context() -> tuple[
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
        enabled_sources="STM,SITRA,ACADEMY",
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


async def seed_persisted_calls(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    observed_at = datetime(2026, 8, 30, 9, 0, tzinfo=UTC)
    stm_calls = [
        make_candidate(
            source_code="STM",
            external_key="stm-later",
            title="STM later deadline",
            deadline=observed_at + timedelta(days=20),
        ),
        make_candidate(
            source_code="STM",
            external_key="stm-sooner",
            title="STM sooner deadline",
            deadline=observed_at + timedelta(days=10),
        ),
    ]
    academy_calls = [
        make_candidate(
            source_code="ACADEMY",
            external_key="academy-one",
            title="Academy call",
            deadline=None,
        )
    ]

    async with session_factory() as session:
        async with session.begin():
            await persist_candidates(session, stm_calls, observed_at=observed_at)
        async with session.begin():
            await persist_candidates(
                session,
                academy_calls,
                observed_at=observed_at + timedelta(minutes=1),
            )


async def test_funding_list_filters_paginates_and_reads_detail(
    api_context: tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = api_context
    await seed_persisted_calls(session_factory)

    first_page = await client.get(
        "/api/funding-calls",
        params={"source_code": "stm", "limit": 1, "offset": 0},
    )
    assert first_page.status_code == 200
    first_payload = first_page.json()
    assert first_payload["total"] == 2
    assert first_payload["limit"] == 1
    assert first_payload["offset"] == 0
    assert [item["title"] for item in first_payload["items"]] == ["STM sooner deadline"]

    second_page = await client.get(
        "/api/funding-calls",
        params={"source_code": "STM", "limit": 1, "offset": 1},
    )
    assert second_page.status_code == 200
    second_payload = second_page.json()
    assert [item["title"] for item in second_payload["items"]] == ["STM later deadline"]

    all_calls = await client.get("/api/funding-calls")
    assert all_calls.status_code == 200
    assert all_calls.json()["total"] == 3

    funding_call_id = first_payload["items"][0]["id"]
    retired_call_id = second_payload["items"][0]["id"]
    detail = await client.get(f"/api/funding-calls/{funding_call_id}")
    assert detail.status_code == 200
    detail_payload = detail.json()
    assert detail_payload["title"] == "STM sooner deadline"
    assert detail_payload["description_text"] == "Details for STM sooner deadline"
    assert detail_payload["relevance_reason"] == "STM business rule"
    assert "content_hash" not in detail_payload
    assert "external_key" not in detail_payload

    missing = await client.get("/api/funding-calls/999999")
    assert missing.status_code == 404

    invalid_limit = await client.get("/api/funding-calls", params={"limit": 101})
    assert invalid_limit.status_code == 422

    # A later authoritative source snapshot contains only the sooner call. The
    # disappeared call remains stored historically but must leave the current API.
    later_observation = datetime(2026, 8, 30, 11, 0, tzinfo=UTC)
    still_current = make_candidate(
        source_code="STM",
        external_key="stm-sooner",
        title="STM sooner deadline",
        deadline=datetime(2026, 9, 9, 9, 0, tzinfo=UTC),
    )
    async with session_factory() as session:
        async with session.begin():
            await persist_candidates(
                session,
                [still_current],
                observed_at=later_observation,
            )

    after_retirement = await client.get(
        "/api/funding-calls",
        params={"source_code": "STM", "limit": 100},
    )
    assert after_retirement.status_code == 200
    retirement_payload = after_retirement.json()
    assert retirement_payload["total"] == 1
    assert [item["title"] for item in retirement_payload["items"]] == [
        "STM sooner deadline"
    ]

    retired_detail = await client.get(f"/api/funding-calls/{retired_call_id}")
    assert retired_detail.status_code == 404

    # A recognized successful source snapshot may legitimately contain no current
    # opportunities. Advancing the source watermark must then yield an empty API set.
    async with session_factory() as session:
        async with session.begin():
            await persist_candidates(
                session,
                [],
                source_code="STM",
                observed_at=later_observation + timedelta(hours=1),
            )

    empty_current = await client.get(
        "/api/funding-calls",
        params={"source_code": "STM", "limit": 100},
    )
    assert empty_current.status_code == 200
    assert empty_current.json()["total"] == 0


async def test_source_health_reports_success_failure_running_and_never_scanned(
    api_context: tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = api_context
    await seed_persisted_calls(session_factory)

    started_at = datetime(2026, 8, 30, 10, 0, tzinfo=UTC)
    async with session_factory() as session:
        async with session.begin():
            session.add(
                SourceScanRun(
                    id=uuid4(),
                    source_code="STM",
                    trigger_type=ScanTrigger.SCHEDULED.value,
                    status=ScanRunStatus.SUCCEEDED.value,
                    started_at=started_at,
                    completed_at=started_at + timedelta(seconds=5),
                    baseline=False,
                    discovered_count=2,
                    new_count=0,
                    unchanged_count=2,
                    changed_count=0,
                )
            )
            session.add(
                SourceScanRun(
                    id=uuid4(),
                    source_code="SITRA",
                    trigger_type=ScanTrigger.SCHEDULED.value,
                    status=ScanRunStatus.FAILED.value,
                    started_at=started_at + timedelta(minutes=1),
                    completed_at=started_at + timedelta(minutes=1, seconds=3),
                    error_type="SourceStructureError",
                )
            )

    response = await client.get("/api/sources/health")
    assert response.status_code == 200
    items = {item["source_code"]: item for item in response.json()["sources"]}

    assert list(items) == ["STM", "SITRA", "ACADEMY"]
    assert items["STM"]["health"] == "HEALTHY"
    assert items["STM"]["current_call_count"] == 2
    assert items["STM"]["latest_unchanged_count"] == 2
    assert items["STM"]["baseline_completed_at"] is not None

    assert items["SITRA"]["health"] == "FAILING"
    assert items["SITRA"]["current_call_count"] == 0
    assert items["SITRA"]["latest_error_type"] == "SourceStructureError"
    assert items["SITRA"]["last_successful_scan_at"] is None

    assert items["ACADEMY"]["health"] == "NEVER_SCANNED"
    assert items["ACADEMY"]["latest_scan_status"] is None
    assert items["ACADEMY"]["current_call_count"] == 1

    async with session_factory() as session:
        async with session.begin():
            session.add(
                SourceScanRun(
                    id=uuid4(),
                    source_code="SITRA",
                    trigger_type=ScanTrigger.MANUAL_API.value,
                    status=ScanRunStatus.RUNNING.value,
                    started_at=started_at + timedelta(minutes=2),
                )
            )

    running_response = await client.get("/api/sources/health")
    assert running_response.status_code == 200
    running_items = {
        item["source_code"]: item for item in running_response.json()["sources"]
    }
    assert running_items["SITRA"]["health"] == "RUNNING"
    assert running_items["SITRA"]["latest_scan_trigger"] == "MANUAL_API"
