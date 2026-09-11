from datetime import UTC, date, datetime

import pytest

from app.services.report_composer import ReportFinding, compose_automated_report


def _finding(*, call_id: int, title: str, source: str, event: str, review: bool = False) -> ReportFinding:
    return ReportFinding(
        funding_call_id=call_id,
        source_code=source,
        title=title,
        source_url=f"https://example.test/{call_id}",
        relevance_status="NEEDS_REVIEW" if review else "RELEVANT",
        relevance_reason=f"{title} tukee VakeHyvän kehittämistavoitetta.",
        event_type=event,
        application_deadline_on=date(2026, 10, call_id),
    )


def test_single_finding_uses_actual_title_in_report_base() -> None:
    finding = _finding(
        call_id=4,
        title="Digitaalisten sote-palvelujen kehittämisrahoitus",
        source="STM",
        event="funding.opportunity.discovered.v1",
    )

    composition = compose_automated_report(
        [finding],
        generated_at=datetime(2026, 9, 11, 9, 30, tzinfo=UTC),
        recipient_emails=("coordinator@example.test",),
    )

    assert "Digitaalisten sote-palvelujen" in composition.title
    assert "Digitaalisten sote-palvelujen" in composition.email_subject
    assert "Miksi VakeHyvälle" in composition.email_body
    assert "4.10.2026" in composition.email_body
    assert composition.recipient_emails == ("coordinator@example.test",)


def test_multi_finding_report_summarizes_actual_sources_and_certainty() -> None:
    findings = [
        _finding(
            call_id=4,
            title="STM haku",
            source="STM",
            event="funding.opportunity.discovered.v1",
        ),
        _finding(
            call_id=5,
            title="Sitra haku",
            source="SITRA",
            event="funding.opportunity.review_required.v1",
            review=True,
        ),
    ]

    composition = compose_automated_report(
        findings,
        generated_at=datetime(2026, 9, 11, 9, 30, tzinfo=UTC),
    )

    assert "2 rahoituslöydöstä" in composition.title
    assert "STM, Sitra" in composition.title
    assert "tarkistettavia 1" in composition.notes
    assert "STM haku" in composition.email_body
    assert "Sitra haku" in composition.email_body


def test_empty_composition_is_rejected() -> None:
    with pytest.raises(ValueError, match="At least one"):
        compose_automated_report(
            [],
            generated_at=datetime(2026, 9, 11, tzinfo=UTC),
        )
