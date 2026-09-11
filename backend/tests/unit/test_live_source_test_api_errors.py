from fastapi.testclient import TestClient

import app.api.live_test as live_test_module
from app.config import Settings
from app.main import create_app


class FailingScanner:
    source_code = "STM"

    async def scan(self):
        raise RuntimeError("source unavailable")


def test_live_test_unknown_source_returns_404() -> None:
    client = TestClient(create_app(Settings(enable_live_test_routes=True)))

    response = client.post("/api/test/live-sources/UNKNOWN")

    assert response.status_code == 404
    assert "Unknown funding source" in response.json()["detail"]


def test_live_test_scanner_failure_returns_diagnostic_502(monkeypatch) -> None:
    def fake_build_scanners(settings, source_codes=None):
        del settings, source_codes
        return (FailingScanner(),)

    monkeypatch.setattr(live_test_module, "build_scanners", fake_build_scanners)
    client = TestClient(create_app(Settings(enable_live_test_routes=True)))

    response = client.post("/api/test/live-sources/STM")

    assert response.status_code == 502
    assert response.json()["detail"] == {
        "source_code": "STM",
        "error_type": "RuntimeError",
        "message": "source unavailable",
    }
