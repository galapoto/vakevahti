from app.ui.dashboard import DASHBOARD_HTML
from app.ui.dashboard_customization import render_dashboard_html
from app.ui.dashboard_date_precision import render_dashboard_date_precision


def render_dashboard() -> str:
    return render_dashboard_date_precision(render_dashboard_html(DASHBOARD_HTML))


def test_date_only_deadline_does_not_invent_a_clock_time() -> None:
    html = render_dashboard()

    assert "function formatDeadline(exactValue, dateOnlyValue)" in html
    assert "hasExactTime" in html
    assert 'new Intl.DateTimeFormat("fi-FI", { dateStyle: "medium" }).format(date)' in html
    assert "formatDeadline(call.application_deadline_at, call.application_deadline_on)" in html
    assert "application_deadline_at || call.application_deadline_on" not in html


def test_date_only_opening_date_is_visible_in_detail_view() -> None:
    html = render_dashboard()

    assert "function formatDateFact(exactValue, dateOnlyValue)" in html
    assert (
        "formatDateFact(detail.application_opens_at, detail.application_opens_on)"
        in html
    )
