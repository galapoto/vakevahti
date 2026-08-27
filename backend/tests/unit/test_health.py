from fastapi.testclient import TestClient

from app.main import app


def test_dashboard_is_served() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "VakeVahti" in response.text
    assert "Kehitysdemo" in response.text


def test_liveness_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "VakeVahti"}
