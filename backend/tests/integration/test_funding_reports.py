import os
from datetime import UTC, datetime, timedelta
from uuid import UUID

import httpx
import pytest
from pydantic import HttpUrl
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.models import FundingCallRecord
from app.db.report_models import FundingReport, FundingReportApprovalEvent
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


async def _create_and_submit_report(
    client: httpx.AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> tuple[str, list[int]]:
    call_ids = await seed_calls(session_factory)
    created = await client.post(
        "/api/reports",
        json={
            "title": "Approval workflow report",
            "notes": "Coordinator review requested.",
            "email_subject": "Funding review",
            "email_body": "Please review the attached funding summary.",
            "recipient_emails": ["coordinator@example.test"],
            "funding_call_ids": call_ids,
        },
    )
    assert created.status_code == 201
    report_id = created.json()["id"]
    submitted = await client.post(f"/api/reports/{report_id}/submit")
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "WAITING_APPROVAL"
    return report_id, call_ids


async def test_coordinator_approval_is_immutable_audited_and_retry_safe(
    report_api: tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = report_api
    report_id, call_ids = await _create_and_submit_report(client, session_factory)

    decision = {
        "decision": "APPROVE",
        "actor_id": "coordinator-123",
        "actor_display_name": "Test Coordinator",
        "comment": "Reviewed against the source evidence.",
    }
    approved = await client.post(f"/api/reports/{report_id}/decision", json=decision)
    assert approved.status_code == 200
    payload = approved.json()
    assert payload["status"] == "APPROVED"
    assert len(payload["approval_events"]) == 1
    event = payload["approval_events"][0]
    assert event["decision"] == "APPROVE"
    assert event["actor_id"] == "coordinator-123"
    assert event["actor_source"] == "CLIENT_ASSERTED"
    assert len(event["content_hash"]) == 64
    assert event["snapshot"]["title"] == "Approval workflow report"
    assert [item["funding_call_id"] for item in event["snapshot"]["items"]] == call_ids

    repeated = await client.post(f"/api/reports/{report_id}/decision", json=decision)
    assert repeated.status_code == 200
    assert repeated.json()["approval_events"] == payload["approval_events"]

    edit = await client.patch(
        f"/api/reports/{report_id}",
        json={"notes": "This must not mutate an approved report."},
    )
    assert edit.status_code == 409

    async with session_factory() as session:
        events = list(
            (
                await session.scalars(
                    select(FundingReportApprovalEvent).where(
                        FundingReportApprovalEvent.report_id == report_id
                    )
                )
            ).all()
        )
        assert len(events) == 1
        assert events[0].snapshot["email_subject"] == "Funding review"


async def test_return_reject_and_resubmission_require_explicit_state_transitions(
    report_api: tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = report_api
    report_id, _ = await _create_and_submit_report(client, session_factory)

    missing_comment = await client.post(
        f"/api/reports/{report_id}/decision",
        json={"decision": "RETURN_FOR_EDIT", "actor_id": "coordinator-123"},
    )
    assert missing_comment.status_code == 422

    returned = await client.post(
        f"/api/reports/{report_id}/decision",
        json={
            "decision": "RETURN_FOR_EDIT",
            "actor_id": "coordinator-123",
            "comment": "Clarify the implementation owner before approval.",
        },
    )
    assert returned.status_code == 200
    assert returned.json()["status"] == "DRAFT"
    assert returned.json()["submitted_for_approval_at"] is None

    edited = await client.patch(
        f"/api/reports/{report_id}",
        json={"notes": "Owner: Digital development team."},
    )
    assert edited.status_code == 200
    resubmitted = await client.post(f"/api/reports/{report_id}/submit")
    assert resubmitted.status_code == 200

    rejected = await client.post(
        f"/api/reports/{report_id}/decision",
        json={
            "decision": "REJECT",
            "actor_id": "coordinator-456",
            "actor_display_name": "Second Coordinator",
            "comment": "Do not proceed with this funding opportunity.",
        },
    )
    assert rejected.status_code == 200
    payload = rejected.json()
    assert payload["status"] == "REJECTED"
    assert [event["decision"] for event in payload["approval_events"]] == [
        "RETURN_FOR_EDIT",
        "REJECT",
    ]
    first_hash = payload["approval_events"][0]["content_hash"]
    second_hash = payload["approval_events"][1]["content_hash"]
    assert first_hash != second_hash

    blocked_resubmit = await client.post(f"/api/reports/{report_id}/submit")
    assert blocked_resubmit.status_code == 409

    reworked = await client.patch(
        f"/api/reports/{report_id}",
        json={"notes": "Reworked after rejection."},
    )
    assert reworked.status_code == 200
    assert reworked.json()["status"] == "DRAFT"


async def test_coordinator_queue_filters_waiting_reports(
    report_api: tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = report_api
    report_id, _ = await _create_and_submit_report(client, session_factory)

    queue = await client.get(
        "/api/reports",
        params={"status": "WAITING_APPROVAL", "limit": 10, "offset": 0},
    )
    assert queue.status_code == 200
    payload = queue.json()
    assert payload["total"] == 1
    assert payload["items"][0]["id"] == report_id
    assert payload["items"][0]["status"] == "WAITING_APPROVAL"

    approved = await client.post(
        f"/api/reports/{report_id}/decision",
        json={"decision": "APPROVE", "actor_id": "queue-coordinator"},
    )
    assert approved.status_code == 200

    after = await client.get("/api/reports", params={"status": "WAITING_APPROVAL"})
    assert after.status_code == 200
    assert after.json()["total"] == 0


async def test_approved_report_revision_creates_one_immutable_successor_version(
    report_api: tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = report_api
    report_id, call_ids = await _create_and_submit_report(client, session_factory)

    approved = await client.post(
        f"/api/reports/{report_id}/decision",
        json={"decision": "APPROVE", "actor_id": "version-coordinator"},
    )
    assert approved.status_code == 200
    approved_payload = approved.json()
    assert approved_payload["version_number"] == 1
    assert approved_payload["supersedes_report_id"] is None

    revised = await client.post(f"/api/reports/{report_id}/revise")
    assert revised.status_code == 200
    successor = revised.json()
    assert successor["status"] == "DRAFT"
    assert successor["version_number"] == 2
    assert successor["supersedes_report_id"] == report_id
    assert successor["approval_events"] == []
    assert [item["funding_call_id"] for item in successor["items"]] == call_ids

    repeated = await client.post(f"/api/reports/{report_id}/revise")
    assert repeated.status_code == 200
    assert repeated.json()["id"] == successor["id"]

    original = await client.get(f"/api/reports/{report_id}")
    assert original.status_code == 200
    original_payload = original.json()
    assert original_payload["status"] == "APPROVED"
    assert original_payload["version_number"] == 1
    assert len(original_payload["approval_events"]) == 1

    edited_successor = await client.patch(
        f"/api/reports/{successor['id']}",
        json={"notes": "Version two has a revised implementation owner."},
    )
    assert edited_successor.status_code == 200
    assert edited_successor.json()["version_number"] == 2

    async with session_factory() as session:
        successor_count = await session.scalar(
            select(func.count()).select_from(FundingReport).where(
                FundingReport.supersedes_report_id == UUID(report_id)
            )
        )
        assert successor_count == 1
