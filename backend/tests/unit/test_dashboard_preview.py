from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def _preview_client() -> TestClient:
    app = create_app(
        Settings(
            dashboard_preview_mode=True,
            enabled_sources="STM,HAEAVUSTUKSIA,EURA,SITRA,ACADEMY",
        )
    )
    return TestClient(app)


def test_preview_mode_serves_themed_dashboard_without_database() -> None:
    client = _preview_client()

    response = client.get("/")

    assert response.status_code == 200
    assert "Kehitysesikatselu · fixture-data" in response.text
    assert "Rahoitushakujen tilannekuva" in response.text
    assert 'id="theme-toggle"' in response.text
    assert "data:image/svg+xml;base64" in response.text


def test_preview_mode_exposes_five_source_read_contracts() -> None:
    client = _preview_client()

    all_calls = client.get("/api/funding-calls")
    assert all_calls.status_code == 200
    payload = all_calls.json()
    assert payload["total"] == 25

    review_calls = client.get(
        "/api/funding-calls",
        params={"relevance_status": "NEEDS_REVIEW"},
    )
    assert review_calls.status_code == 200
    assert review_calls.json()["total"] == 7

    eura = client.get("/api/funding-calls", params={"source_code": "eura"})
    assert eura.status_code == 200
    eura_payload = eura.json()
    assert eura_payload["total"] == 5
    assert all(item["source_code"] == "EURA" for item in eura_payload["items"])

    detail = client.get(f"/api/funding-calls/{eura_payload['items'][0]['id']}")
    assert detail.status_code == 200
    assert detail.json()["evidence"] == [{"kind": "preview_fixture", "synthetic": True}]

    health = client.get("/api/sources/health")
    assert health.status_code == 200
    sources = {item["source_code"]: item for item in health.json()["sources"]}
    assert set(sources) == {"STM", "HAEAVUSTUKSIA", "EURA", "SITRA", "ACADEMY"}
    assert sources["HAEAVUSTUKSIA"]["relevant_call_count"] == 5
    assert sources["HAEAVUSTUKSIA"]["review_call_count"] == 2
    assert sources["EURA"]["current_call_count"] == 5
    assert all(item["health"] == "HEALTHY" for item in sources.values())


def test_preview_readiness_is_explicitly_fixture_backed() -> None:
    response = _preview_client().get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "preview_ready",
        "service": "VakeVahti",
        "database": "bypassed",
        "storage": "fixture",
    }
