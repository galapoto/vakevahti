from app.ui.dashboard import DASHBOARD_HTML
from app.ui.dashboard_customization import render_dashboard_html


def test_employee_dashboard_uses_five_sources_and_vake_theme() -> None:
    html = render_dashboard_html(DASHBOARD_HTML)

    assert "HAEAVUSTUKSIA" in html
    assert "Haeavustuksia.fi" in html
    assert "EURA 2021" in html
    assert "--brand: #312783" in html
    assert "--good: #1FB578" in html
    assert "--danger: #D90066" in html
    assert 'data-source=\"HAEAVUSTUKSIA\"' in html
    assert 'data-source=\"EURA\"' in html


def test_employee_dashboard_localizes_scan_and_review_statuses() -> None:
    html = render_dashboard_html(DASHBOARD_HTML)

    assert 'String(value || "").trim().toUpperCase()' in html
    assert 'SUCCEEDED: "Onnistunut"' in html
    assert 'SUCCESS: "Onnistunut"' in html
    assert 'NEEDS_REVIEW: "Tarkistettava"' in html


def test_employee_dashboard_separates_confirmed_and_reviewable_calls() -> None:
    html = render_dashboard_html(DASHBOARD_HTML)

    assert "Varmistetusti sopivat haut" in html
    assert "varmistetut ja tarkistettavat rahoitushaut" in html
    assert "item.relevant_call_count || 0" in html
    assert "item.review_call_count || 0" in html
    assert "Miksi tarkistettava: " in html
    assert "Miksi tämä on tarkistettava" in html
    assert 'row.dataset.relevance = String(call.relevance_status || "")' in html
    assert '.opportunity[data-relevance="NEEDS_REVIEW"]' in html
    assert "vahvistettua · ${reviewCount} tarkistettavaa" in html


def test_employee_dashboard_is_persisted_read_only() -> None:
    html = render_dashboard_html(DASHBOARD_HTML)

    assert 'fetch("/api/sources/health")' in html
    assert "fetch(`/api/funding-calls?${params.toString()}`)" in html
    assert "/api/demo/stm-calls" not in html
    assert "relevanceReason(call)" in html
