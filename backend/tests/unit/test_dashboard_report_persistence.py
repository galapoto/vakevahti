from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.ui.dashboard_report_persistence import render_dashboard_report_persistence


def test_preview_dashboard_exposes_real_save_and_submit_controls() -> None:
    app = create_app(
        Settings(
            dashboard_preview_mode=True,
            enabled_sources="STM,HAEAVUSTUKSIA,EURA,SITRA,ACADEMY",
        )
    )
    response = TestClient(app).get("/")

    assert response.status_code == 200
    html = response.text
    assert 'id="report-save"' in html
    assert "Tallenna luonnos" in html
    assert 'fetch("/api/reports"' in html
    assert "/submit" in html
    assert "Testiluonnos tallennettu" in html
    assert "fixture-muistiin" in html


def test_report_persistence_hidden_without_safe_write_api() -> None:
    app = create_app(Settings(dashboard_preview_mode=False, enable_report_write_routes=False))
    response = TestClient(app).get("/")

    assert response.status_code == 200
    assert 'id="report-save"' not in response.text


def test_renderer_is_noop_when_disabled() -> None:
    original = "<html><head></head><body><main></main></body></html>"

    assert (
        render_dashboard_report_persistence(
            original,
            enabled=False,
            preview_mode=False,
        )
        == original
    )
