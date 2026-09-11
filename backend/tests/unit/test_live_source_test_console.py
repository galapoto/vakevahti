from fastapi.testclient import TestClient

import app.api.live_test as live_test_module
from app.config import Settings
from app.domain.funding_call import FundingCallCandidate, RelevanceStatus
from app.main import create_app


class FakeScanner:
    source_code = "STM"

    async def scan(self) -> list[FundingCallCandidate]:
        return [
            FundingCallCandidate(
                external_key="confirmed",
                source_code="STM",
                title="Confirmed call",
                source_url="https://example.com/confirmed",
                relevance_status=RelevanceStatus.RELEVANT,
                relevance_reason="Explicit wellbeing-area eligibility.",
            ),
            FundingCallCandidate(
                external_key="review",
                source_code="STM",
                title="Review call",
                source_url="https://example.com/review",
                relevance_status=RelevanceStatus.NEEDS_REVIEW,
                relevance_reason="Eligibility wording needs review.",
            ),
            FundingCallCandidate(
                external_key="excluded",
                source_code="STM",
                title="Excluded call",
                source_url="https://example.com/excluded",
                relevance_status=RelevanceStatus.NOT_RELEVANT,
                relevance_reason="Applicant group excludes VakeHyvä.",
            ),
        ]


def test_live_test_routes_are_disabled_by_default() -> None:
    client = TestClient(create_app(Settings(enable_live_test_routes=False)))

    assert client.get("/test/live-sources").status_code == 404
    assert client.get("/api/test/live-sources").status_code == 404


def test_live_test_console_runs_scanner_without_persistence(monkeypatch) -> None:
    def fake_build_scanners(
        settings: Settings,
        source_codes: list[str] | None = None,
    ) -> tuple[FakeScanner, ...]:
        del settings
        assert source_codes == ["STM"]
        return (FakeScanner(),)

    monkeypatch.setattr(live_test_module, "build_scanners", fake_build_scanners)
    client = TestClient(create_app(Settings(enable_live_test_routes=True)))

    page = client.get("/test/live-sources")
    assert page.status_code == 200
    assert "VakeVahti · Live-lähdetesti" in page.text
    assert "ei tallenna tuloksia tietokantaan" in page.text

    catalog = client.get("/api/test/live-sources")
    assert catalog.status_code == 200
    assert {item["code"] for item in catalog.json()["sources"]} == {
        "STM",
        "HAEAVUSTUKSIA",
        "EURA",
        "SITRA",
        "ACADEMY",
    }

    response = client.post("/api/test/live-sources/STM")
    assert response.status_code == 200
    payload = response.json()
    assert payload["source_code"] == "STM"
    assert payload["total"] == 3
    assert payload["distribution"] == {
        "relevant": 1,
        "needs_review": 1,
        "not_relevant": 1,
    }
    assert [item["relevance_status"] for item in payload["items"]] == [
        "RELEVANT",
        "NEEDS_REVIEW",
        "NOT_RELEVANT",
    ]
