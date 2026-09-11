from app.ui.dashboard import DASHBOARD_HTML
from app.ui.dashboard_certainty_filter import render_dashboard_certainty_filter
from app.ui.dashboard_customization import render_dashboard_html
from app.ui.dashboard_date_precision import render_dashboard_date_precision


def render_dashboard() -> str:
    customized = render_dashboard_html(DASHBOARD_HTML)
    precise = render_dashboard_date_precision(customized)
    return render_dashboard_certainty_filter(precise)


def test_dashboard_has_operator_certainty_filter() -> None:
    html = render_dashboard()

    assert 'id="relevance-filter"' in html
    assert '<option value="RELEVANT">Varmistetut</option>' in html
    assert '<option value="NEEDS_REVIEW">Tarkistettavat</option>' in html
    assert 'relevance: ""' in html
    assert 'params.set("relevance_status", state.relevance)' in html


def test_confirmed_kpi_selects_confirmed_filter() -> None:
    html = render_dashboard()

    assert 'state.relevance = "RELEVANT"' in html
    assert 'elements.relevanceFilter.value = "RELEVANT"' in html
    assert 'applySourceFilter("")' in html


def test_dashboard_loads_all_persisted_result_pages() -> None:
    html = render_dashboard()

    assert "const pageSize = 100;" in html
    assert "while (expectedTotal === null || offset < expectedTotal)" in html
    assert 'offset: String(offset)' in html
    assert "calls.push(...pageItems);" in html
    assert 'throw new Error("Funding API pagination stopped before the advertised total.")' in html


def test_dashboard_filter_remains_persisted_read_only() -> None:
    html = render_dashboard()

    assert "scan-source" not in html
    assert "/api/demo/stm-calls" not in html
    assert "relevance_status" in html
