from datetime import UTC, datetime
from uuid import uuid4

from app.api.report_schemas import (
    FundingReportOrigin,
    FundingReportResponse,
    FundingReportStatus,
)
from app.services.report_email_delivery import retry_delay_minutes
from app.services.report_email_renderer import render_report_email_html


def _report() -> FundingReportResponse:
    return FundingReportResponse(
        id=uuid4(),
        title="VakeVahti · STM · Digipalvelujen kehittämisrahoitus",
        status=FundingReportStatus.DRAFT,
        origin=FundingReportOrigin.AUTOMATED,
        automation_key="scan-cycle:test",
        notes="Automaattinen raportti",
        email_subject="VakeVahti: Uusi löydös – Digipalvelujen kehittämisrahoitus",
        email_body=(
            "1. Digipalvelujen kehittämisrahoitus\n"
            "Miksi VakeHyvälle: tukee digitaalisten palvelujen kehittämistä."
        ),
        recipient_emails=["coordinator@example.test"],
        created_at=datetime(2026, 9, 11, 10, 0, tzinfo=UTC),
        updated_at=datetime(2026, 9, 11, 10, 0, tzinfo=UTC),
        submitted_for_approval_at=None,
        items=[],
    )


def test_html_email_uses_vake_brand_and_email_safe_font_stack() -> None:
    html = render_report_email_html(_report())

    assert "#312783" in html
    assert "#E6007E" in html
    assert "#76CBF3" in html
    assert "font-family:Poppins,Calibri,Arial,sans-serif" in html
    assert "Digipalvelujen kehittämisrahoitus" in html
    assert "Miksi VakeHyvälle" in html


def test_html_email_escapes_report_content() -> None:
    report = _report().model_copy(
        update={"email_body": "<script>alert('x')</script>"}
    )

    html = render_report_email_html(report)

    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_retry_delay_is_exponential_and_capped() -> None:
    assert retry_delay_minutes(1, base_minutes=5, max_minutes=60) == 5
    assert retry_delay_minutes(2, base_minutes=5, max_minutes=60) == 10
    assert retry_delay_minutes(5, base_minutes=5, max_minutes=60) == 60
