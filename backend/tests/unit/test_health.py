from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def _normal_client() -> TestClient:
    app = create_app(Settings(dashboard_preview_mode=False))
    return TestClient(app)


def test_dashboard_is_served() -> None:
    client = _normal_client()

    response = client.get("/")

    assert response.status_code == 200
    assert "VakeVahti" in response.text
    assert "Rahoitushakujen tilannekuva" in response.text
    assert "Tallennettu tilannekuva" in response.text


def test_dashboard_uses_persisted_read_contracts_not_live_demo_scan() -> None:
    client = _normal_client()

    response = client.get("/")

    assert response.status_code == 200
    assert "/api/sources/health" in response.text
    assert "/api/funding-calls" in response.text
    assert "/api/demo/stm-calls" not in response.text
    assert "Kehitysdemo" not in response.text


def test_dashboard_cards_are_interactive_source_aware_and_linked() -> None:
    client = _normal_client()

    response = client.get("/")

    assert response.status_code == 200
    html = response.text

    # KPI cards are real buttons with dashboard navigation actions.
    assert 'id="kpi-current"' in html
    assert 'id="kpi-healthy"' in html
    assert 'id="kpi-attention"' in html
    assert 'id="kpi-latest"' in html
    assert "applySourceFilter" in html
    assert "flashCards" in html

    # Source cards have distinct source identities and explicit source destinations.
    assert 'data-source="STM"' in html
    assert 'data-source="SITRA"' in html
    assert 'data-source="ACADEMY"' in html
    assert "https://stm.fi/vuoden-2026-valtionavustushaut" in html
    assert "https://asiointi.sitra.fi/" in html
    assert "https://www.aka.fi/tutkimusrahoitus/hae-rahoitusta/haut/" in html

    # Funding-call rows expose a direct persisted source URL as well as expandable detail.
    assert "row-source-link" in html
    assert "call.source_url" in html
    assert 'aria-controls' in html


def test_liveness_endpoint() -> None:
    client = _normal_client()

    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "VakeVahti"}
