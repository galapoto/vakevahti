import re
from collections.abc import Awaitable, Callable

import httpx
from bs4 import BeautifulSoup, NavigableString, Tag
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright
from pydantic import HttpUrl

from app.config import Settings
from app.domain.funding_call import Evidence, FundingCallCandidate, RelevanceStatus
from app.scanners.common import (
    SourceStructureError,
    canonical_url,
    normalize_text,
    parse_explicit_finnish_datetime,
    stable_external_key,
)

_OPEN_STATUS = "haku käynnissä"
_CLOSED_STATUS = "haku sulkeutunut"
_CALL_HEADING_NAMES = ("h3", "h4", "h5", "h6")
_LIFECYCLE_TEXT = re.compile(r"haku\s+(?:käynnissä|sulkeutunut)", re.IGNORECASE)

SitraHtmlRenderer = Callable[[], Awaitable[str]]


class SitraListingStructureError(SourceStructureError):
    """Raised when no Sitra funding-call lifecycle blocks can be recognized."""


def _contains_visible_lifecycle_status(html: str) -> bool:
    """Return whether lifecycle text is already present in non-script HTTP content."""

    soup = BeautifulSoup(html, "lxml")
    for hidden in soup.find_all(["script", "style", "template"]):
        hidden.decompose()

    text = normalize_text(soup.get_text(" ", strip=True)).casefold()
    return _OPEN_STATUS in text or _CLOSED_STATUS in text


def _nearest_call_container(status_text: NavigableString, root: Tag) -> tuple[Tag, Tag] | None:
    """Associate a lifecycle marker with the nearest single-card heading.

    Sitra's Power Pages markup can wrap an ``h3`` inside an anchor while placing the
    lifecycle status in a sibling element. Walking upward from the status avoids
    mistaking the broader ``h2 Rahoitushaut`` section for an individual opportunity.
    """

    node = status_text.parent
    while isinstance(node, Tag):
        headings = [
            heading
            for heading in node.find_all(_CALL_HEADING_NAMES)
            if isinstance(heading, Tag)
        ]
        if len(headings) == 1:
            return node, headings[0]
        if node is root:
            break
        node = node.parent
    return None


def _call_url(heading: Tag, card: Tag, base_url: str) -> str:
    """Prefer the link owning the call heading, then a unique card link."""

    anchor = heading.find("a", href=True)
    if isinstance(anchor, Tag):
        href = anchor.attrs.get("href")
        if isinstance(href, str):
            return canonical_url(base_url, href)

    node = heading.parent
    while isinstance(node, Tag):
        if node.name == "a":
            href = node.attrs.get("href")
            if isinstance(href, str):
                return canonical_url(base_url, href)
        if node is card:
            break
        node = node.parent

    anchors = [anchor for anchor in card.find_all("a", href=True) if isinstance(anchor, Tag)]
    if len(anchors) == 1:
        href = anchors[0].attrs.get("href")
        if isinstance(href, str):
            return canonical_url(base_url, href)

    return base_url


def parse_sitra_html(
    html: str,
    source_url: str,
    *,
    timezone: str = "Europe/Helsinki",
) -> list[FundingCallCandidate]:
    """Parse currently open Sitra funding cards from a rendered listing."""

    soup = BeautifulSoup(html, "lxml")
    root = soup.find("main") or soup

    recognized = 0
    calls: list[FundingCallCandidate] = []
    seen_containers: set[int] = set()

    for status_text in root.find_all(string=_LIFECYCLE_TEXT):
        if not isinstance(status_text, NavigableString):
            continue

        association = _nearest_call_container(status_text, root)
        if association is None:
            continue

        card, heading = association
        container_id = id(card)
        if container_id in seen_containers:
            continue
        seen_containers.add(container_id)

        title = normalize_text(heading.get_text(" ", strip=True))
        if not title:
            continue

        lifecycle = normalize_text(str(status_text)).casefold()
        is_open = _OPEN_STATUS in lifecycle
        is_closed = _CLOSED_STATUS in lifecycle
        if not (is_open or is_closed):
            continue

        recognized += 1
        if not is_open:
            continue

        details = normalize_text(card.get_text(" ", strip=True))
        canonical_call_url = _call_url(heading, card, source_url)
        deadline = parse_explicit_finnish_datetime(details, timezone)
        relevance_reason = (
            "Sitra-liiketoimintasäännön mukaan kaikki avoimet rahoitushaut ovat relevantteja."
        )
        evidence = (
            Evidence(
                section="Sitra funding call listing",
                text=details,
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
        raise SitraListingStructureError(
            "Sitra page loaded, but no funding-call status blocks could be associated with "
            "individual funding-card headings. Treat this as a possible source-structure change."
        )

    if not calls:
        raise SourceStructureError(
            "Sitra funding-call structure was recognized, but no currently open call "
            "could be emitted. Empty-source persistence semantics are not implemented yet."
        )

    return calls


async def _parse_sitra_with_render_fallback(
    html: str,
    source_url: str,
    *,
    timezone: str,
    render_html: SitraHtmlRenderer,
) -> list[FundingCallCandidate]:
    """Parse HTTP HTML first and render only when lifecycle content is client-side."""

    try:
        return parse_sitra_html(html, source_url, timezone=timezone)
    except SitraListingStructureError:
        if _contains_visible_lifecycle_status(html):
            raise

    rendered_html = await render_html()
    return parse_sitra_html(rendered_html, source_url, timezone=timezone)


async def _render_sitra_html(
    source_url: str,
    *,
    user_agent: str,
    timeout_seconds: float,
) -> str:
    """Render Sitra's public Power Pages listing when HTTP returns only the app shell."""

    timeout_ms = max(1, int(timeout_seconds * 1000))
    status_probe = """
    () => {
      const text = (document.body?.innerText || "").toLocaleLowerCase("fi-FI");
      return text.includes("haku käynnissä") || text.includes("haku sulkeutunut");
    }
    """

    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            try:
                page = await browser.new_page(user_agent=user_agent)
                await page.goto(
                    source_url,
                    wait_until="domcontentloaded",
                    timeout=timeout_ms,
                )
                await page.wait_for_function(status_probe, timeout=timeout_ms)
                return await page.content()
            finally:
                await browser.close()
    except PlaywrightTimeoutError as exc:
        raise SourceStructureError(
            "Sitra rendered page did not expose funding-call lifecycle markers before "
            "the configured timeout. Treat this as a possible source-structure change."
        ) from exc
    except PlaywrightError as exc:
        raise RuntimeError(
            "Sitra browser rendering failed. Ensure the Playwright Chromium runtime "
            "is installed for workers that enable SITRA."
        ) from exc


class SitraScanner:
    source_code = "SITRA"

    def __init__(
        self,
        settings: Settings,
        *,
        html_renderer: SitraHtmlRenderer | None = None,
    ) -> None:
        self._settings = settings
        self._html_renderer = html_renderer

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

        async def render_html() -> str:
            if self._html_renderer is not None:
                return await self._html_renderer()
            return await _render_sitra_html(
                source_url,
                user_agent=self._settings.user_agent,
                timeout_seconds=self._settings.http_timeout_seconds,
            )

        return await _parse_sitra_with_render_fallback(
            response.text,
            source_url,
            timezone=self._settings.timezone,
            render_html=render_html,
        )
