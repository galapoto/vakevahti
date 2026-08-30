from fastapi.testclient import TestClient

from app.main import app


def test_dashboard_is_served() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "VakeVahti" in response.text
    assert "Rahoitushakujen tilannekuva" in response.text
    assert "Tallennettu tilannekuva" in response.text


def test_dashboard_uses_persisted_read_contracts_not_live_demo_scan() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "/api/sources/health" in response.text
    assert "/api/funding-calls" in response.text
    assert "/api/demo/stm-calls" not in response.text
    assert "Kehitysdemo" not in response.text


def test_liveness_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "VakeVahti"}
