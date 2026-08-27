import hashlib
import re
from collections.abc import Iterable

import httpx
from bs4 import BeautifulSoup, Tag
from pydantic import HttpUrl

from app.config import Settings
from app.domain.funding_call import Evidence, FundingCallCandidate, RelevanceStatus


class SourceStructureError(RuntimeError):
    """Raised when a source loads but its expected funding-call structure is missing."""


_WHITESPACE = re.compile(r"\s+")


def normalize_text(value: str) -> str:
    return _WHITESPACE.sub(" ", value).strip()


def _external_key(title: str) -> str:
    """Create a deterministic fallback identity until STM exposes a better call ID."""

    canonical = f"STM|{normalize_text(title).casefold()}"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _candidate_buttons(root: Tag | BeautifulSoup) -> Iterable[Tag]:
    """Yield probable STM funding-call accordion buttons.

    STM currently exposes each call as an expandable button. We use semantic
    button elements rather than visual colour classes. The title text itself
    currently contains 'valtionavustus', which is used as a conservative guard
    against accidentally ingesting navigation/search buttons.
    """

    for node in root.find_all("button"):
        if not isinstance(node, Tag):
            continue

        title = normalize_text(node.get_text(" ", strip=True))
        if len(title) >= 20 and "valtionavustus" in title.casefold():
            yield node


def _details_for_button(button: Tag, root: Tag | BeautifulSoup) -> str | None:
    """Return visible accordion content associated with a funding-call heading."""

    controlled_id = button.attrs.get("aria-controls")
    if isinstance(controlled_id, str):
        controlled = root.find(id=controlled_id)
        if isinstance(controlled, Tag):
            text = normalize_text(controlled.get_text(" ", strip=True))
            if text:
                return text

    sibling = button.find_next_sibling()
    if isinstance(sibling, Tag) and sibling.name != "button":
        text = normalize_text(sibling.get_text(" ", strip=True))
        if text:
            return text

    return None


def parse_stm_html(html: str, source_url: str) -> list[FundingCallCandidate]:
    """Parse STM listing HTML into the source-independent domain model."""

    soup = BeautifulSoup(html, "lxml")
    root = soup.find("main") or soup

    seen_titles: set[str] = set()
    calls: list[FundingCallCandidate] = []

    for button in _candidate_buttons(root):
        title = normalize_text(button.get_text(" ", strip=True))
        normalized_title = title.casefold()
        if normalized_title in seen_titles:
            continue
        seen_titles.add(normalized_title)

        details_text = _details_for_button(button, root)
        relevance_reason = (
            "STM-liiketoimintasäännön mukaan kaikki uudet haut ovat relevantteja."
        )
        evidence = [
            Evidence(
                section="STM funding call heading",
                text=title,
                source_url=HttpUrl(source_url),
            )
        ]
        if details_text:
            evidence.append(
                Evidence(
                    section="STM funding call details",
                    text=details_text,
                    source_url=HttpUrl(source_url),
                )
            )

        calls.append(
            FundingCallCandidate(
                external_key=_external_key(title),
                source_code="STM",
                title=title,
                source_url=HttpUrl(source_url),
                description_text=details_text,
                relevance_status=RelevanceStatus.RELEVANT,
                relevance_reason=relevance_reason,
                evidence=tuple(evidence),
            )
        )

    if not calls:
        raise SourceStructureError(
            "STM page loaded, but no funding-call accordion buttons were found. "
            "Treat this as a possible source-structure change, not as an empty successful scan."
        )

    return calls


class STMScanner:
    source_code = "STM"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def scan(self) -> list[FundingCallCandidate]:
        source_url = str(self._settings.stm_url)
        headers = {"User-Agent": self._settings.user_agent}

        async with httpx.AsyncClient(
            headers=headers,
            timeout=self._settings.http_timeout_seconds,
            follow_redirects=True,
        ) as client:
            response = await client.get(source_url)
            response.raise_for_status()

        return parse_stm_html(response.text, source_url)
