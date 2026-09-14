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
    assert "Rahoituscase · VakeTomatti" in html
    assert "Prosessikuvaus" in html
    assert "Raportointi" in html
    assert "Lähetä sähköposti" in html
    assert "Poppins" in html
    assert "#312783" in html
    assert "#E6007E" in html


@pytest.mark.asyncio
async def test_preview_case_api_builds_cross_app_email_package() -> None:
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
