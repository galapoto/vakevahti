from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app, create_app


class FakeSession:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def execute(self, statement):
        del statement
        if self.fail:
            raise ConnectionError("database unavailable")
        return None


class FakeSessionFactory:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail

    def __call__(self) -> FakeSession:
        return FakeSession(fail=self.fail)


def test_dashboard_is_served() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "VakeVahti" in response.text
    assert "VakeHyvälle sopivat rahoitushaut" in response.text
    assert "Kehitysdemo" not in response.text


def test_liveness_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "VakeVahti"}


def test_readiness_reports_database_ready() -> None:
    test_app = create_app(
        Settings(),
        session_factory=FakeSessionFactory(),  # type: ignore[arg-type]
    )
    client = TestClient(test_app)

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "service": "VakeVahti",
        "database": "ok",
    }


def test_readiness_reports_database_unavailable_without_hiding_liveness() -> None:
    test_app = create_app(
        Settings(),
        session_factory=FakeSessionFactory(fail=True),  # type: ignore[arg-type]
    )
    client = TestClient(test_app)

    readiness = client.get("/health/ready")
    liveness = client.get("/health/live")

    assert readiness.status_code == 503
    assert readiness.json() == {
        "status": "not_ready",
        "service": "VakeVahti",
        "database": "unavailable",
        "error_type": "ConnectionError",
    }
    assert liveness.status_code == 200
