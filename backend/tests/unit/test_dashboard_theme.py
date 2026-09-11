from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def _client(*, preview: bool = False) -> TestClient:
    app = create_app(
        Settings(
            dashboard_preview_mode=preview,
            enabled_sources="STM,HAEAVUSTUKSIA,EURA,SITRA,ACADEMY",
        )
    )
    return TestClient(app)


def test_dashboard_uses_restored_vake_palette_logo_and_theme_toggle() -> None:
    response = _client().get("/")

    assert response.status_code == 200
    html = response.text.lower()
    assert 'id="theme-toggle"' in html
    assert "vakevahti-theme" in html
    assert 'html[data-theme="dark"]' in html
    assert "#312783" in html
    assert "#76cbf3" in html
    assert "#00983a" in html
    assert "#74b72b" in html
    assert "#e6007e" in html
    assert "#ea5297" in html
    assert "data:image/svg+xml;base64" in html


def test_preview_badge_survives_theme_and_certainty_injection() -> None:
    response = _client(preview=True).get("/")

    assert response.status_code == 200
    assert "Kehitysesikatselu · fixture-data" in response.text
    assert 'id="theme-toggle"' in response.text
    assert "Varmistetut" in response.text
    assert "Tarkistettavat" in response.text
