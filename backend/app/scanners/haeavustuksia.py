import asyncio
import re
from collections.abc import Awaitable, Callable
from urllib.parse import urlsplit, urlunsplit

import httpx
from bs4 import BeautifulSoup, Tag
from bs4.element import NavigableString
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

HaeavustuksiaHtmlRenderer = Callable[[], Awaitable[str]]

_CALL_PATH = re.compile(r"^/fi/haku/(?P<call_id>[^/?#]+)", re.IGNORECASE)
_HEADING_NAMES = tuple(f"h{level}" for level in range(1, 7))
_ELIGIBILITY_HEADING = "kenelle/mille avustusta voidaan myöntää"
_POSITIVE_ELIGIBILITY_TERMS = (
    "hyvinvointialue",
    "julkisoikeudellinen yhteisö",
    "julkinen toimija",
    "julkinen organisaatio",
    "julkisyhteisö",
    "julkinen oikeushenkilö",
    "valtionavustuskelpoinen julkisoikeudellinen toimija",
)
_EXCLUSIVE_MARKERS = ("ainoastaan", "vain ")


class HaeavustuksiaListingStructureError(SourceStructureError):
    """Raised when the grants listing cannot be mapped to individual call URLs."""


def _call_identity_from_url(url: str) -> str | None:
    path = urlsplit(url).path
    match = _CALL_PATH.match(path)
    return match.group("call_id") if match else None


def _call_root_url(base_url: str, href: str) -> str | None:
    resolved = canonical_url(base_url, href)
    split = urlsplit(resolved)
    match = _CALL_PATH.match(split.path)
    if match is None:
        return None
    root_path = f"/fi/haku/{match.group('call_id')}"
    return urlunsplit((split.scheme, split.netloc, root_path, "", ""))


def parse_haeavustuksia_listing_html(html: str, source_url: str) -> list[str]:
    """Return de-duplicated canonical grant roots from a Haeavustuksia listing."""

    soup = BeautifulSoup(html, "lxml")
    root = soup.find("main") or soup
    urls: list[str] = []
    seen: set[str] = set()

    for anchor in root.find_all("a", href=True):
        if not isinstance(anchor, Tag):
            continue
        href = anchor.attrs.get("href")
        if not isinstance(href, str):
            continue
        call_url = _call_root_url(source_url, href)
        if call_url is None or call_url in seen:
            continue
        seen.add(call_url)
        urls.append(call_url)

    if not urls:
        raise HaeavustuksiaListingStructureError(
            "Haeavustuksia listing loaded, but no /fi/haku/<id> grant links were found. "
            "Treat this as a possible source-structure change rather than an empty scan."
        )

    return urls


def _heading_level(tag: Tag) -> int:
    name = tag.name or "h6"
    return int(name[1]) if len(name) == 2 and name[0] == "h" and name[1].isdigit() else 6


def _section_after_heading(root: Tag | BeautifulSoup, heading_text: str) -> str | None:
    """Extract semantic section text until the next heading of equal/higher rank."""

    target: Tag | None = None
    for heading in root.find_all(_HEADING_NAMES):
        if not isinstance(heading, Tag):
            continue
        text = normalize_text(heading.get_text(" ", strip=True)).casefold()
        if heading_text.casefold() in text:
            target = heading
            break

    if target is None:
        return None

    level = _heading_level(target)
    parts: list[str] = []
    for node in target.next_elements:
        if node is target:
            continue
        if isinstance(node, Tag) and node.name in _HEADING_NAMES:
            if _heading_level(node) <= level:
                break
        if isinstance(node, NavigableString):
            text = normalize_text(str(node))
            if text:
                parts.append(text)

    value = normalize_text(" ".join(parts))
    return value or None


def _application_window(text: str, timezone: str) -> tuple[object | None, object | None]:
    """Parse only explicitly timed opening/deadline values from the Hakuaika segment."""

    folded = text.casefold()
    start = folded.find("hakuaika")
    if start < 0:
        return None, None

    window = text[start : start + 500]
    opens_at = parse_explicit_finnish_datetime(window, timezone)

    window_folded = window.casefold()
    deadline_start = window_folded.find("päätt")
    deadline_at = None
    if deadline_start >= 0:
        deadline_at = parse_explicit_finnish_datetime(window[deadline_start:], timezone)

    return opens_at, deadline_at


def _classify_eligibility(section: str | None) -> tuple[RelevanceStatus, str, str | None]:
    if not section:
        return (
            RelevanceStatus.NEEDS_REVIEW,
            "Hakijakelpoisuuden Myöntöperusteet-osiota ei voitu tunnistaa varmasti; "
            "haku vaatii tarkistuksen ennen ilmoitusta.",
            None,
        )

    folded = section.casefold()
    for term in _POSITIVE_ELIGIBILITY_TERMS:
        if term.casefold() in folded:
            return (
                RelevanceStatus.RELEVANT,
                f"Hakijakelpoisuus sisältää VakeHyvälle soveltuvan ilmauksen: {term}.",
                term,
            )

    if any(marker in folded for marker in _EXCLUSIVE_MARKERS):
        return (
            RelevanceStatus.NOT_RELEVANT,
            "Hakijakelpoisuus on ilmaistu rajatuksi, eikä stakeholderin hyväksymää "
            "hyvinvointialue-/julkistoimija-termiä löytynyt.",
            None,
        )

    return (
        RelevanceStatus.NEEDS_REVIEW,
        "Hakijakelpoisuus löytyi, mutta hyvinvointialueen osallistumista ei voida "
        "ratkaista turvallisesti nykyisillä deterministisillä termeillä.",
        None,
    )


def parse_haeavustuksia_detail_html(
    html: str,
    call_url: str,
    *,
    timezone: str = "Europe/Helsinki",
) -> FundingCallCandidate:
    """Parse one Haeavustuksia grant and classify wellbeing-area eligibility."""

    soup = BeautifulSoup(html, "lxml")
    root = soup.find("main") or soup
    heading = root.find("h1")
    if not isinstance(heading, Tag):
        raise SourceStructureError(
            f"Haeavustuksia call {call_url} loaded without an h1 title."
        )

    title = normalize_text(heading.get_text(" ", strip=True))
    if not title:
        raise SourceStructureError(f"Haeavustuksia call {call_url} has an empty title.")

    call_id = _call_identity_from_url(call_url)
    if call_id is None:
        raise SourceStructureError(f"Haeavustuksia call URL has no stable call id: {call_url}")

    full_text = normalize_text(root.get_text(" ", strip=True))
    opens_at, deadline_at = _application_window(full_text, timezone)
    eligibility = _section_after_heading(root, _ELIGIBILITY_HEADING)
    status, reason, matched_term = _classify_eligibility(eligibility)

    detail_url = f"{call_url.rstrip('/')}/hakuilmoitus/myontoperusteet"
    evidence: list[Evidence] = [
        Evidence(
            section="Haeavustuksia grant title",
            text=title,
            source_url=HttpUrl(call_url),
        )
    ]
    if eligibility:
        evidence.append(
            Evidence(
                section="Kenelle/mille avustusta voidaan myöntää",
                text=eligibility,
                source_url=HttpUrl(detail_url),
            )
        )
    if matched_term:
        evidence.append(
            Evidence(
                section="Matched wellbeing/public-entity eligibility term",
                text=matched_term,
                source_url=HttpUrl(detail_url),
            )
        )

    return FundingCallCandidate(
        external_key=stable_external_key("HAEAVUSTUKSIA", identity=call_id),
        source_code="HAEAVUSTUKSIA",
        title=title,
        source_url=HttpUrl(call_url),
        application_opens_at=opens_at,
        application_deadline_at=deadline_at,
        description_text=eligibility or None,
        relevance_status=status,
        relevance_reason=reason,
        evidence=tuple(evidence),
    )


async def _render_listing_html(
    source_url: str,
    *,
    user_agent: str,
    timeout_seconds: float,
) -> str:
    timeout_ms = max(1, int(timeout_seconds * 1000))
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            try:
                page = await browser.new_page(user_agent=user_agent)
                await page.goto(source_url, wait_until="domcontentloaded", timeout=timeout_ms)
                await page.wait_for_function(
                    "document.querySelectorAll('a[href*=\"/fi/haku/\"]').length > 0",
                    timeout=timeout_ms,
                )

                previous = -1
                stable_rounds = 0
                for _ in range(20):
                    count = await page.locator('a[href*="/fi/haku/"]').count()
                    if count == previous:
                        stable_rounds += 1
                    else:
                        stable_rounds = 0
                        previous = count
                    if stable_rounds >= 3:
                        break
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(250)
                return await page.content()
            finally:
                await browser.close()
    except PlaywrightTimeoutError as exc:
        raise HaeavustuksiaListingStructureError(
            "Rendered Haeavustuksia listing did not expose grant links before timeout."
        ) from exc
    except PlaywrightError as exc:
        raise RuntimeError(
            "Haeavustuksia browser rendering failed. Ensure Playwright Chromium is installed."
        ) from exc


class HaeavustuksiaScanner:
    source_code = "HAEAVUSTUKSIA"

    def __init__(
        self,
        settings: Settings,
        *,
        html_renderer: HaeavustuksiaHtmlRenderer | None = None,
        detail_concurrency: int = 6,
    ) -> None:
        self._settings = settings
        self._html_renderer = html_renderer
        self._detail_concurrency = detail_concurrency

    async def scan(self) -> list[FundingCallCandidate]:
        source_url = str(self._settings.haeavustuksia_url)
        headers = {"User-Agent": self._settings.user_agent}

        async with httpx.AsyncClient(
            headers=headers,
            timeout=self._settings.http_timeout_seconds,
            follow_redirects=True,
        ) as client:
            listing = await client.get(source_url)
            listing.raise_for_status()
            try:
                call_urls = parse_haeavustuksia_listing_html(listing.text, source_url)
            except HaeavustuksiaListingStructureError:
                if self._html_renderer is not None:
                    rendered = await self._html_renderer()
                else:
                    rendered = await _render_listing_html(
                        source_url,
                        user_agent=self._settings.user_agent,
                        timeout_seconds=self._settings.http_timeout_seconds,
                    )
                call_urls = parse_haeavustuksia_listing_html(rendered, source_url)

            semaphore = asyncio.Semaphore(self._detail_concurrency)

            async def fetch_call(call_url: str) -> FundingCallCandidate:
                detail_url = f"{call_url.rstrip('/')}/hakuilmoitus/myontoperusteet"
                async with semaphore:
                    response = await client.get(detail_url)
                    response.raise_for_status()
                return parse_haeavustuksia_detail_html(
                    response.text,
                    call_url,
                    timezone=self._settings.timezone,
                )

            return list(await asyncio.gather(*(fetch_call(url) for url in call_urls)))
