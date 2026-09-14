import os
from datetime import UTC, datetime

import httpx
import pytest
from pydantic import HttpUrl
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.report_models import FundingReportDelivery
from app.domain.funding_call import FundingCallCandidate, RelevanceStatus
from app.main import create_app
from app.services.case_sync import ensure_cases_for_source_snapshot
from app.services.funding_cases import stable_case_id
from app.services.persistence import persist_candidates

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not TEST_DATABASE_URL,
        reason="TEST_DATABASE_URL is required for funding case integration tests.",
    ),
]

TRUNCATE_SQL = (
    "TRUNCATE TABLE funding_case_artifacts, funding_cases, "
    "funding_report_deliveries, funding_report_items, funding_reports, "
    "notification_outbox, source_scan_runs, funding_call_versions, funding_calls, "
    "source_states RESTART IDENTITY CASCADE"
)


def _candidate() -> FundingCallCandidate:
    return FundingCallCandidate(
        external_key="digital-care-2026",
        source_code="STM",
        title="Digitaalisten sote-palvelujen kehittämisrahoitus",
        source_url=HttpUrl("https://example.test/stm/digital-care-2026"),
        application_deadline_on=datetime(2026, 11, 30, tzinfo=UTC).date(),
        description_text="Rahoitus digitaalisten sote-palvelujen kehittämiseen.",
        relevance_status=RelevanceStatus.RELEVANT,
        relevance_reason="Haku tukee VakeHyvän digitaalisten palvelujen kehittämistä.",
    )


@pytest.fixture
async def case_api() -> tuple[
    httpx.AsyncClient,
    async_sessionmaker[AsyncSession],
]:
    assert TEST_DATABASE_URL is not None
    engine = create_async_engine(TEST_DATABASE_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.execute(text(TRUNCATE_SQL))

    observed_at = datetime(2026, 9, 14, 8, 0, tzinfo=UTC)
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

    settings = Settings(
        database_url=TEST_DATABASE_URL,
        enabled_sources="STM",
        enable_case_write_routes=True,
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


async def test_case_collects_cross_app_artifacts_and_queues_one_email_package(
    case_api: tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = case_api

    listed = await client.get("/api/cases")
    assert listed.status_code == 200
    cases = listed.json()
    assert len(cases) == 1
    case_id = cases[0]["id"]
    assert case_id == str(stable_case_id("STM", "digital-care-2026"))

    process_v1 = await client.post(
        f"/api/cases/{case_id}/artifacts",
        json={
            "source_app": "prosessikuvaus",
            "artifact_type": "process_description",
            "external_artifact_id": "process-42",
            "version": 1,
            "status": "draft",
            "title": "Hakuprosessin prosessikuvaus",
            "summary": "Luonnos hakemuksen valmisteluprosessista.",
            "content_url": "https://intra.example.test/process/42/v1",
        },
    )
    assert process_v1.status_code == 201

    process_v2 = await client.post(
        f"/api/cases/{case_id}/artifacts",
        json={
            "source_app": "prosessikuvaus",
            "artifact_type": "process_description",
            "external_artifact_id": "process-42",
            "version": 2,
            "status": "approved",
            "title": "Hakuprosessin prosessikuvaus",
            "summary": "Hyväksytty prosessi omistajineen ja päätöspisteineen.",
            "content_url": "https://intra.example.test/process/42/v2",
        },
    )
    assert process_v2.status_code == 201

    reporting = await client.post(
        f"/api/cases/{case_id}/artifacts",
        json={
            "source_app": "raportointi",
            "artifact_type": "reporting",
            "external_artifact_id": "reporting-19",
            "version": 1,
            "status": "approved",
            "title": "Rahoituksen raportointisuunnitelma",
            "summary": "KPI:t, raportointivastuut ja määräajat.",
            "content_text": "Raportointi tehdään kvartaalittain sovituilla mittareilla.",
        },
    )
    assert reporting.status_code == 201

    package_response = await client.get(f"/api/cases/{case_id}/email-package")
    assert package_response.status_code == 200
    package = package_response.json()
    assert package["subject"].startswith("VakeHyvä: Digitaalisten sote-palvelujen")
    assert "Prosessikuvaus" in package["body"]
    assert "Raportointi" in package["body"]
    assert "process/42/v2" in package["body"]
    assert "process/42/v1" not in package["body"]
    assert len(package["included_artifacts"]) == 2

    queued_response = await client.post(
        f"/api/cases/{case_id}/email",
        json={"recipient_emails": ["user@example.test", "owner@example.test"]},
    )
    assert queued_response.status_code == 202
    queued = queued_response.json()
    assert queued["delivery_status"] == "PENDING"
    assert queued["recipients"] == ["user@example.test", "owner@example.test"]

    async with session_factory() as session:
        delivery = (
            await session.scalars(
                select(FundingReportDelivery).where(
                    FundingReportDelivery.id == queued["delivery_id"]
                )
            )
        ).one()
        assert delivery.recipient_emails == ["user@example.test", "owner@example.test"]
        assert "Prosessikuvaus" in delivery.body_text
        assert "Raportointi" in delivery.body_text
        assert "#312783" in delivery.body_html


async def test_artifact_version_promotes_status_but_rejects_changed_content(
    case_api: tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = case_api
    case_id = (await client.get("/api/cases")).json()[0]["id"]
    content = {
        "source_app": "prosessikuvaus",
        "artifact_type": "process_description",
        "external_artifact_id": "process-idempotent",
        "version": 1,
        "title": "Prosessikuvaus",
        "summary": "Sama sisältö säilyttää saman version tunnisteen.",
    }

    draft = await client.post(
        f"/api/cases/{case_id}/artifacts",
        json={**content, "status": "draft"},
    )
    approved = await client.post(
        f"/api/cases/{case_id}/artifacts",
        json={**content, "status": "approved"},
    )
    repeated = await client.post(
        f"/api/cases/{case_id}/artifacts",
        json={**content, "status": "approved"},
    )
    changed = await client.post(
        f"/api/cases/{case_id}/artifacts",
        json={
            **content,
            "status": "approved",
            "summary": "Sama versionumero mutta eri sisältö.",
        },
    )

    assert draft.status_code == 201
    assert approved.status_code == 201
    assert approved.json()["id"] == draft.json()["id"]
    assert approved.json()["status"] == "APPROVED"
    assert approved.json()["approved_at"] is not None
    assert repeated.json()["id"] == draft.json()["id"]
    assert changed.status_code == 409


async def test_case_mutations_are_hidden_when_integration_boundary_is_disabled() -> None:
    assert TEST_DATABASE_URL is not None
    engine = create_async_engine(TEST_DATABASE_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    settings = Settings(
        database_url=TEST_DATABASE_URL,
        enabled_sources="STM",
        enable_case_write_routes=False,
    )
    application = create_app(settings, session_factory=session_factory)
    transport = httpx.ASGITransport(app=application)

    try:
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            response = await client.post(
                f"/api/cases/{stable_case_id('STM', 'missing')}/artifacts",
                json={
                    "source_app": "prosessikuvaus",
                    "artifact_type": "process_description",
                    "external_artifact_id": "blocked",
                    "title": "Blocked",
                },
            )
        assert response.status_code == 404
        assert response.json()["detail"] == "Case write routes are disabled."
    finally:
        await engine.dispose()
