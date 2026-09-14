import os
from datetime import UTC, datetime

import httpx
import pytest
from pydantic import HttpUrl
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.domain.funding_call import FundingCallCandidate, RelevanceStatus
from app.main import create_app
from app.services.case_sync import ensure_cases_for_source_snapshot
from app.services.persistence import persist_candidates

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not TEST_DATABASE_URL,
        reason="TEST_DATABASE_URL is required for case automation integration tests.",
    ),
]

TRUNCATE_SQL = (
    "TRUNCATE TABLE funding_case_tasks, funding_case_artifacts, funding_cases, "
    "funding_report_deliveries, funding_report_items, funding_reports, "
    "notification_outbox, source_scan_runs, funding_call_versions, funding_calls, "
    "source_states RESTART IDENTITY CASCADE"
)


def _candidate() -> FundingCallCandidate:
    return FundingCallCandidate(
        external_key="automation-case-2026",
        source_code="STM",
        title="Automaattisen case-polun kehittämisrahoitus",
        source_url=HttpUrl("https://example.test/stm/automation-case-2026"),
        application_deadline_on=datetime(2026, 12, 15, tzinfo=UTC).date(),
        description_text="Rahoitus VakeHyvän kehittämistyöhön.",
        relevance_status=RelevanceStatus.RELEVANT,
        relevance_reason="Haku tukee VakeHyvän kehittämistavoitteita.",
    )


@pytest.fixture
async def automation_api() -> httpx.AsyncClient:
    assert TEST_DATABASE_URL is not None
    engine = create_async_engine(TEST_DATABASE_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.execute(text(TRUNCATE_SQL))

    observed_at = datetime(2026, 9, 14, 10, 0, tzinfo=UTC)
    async with session_factory() as session:
        async with session.begin():
            await persist_candidates(
                session,
                [_candidate()],
                observed_at=observed_at,
            )
            await ensure_cases_for_source_snapshot(
                session,
                source_code="STM",
                observed_at=observed_at,
            )

    app = create_app(
        Settings(
            database_url=TEST_DATABASE_URL,
            enabled_sources="STM",
            enable_case_write_routes=True,
        ),
        session_factory=session_factory,
    )
    transport = httpx.ASGITransport(app=app)

    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            yield client
    finally:
        async with engine.begin() as connection:
            await connection.execute(text(TRUNCATE_SQL))
        await engine.dispose()


def _tasks_by_key(case: dict[str, object]) -> dict[str, dict[str, object]]:
    tasks = case["tasks"]
    assert isinstance(tasks, list)
    return {str(task["task_key"]): task for task in tasks if isinstance(task, dict)}


async def test_case_tasks_advance_automatically_when_artifacts_are_approved(
    automation_api: httpx.AsyncClient,
) -> None:
    listed = await automation_api.get("/api/cases")
    assert listed.status_code == 200
    case = listed.json()[0]
    case_id = case["id"]
    tasks = _tasks_by_key(case)

    assert tasks["ELIGIBILITY_REVIEW"]["status"] == "COMPLETED"
    assert tasks["PROCESS_DESCRIPTION"]["status"] == "OPEN"
    assert tasks["REPORTING_PLAN"]["status"] == "OPEN"
    assert tasks["FUNDING_REPORT_REVIEW"]["status"] == "OPEN"
    assert case["next_action"] == "Valmistele prosessikuvaus"
    assert tasks["PROCESS_DESCRIPTION"]["due_on"] == "2026-12-15"

    process = await automation_api.post(
        f"/api/cases/{case_id}/artifacts",
        json={
            "source_app": "prosessikuvaus",
            "artifact_type": "process_description",
            "external_artifact_id": "automation-process",
            "version": 1,
            "status": "approved",
            "title": "Hakemuksen prosessikuvaus",
            "summary": "Hyväksytty prosessikuvaus.",
        },
    )
    assert process.status_code == 201

    after_process = (await automation_api.get(f"/api/cases/{case_id}")).json()
    tasks = _tasks_by_key(after_process)
    assert tasks["PROCESS_DESCRIPTION"]["status"] == "COMPLETED"
    assert after_process["next_action"] == "Valmistele raportointisuunnitelma"

    reporting = await automation_api.post(
        f"/api/cases/{case_id}/artifacts",
        json={
            "source_app": "raportointi",
            "artifact_type": "reporting",
            "external_artifact_id": "automation-reporting",
            "version": 1,
            "status": "approved",
            "title": "Rahoituksen raportointisuunnitelma",
            "summary": "Hyväksytty raportointisuunnitelma.",
        },
    )
    assert reporting.status_code == 201

    after_reporting = (await automation_api.get(f"/api/cases/{case_id}")).json()
    tasks = _tasks_by_key(after_reporting)
    assert tasks["REPORTING_PLAN"]["status"] == "COMPLETED"
    assert tasks["FUNDING_REPORT_REVIEW"]["status"] == "OPEN"
    assert after_reporting["next_action"] == "Tarkista rahoitusraportti ja sähköpostipaketti"
