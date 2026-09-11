import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.ui.dashboard_report_workspace import render_dashboard_report_workspace


def _preview_client() -> TestClient:
    app = create_app(
        Settings(
            dashboard_preview_mode=True,
            enabled_sources="STM,HAEAVUSTUKSIA,EURA,SITRA,ACADEMY",
        )
    )
    return TestClient(app)


def test_employee_dashboard_contains_report_workflow() -> None:
    response = _preview_client().get("/")

    assert response.status_code == 200
    html = response.text
    assert 'id="report-workspace"' in html
    assert "VakeHyvän rahoitusraportti" in html
    assert "Lisää raporttiin" in html
    assert "Valitse näkyvät varmistetut" in html
    assert "Muodosta raporttiluonnos" in html
    assert "Merkitse hyväksyntää varten" in html
    assert "Odottaa koordinaattorin hyväksyntää" in html
    assert "Miksi VakeHyvälle" in html
    assert "Hakuaika päättyy" in html
    assert "Koordinaattorin muistiinpanot" in html
    assert "Tulosta / PDF" in html


def test_preview_report_is_explicitly_local_and_not_sent() -> None:
    response = _preview_client().get("/")

    assert response.status_code == 200
    html = response.text
    assert "const previewMode = true;" in html
    assert "fixture-dataa, ei lähetetty" in html
    assert "ei lähetä raporttia sähköpostiin tai Teamsiin" in html


def test_report_workspace_preserves_existing_dashboard_layers() -> None:
    response = _preview_client().get("/")

    assert response.status_code == 200
    html = response.text
    assert 'id="theme-toggle"' in html
    assert 'id="certainty-filter"' in html
    assert "Haeavustuksia.fi" in html
    assert "EURA 2021" in html
    assert 'id="opportunity-list"' in html


def test_report_renderer_fails_loudly_if_dashboard_contract_changes() -> None:
    with pytest.raises(ValueError, match="sentinels missing"):
        render_dashboard_report_workspace(
            "<html><head></head><body></body></html>",
            preview_mode=False,
        )
