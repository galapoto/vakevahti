from datetime import date

import httpx
import pytest

from app.config import Settings
from app.main import create_app
from app.services.case_requirements import (
    RequirementCertainty,
    RequirementSpec,
    derive_requirement_specs,
)


def _by_key(specs: list[RequirementSpec]) -> dict[str, RequirementSpec]:
    return {spec.requirement_key: spec for spec in specs}


def test_keyword_evidence_is_reviewable_not_promoted_to_confirmed() -> None:
    specs = derive_requirement_specs(
        source_url="https://example.test/call",
        relevance_status="RELEVANT",
        relevance_reason="Hyvinvointialue kuuluu hakijaryhmään.",
        description_text=(
            "Hakuilmoitus kuvaa budjetin, pakolliset liitteet ja raportointivaatimukset."
        ),
        evidence=[],
        application_deadline_on=date(2026, 11, 30),
        application_deadline_at=None,
    )
    by_key = _by_key(specs)

    assert by_key["ELIGIBILITY"].certainty == RequirementCertainty.EVIDENCE_FOUND
    assert "ei yksin vahvista hakukelpoisuutta" in by_key["ELIGIBILITY"].statement
    assert by_key["APPLICATION_DEADLINE"].certainty == RequirementCertainty.CONFIRMED
    assert by_key["REQUIRED_DOCUMENTS"].certainty == RequirementCertainty.EVIDENCE_FOUND
    assert by_key["BUDGET_AND_COFUNDING"].certainty == RequirementCertainty.EVIDENCE_FOUND
    assert by_key["REPORTING_OBLIGATIONS"].certainty == RequirementCertainty.EVIDENCE_FOUND
    assert by_key["APPROVALS_AND_DECISIONS"].certainty == RequirementCertainty.REVIEW_REQUIRED
    assert "Tarkista täsmällinen vaatimus" in by_key["BUDGET_AND_COFUNDING"].statement


def test_missing_source_conditions_remain_review_required() -> None:
    specs = derive_requirement_specs(
        source_url="https://example.test/call",
        relevance_status="NEEDS_REVIEW",
        relevance_reason="Hakukelpoisuus jäi epäselväksi.",
        description_text="Yleinen kehittämishaku.",
        evidence=[],
        application_deadline_on=None,
        application_deadline_at=None,
    )
    by_key = _by_key(specs)

    assert by_key["ELIGIBILITY"].certainty == RequirementCertainty.REVIEW_REQUIRED
    assert by_key["APPLICATION_DEADLINE"].certainty == RequirementCertainty.REVIEW_REQUIRED
    assert by_key["REQUIRED_DOCUMENTS"].certainty == RequirementCertainty.REVIEW_REQUIRED
    assert by_key["BUDGET_AND_COFUNDING"].certainty == RequirementCertainty.REVIEW_REQUIRED
    assert by_key["REPORTING_OBLIGATIONS"].certainty == RequirementCertainty.REVIEW_REQUIRED


@pytest.mark.asyncio
async def test_preview_case_exposes_requirement_intelligence_and_workspace() -> None:
    application = create_app(
        Settings(
            dashboard_preview_mode=True,
            enabled_sources="STM,HAEAVUSTUKSIA,EURA,SITRA,ACADEMY",
        )
    )
    transport = httpx.ASGITransport(app=application)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        dashboard = await client.get("/")
        cases = (await client.get("/api/cases")).json()
        case_id = cases[0]["id"]
        response = await client.get(f"/api/cases/{case_id}/requirements")

    assert dashboard.status_code == 200
    assert 'id="case-requirements-card"' in dashboard.text
    assert "Rahoitusvaatimukset" in dashboard.text
    assert response.status_code == 200
    requirements = response.json()
    assert len(requirements) == 6
    by_key = {item["requirement_key"]: item for item in requirements}
    assert by_key["ELIGIBILITY"]["certainty"] == "EVIDENCE_FOUND"
    assert by_key["APPLICATION_DEADLINE"]["certainty"] == "CONFIRMED"
    assert by_key["REQUIRED_DOCUMENTS"]["certainty"] == "EVIDENCE_FOUND"
    assert by_key["BUDGET_AND_COFUNDING"]["certainty"] == "EVIDENCE_FOUND"
    assert by_key["REPORTING_OBLIGATIONS"]["certainty"] == "EVIDENCE_FOUND"
    assert by_key["APPROVALS_AND_DECISIONS"]["certainty"] == "REVIEW_REQUIRED"
