import httpx
import pytest

from app.config import Settings
from app.main import create_app


@pytest.mark.asyncio
async def test_preview_dashboard_contains_unified_case_workspace() -> None:
    settings = Settings(
        dashboard_preview_mode=True,
        enabled_sources="STM,HAEAVUSTUKSIA,EURA,SITRA,ACADEMY",
    )
    application = create_app(settings)
    transport = httpx.ASGITransport(app=application)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/")

    assert response.status_code == 200
    html = response.text
    assert 'id="funding-case-workspace"' in html
    assert 'id="case-automation-card"' in html
    assert "Automaattinen tehtävälista" in html
    assert "Rahoituscase · VakeTomatti" in html
    assert "Prosessikuvaus" in html
    assert "Raportointi" in html
    assert "Lähetä sähköposti" in html
    assert "Poppins" in html
    assert "#312783" in html
    assert "#E6007E" in html


@pytest.mark.asyncio
async def test_preview_case_api_builds_cross_app_email_package_and_task_plan() -> None:
    settings = Settings(
        dashboard_preview_mode=True,
        enabled_sources="STM,HAEAVUSTUKSIA,EURA,SITRA,ACADEMY",
    )
    application = create_app(settings)
    transport = httpx.ASGITransport(app=application)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        cases_response = await client.get("/api/cases")
        assert cases_response.status_code == 200
        cases = cases_response.json()
        assert cases
        case = cases[0]
        artifact_types = {artifact["artifact_type"] for artifact in case["artifacts"]}
        assert {"PROCESS_DESCRIPTION", "REPORTING", "FUNDING_REPORT"} <= artifact_types
        task_by_key = {task["task_key"]: task for task in case["tasks"]}
        assert task_by_key["ELIGIBILITY_REVIEW"]["status"] == "COMPLETED"
        assert task_by_key["PROCESS_DESCRIPTION"]["status"] == "COMPLETED"
        assert task_by_key["REPORTING_PLAN"]["status"] == "COMPLETED"
        assert task_by_key["FUNDING_REPORT_REVIEW"]["status"] == "OPEN"
        assert case["next_action"] == "Tarkista rahoitusraportti ja sähköpostipaketti"

        package_response = await client.get(f"/api/cases/{case['id']}/email-package")
        assert package_response.status_code == 200
        package = package_response.json()
        assert package["subject"].startswith("VakeHyvä:")
        assert "Prosessikuvaus" in package["body"]
        assert "Raportointi" in package["body"]

        queued_response = await client.post(
            f"/api/cases/{case['id']}/email",
            json={
                "recipient_emails": ["user@example.test", "owner@example.test"],
                "subject": package["subject"],
                "body": package["body"],
                "artifact_ids": [artifact["id"] for artifact in package["included_artifacts"]],
            },
        )

    assert queued_response.status_code == 202
    queued = queued_response.json()
    assert queued["delivery_status"] == "PREVIEW_QUEUED"
    assert queued["recipients"] == ["user@example.test", "owner@example.test"]


@pytest.mark.asyncio
async def test_preview_review_case_keeps_eligibility_as_first_automated_action() -> None:
    settings = Settings(
        dashboard_preview_mode=True,
        enabled_sources="STM,HAEAVUSTUKSIA,EURA,SITRA,ACADEMY",
    )
    application = create_app(settings)
    transport = httpx.ASGITransport(app=application)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/cases")

    review_case = next(
        case
        for case in response.json()
        if case["funding_call"]["relevance_status"] == "NEEDS_REVIEW"
    )
    task_by_key = {task["task_key"]: task for task in review_case["tasks"]}
    assert task_by_key["ELIGIBILITY_REVIEW"]["status"] == "OPEN"
    assert review_case["next_action"] == "Varmista hakukelpoisuus"
