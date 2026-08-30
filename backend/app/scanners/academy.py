import re
from datetime import datetime

import httpx
from bs4 import BeautifulSoup, Tag
from pydantic import HttpUrl

from app.config import Settings
from app.domain.funding_call import Evidence, FundingCallCandidate, RelevanceStatus
from app.scanners.common import (
    SourceStructureError,
    heading_link,
    normalize_text,
    parse_explicit_finnish_datetime,
    stable_external_key,
)

_START_SECTION = "avoimet ja tulossa olevat haut"
_END_SECTIONS = {"valmistelussa olevat haut", "päättyneet haut"}
_DEADLINE_LINE = re.compile(r"haku päättyy", re.IGNORECASE)


def _call_segment(heading: Tag) -> str:
    parts: list[str] = []
    node = heading.find_next_sibling()
    while isinstance(node, Tag):
        if node.name in {"h3", "h4"}:
            break
        text = normalize_text(node.get_text(" ", strip=True))
        if text:
            parts.append(text)
        node = node.find_next_sibling()
    return normalize_text(" ".join(parts))


def _deadline_from_details(details: str, timezone: str) -> datetime | None:
    match = _DEADLINE_LINE.search(details)
    if match is None:
        return None
    return parse_explicit_finnish_datetime(details[match.start() :], timezone)


def parse_academy_html(
    html: str,
    source_url: str,
    *,
    timezone: str = "Europe/Helsinki",
) -> list[FundingCallCandidate]:
    """Parse open/upcoming Suomen Akatemia calls from the official calls page."""

    soup = BeautifulSoup(html, "lxml")
    root = soup.find("main") or soup

    start_heading: Tag | None = None
    for heading in root.find_all(["h1", "h2", "h3"]):
        if isinstance(heading, Tag) and _START_SECTION in normalize_text(
            heading.get_text(" ", strip=True)
        ).casefold():
            start_heading = heading
            break

    if start_heading is None:
        raise SourceStructureError(
            "Suomen Akatemia page loaded, but the open/upcoming calls section was not found."
        )

    calls: list[FundingCallCandidate] = []
    for heading in start_heading.find_all_next(["h2", "h3", "h4"]):
        if not isinstance(heading, Tag):
            continue

        title = normalize_text(heading.get_text(" ", strip=True))
        title_folded = title.casefold()
        if any(marker in title_folded for marker in _END_SECTIONS):
            break

        if heading.name not in {"h3", "h4"}:
            continue

        details = _call_segment(heading)
        details_folded = details.casefold()
        if "haku alkaa" not in details_folded or "haku päättyy" not in details_folded:
            continue

        canonical_call_url = heading_link(heading, source_url) or source_url
        deadline = _deadline_from_details(details, timezone)
        relevance_reason = (
            "Suomen Akatemia -liiketoimintasäännön mukaan kaikki avoimet ja tulossa "
            "olevat haut ovat relevantteja."
        )
        evidence = (
            Evidence(
                section="Suomen Akatemia open/upcoming call listing",
                text=normalize_text(f"{title} {details}"),
                source_url=HttpUrl(canonical_call_url),
            ),
        )

        calls.append(
            FundingCallCandidate(
                external_key=stable_external_key(
                    "ACADEMY",
                    identity=canonical_call_url if canonical_call_url != source_url else title,
                ),
                source_code="ACADEMY",
                title=title,
                source_url=HttpUrl(canonical_call_url),
                application_deadline_at=deadline,
                description_text=details,
                relevance_status=RelevanceStatus.RELEVANT,
                relevance_reason=relevance_reason,
                evidence=evidence,
            )
        )

    if not calls:
        raise SourceStructureError(
            "Suomen Akatemia open/upcoming section was found, but no call blocks with "
            "application timing were recognized."
        )

    return calls


class AcademyScanner:
    source_code = "ACADEMY"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def scan(self) -> list[FundingCallCandidate]:
        source_url = str(self._settings.academy_url)
        headers = {"User-Agent": self._settings.user_agent}

        async with httpx.AsyncClient(
            headers=headers,
            timeout=self._settings.http_timeout_seconds,
            follow_redirects=True,
        ) as client:
            response = await client.get(source_url)
            response.raise_for_status()

        return parse_academy_html(
            response.text,
            source_url,
            timezone=self._settings.timezone,
        )
