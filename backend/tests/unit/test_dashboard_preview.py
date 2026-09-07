from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def _preview_client() -> TestClient:
    app = create_app(
        Settings(
            dashboard_preview_mode=True,
            enabled_sources="STM,SITRA,ACADEMY",
        )
    )
    return TestClient(app)


def test_preview_mode_serves_dashboard_without_database() -> None:
    client = _preview_client()

    response = client.get("/")

    assert response.status_code == 200
    assert "Kehitysesikatselu · fixture-data" in response.text
    assert "Rahoitushakujen tilannekuva" in response.text


def test_preview_mode_exposes_same_read_contracts_without_postgresql() -> None:
    client = _preview_client()

    all_calls = client.get("/api/funding-calls")
    assert all_calls.status_code == 200
    payload = all_calls.json()
    assert payload["total"] == 17

    sitra = client.get("/api/funding-calls", params={"source_code": "sitra"})
    assert sitra.status_code == 200
    sitra_payload = sitra.json()
    assert sitra_payload["total"] == 1
    assert sitra_payload["items"][0]["source_code"] == "SITRA"

    detail = client.get(f"/api/funding-calls/{sitra_payload['items'][0]['id']}")
    assert detail.status_code == 200
    assert detail.json()["evidence"] == [{"kind": "preview_fixture", "synthetic": True}]

    health = client.get("/api/sources/health")
    assert health.status_code == 200
    sources = {item["source_code"]: item for item in health.json()["sources"]}
    assert sources["STM"]["current_call_count"] == 9
    assert sources["SITRA"]["current_call_count"] == 1
    assert sources["ACADEMY"]["current_call_count"] == 7
    assert all(item["health"] == "HEALTHY" for item in sources.values())
