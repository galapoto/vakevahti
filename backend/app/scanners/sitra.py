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

_OPEN_STATUS = "haku käynnissä"
_CLOSED_STATUS = "haku sulkeutunut"


def _segment_text(heading: Tag) -> str:
    parts: list[str] = []
    node = heading.find_next_sibling()
    while isinstance(node, Tag):
        if node.name in {"h2", "h3"}:
            break
        text = normalize_text(node.get_text(" ", strip=True))
        if text:
            parts.append(text)
        node = node.find_next_sibling()

    if parts:
        return normalize_text(" ".join(parts))

    parent = heading.parent
    if isinstance(parent, Tag):
        return normalize_text(parent.get_text(" ", strip=True))
    return ""


def parse_sitra_html(
    html: str,
    source_url: str,
    *,
    timezone: str = "Europe/Helsinki",
) -> list[FundingCallCandidate]:
    """Parse currently open Sitra funding calls from the funding service listing."""

    soup = BeautifulSoup(html, "lxml")
    root = soup.find("main") or soup

    recognized = 0
    calls: list[FundingCallCandidate] = []

    for heading in root.find_all(["h3", "h4"]):
        if not isinstance(heading, Tag):
            continue

        title = normalize_text(heading.get_text(" ", strip=True))
        if not title:
            continue

        details = _segment_text(heading)
        details_folded = details.casefold()
        is_open = _OPEN_STATUS in details_folded
        is_closed = _CLOSED_STATUS in details_folded
        if not (is_open or is_closed):
            continue

        recognized += 1
        if not is_open:
            continue

        canonical_call_url = heading_link(heading, source_url) or source_url
        deadline = parse_explicit_finnish_datetime(details, timezone)
        relevance_reason = (
            "Sitra-liiketoimintasäännön mukaan kaikki avoimet rahoitushaut ovat relevantteja."
        )
        evidence = (
            Evidence(
                section="Sitra funding call listing",
                text=normalize_text(f"{title} {details}"),
                source_url=HttpUrl(canonical_call_url),
            ),
        )

        calls.append(
            FundingCallCandidate(
                external_key=stable_external_key(
                    "SITRA",
                    identity=canonical_call_url if canonical_call_url != source_url else title,
                ),
                source_code="SITRA",
                title=title,
                source_url=HttpUrl(canonical_call_url),
                application_deadline_at=deadline,
                description_text=details or None,
                relevance_status=RelevanceStatus.RELEVANT,
                relevance_reason=relevance_reason,
                evidence=evidence,
            )
        )

    if recognized == 0:
        raise SourceStructureError(
            "Sitra page loaded, but no funding-call status blocks were recognized. "
            "Treat this as a possible source-structure change."
        )

    if not calls:
        raise SourceStructureError(
            "Sitra funding-call structure was recognized, but no currently open call "
            "could be emitted. Empty-source persistence semantics are not implemented yet."
        )

    return calls


class SitraScanner:
    source_code = "SITRA"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def scan(self) -> list[FundingCallCandidate]:
        source_url = str(self._settings.sitra_url)
        headers = {"User-Agent": self._settings.user_agent}

        async with httpx.AsyncClient(
            headers=headers,
            timeout=self._settings.http_timeout_seconds,
            follow_redirects=True,
        ) as client:
            response = await client.get(source_url)
            response.raise_for_status()

        return parse_sitra_html(
            response.text,
            source_url,
            timezone=self._settings.timezone,
        )
