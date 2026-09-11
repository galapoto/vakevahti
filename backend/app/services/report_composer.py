from dataclasses import dataclass
from datetime import date, datetime

_SOURCE_NAMES = {
    "STM": "STM",
    "HAEAVUSTUKSIA": "Haeavustuksia.fi",
    "EURA": "EURA 2021",
    "SITRA": "Sitra",
    "ACADEMY": "Suomen Akatemia",
}

_EVENT_LABELS = {
    "funding.opportunity.discovered.v1": "Uusi löydös",
    "funding.opportunity.changed.v1": "Muuttunut haku",
    "funding.opportunity.review_required.v1": "Tarkistettava löydös",
}


@dataclass(frozen=True)
class ReportFinding:
    funding_call_id: int
    source_code: str
    title: str
    source_url: str
    relevance_status: str
    relevance_reason: str
    event_type: str
    application_deadline_on: date | None = None
    application_deadline_at: datetime | None = None


@dataclass(frozen=True)
class ReportComposition:
    title: str
    notes: str
    email_subject: str
    email_body: str
    recipient_emails: tuple[str, ...]


def _source_name(source_code: str) -> str:
    return _SOURCE_NAMES.get(source_code, source_code)


def _deadline(finding: ReportFinding) -> str:
    if finding.application_deadline_at is not None:
        exact = finding.application_deadline_at
        return f"{exact.day}.{exact.month}.{exact.year} klo {exact.hour:02d}.{exact.minute:02d}"
    if finding.application_deadline_on is not None:
        day = finding.application_deadline_on
        return f"{day.day}.{day.month}.{day.year}"
    return "Ei ilmoitettu"


def _event_label(event_type: str) -> str:
    return _EVENT_LABELS.get(event_type, "Rahoituslöydös")


def compose_automated_report(
    findings: list[ReportFinding],
    *,
    generated_at: datetime,
    recipient_emails: tuple[str, ...] = (),
) -> ReportComposition:
    """Build a deterministic report base whose wording comes from the actual findings."""

    if not findings:
        raise ValueError("At least one report finding is required.")

    unique_sources: list[str] = []
    for finding in findings:
        name = _source_name(finding.source_code)
        if name not in unique_sources:
            unique_sources.append(name)

    generated_date = f"{generated_at.day}.{generated_at.month}.{generated_at.year}"
    review_count = sum(
        finding.relevance_status.upper() == "NEEDS_REVIEW" for finding in findings
    )
    confirmed_count = len(findings) - review_count
    changed_count = sum(
        finding.event_type == "funding.opportunity.changed.v1" for finding in findings
    )
    new_count = sum(
        finding.event_type == "funding.opportunity.discovered.v1" for finding in findings
    )

    if len(findings) == 1:
        finding = findings[0]
        title = f"VakeVahti · {_source_name(finding.source_code)} · {finding.title}"
        subject = f"VakeVahti: {_event_label(finding.event_type)} – {finding.title}"
    else:
        source_text = ", ".join(unique_sources)
        title = (
            f"VakeVahti · {len(findings)} rahoituslöydöstä · "
            f"{source_text} · {generated_date}"
        )
        subject = (
            f"VakeVahti: {len(findings)} uutta tai muuttunutta "
            f"rahoituslöydöstä – {source_text}"
        )

    title = title[:200]
    subject = subject[:500]
    notes = (
        "Automaattisesti muodostettu VakeVahdin uusista ja muuttuneista löydöksistä. "
        f"Varmistettuja {confirmed_count}, tarkistettavia {review_count}. "
        "Sisältöä voi muokata ennen mahdollista uutta lähetystä."
    )

    lines = [
        "VakeHyvän rahoitusvahti",
        "",
        f"Koonti {generated_date}",
        (
            f"Löydöksiä yhteensä {len(findings)} · uusia {new_count} · "
            f"muuttuneita {changed_count} · tarkistettavia {review_count}"
        ),
        "",
        "VakeVahti muodosti tämän raporttipohjan automaattisesti havaittujen "
        "rahoitusmahdollisuuksien perusteella.",
        "",
    ]

    for index, finding in enumerate(findings, start=1):
        lines.extend(
            [
                f"{index}. {finding.title}",
                f"Lähde: {_source_name(finding.source_code)}",
                f"Tyyppi: {_event_label(finding.event_type)}",
                f"Hakuaika päättyy: {_deadline(finding)}",
                f"Miksi VakeHyvälle: {finding.relevance_reason}",
                f"Linkki: {finding.source_url}",
                "",
            ]
        )

    lines.extend(
        [
            "Seuraava vaihe",
            "Varmistetut haut voidaan ottaa valmisteluun. Tarkistettavat haut tulee "
            "varmistaa ennen hakemuksen käynnistämistä.",
            "",
            "Tämä raportti on VakeVahdin automaattisesti muodostama pohja ja sitä voi muokata.",
        ]
    )

    return ReportComposition(
        title=title,
        notes=notes,
        email_subject=subject,
        email_body="\n".join(lines),
        recipient_emails=recipient_emails,
    )
