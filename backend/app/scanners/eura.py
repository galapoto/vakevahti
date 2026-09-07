import asyncio
import re
from collections.abc import Awaitable, Callable
from urllib.parse import urlsplit, urlunsplit

import httpx
from bs4 import BeautifulSoup, Tag
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright
from pydantic import HttpUrl

from app.config import Settings
from app.domain.funding_call import Evidence, FundingCallCandidate, RelevanceStatus
from app.scanners.common import SourceStructureError, canonical_url, normalize_text, stable_external_key

EuraHtmlRenderer = Callable[[], Awaitable[str]]

_NOTICE_PATH = re.compile(
    r"^/hakuilmoitukset/hakuilmoitus/(?P<notice_id>[0-9a-fA-F-]{20,})/?$"
)
_TARGET_REGIONS = ("valtakunnallinen", "etelä-suomi")
_POSITIVE_ELIGIBILITY_TERMS = (
    "hyvinvointialue",
    "julkisoikeudellinen yhteisö",
    "julkinen toimija",
    "julkinen organisaatio",
    "julkisyhteisö",
    "julkinen oikeushenkilö",
    "valtionavustuskelpoinen julkisoikeudellinen toimija",
)


class EuraListingStructureError(SourceStructureError):
    """Raised when EURA listing does not expose recognizable notice URLs."""


def _notice_identity_from_url(url: str) -> str | None:
    path = urlsplit(url).path
    match = _NOTICE_PATH.match(path)
    return match.group("notice_id") if match else None


def _notice_root_url(base_url: str, href: str) -> str | None:
    resolved = canonical_url(base_url, href)
    split = urlsplit(resolved)
    match = _NOTICE_PATH.match(split.path)
    if match is None:
        return None
    path = f"/hakuilmoitukset/hakuilmoitus/{match.group('notice_id')}"
    return urlunsplit((split.scheme, split.netloc, path, "", ""))


def parse_eura_listing_html(html: str, source_url: str) -> list[str]:
    """Return de-duplicated canonical EURA notice URLs."""

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
        notice_url = _notice_root_url(source_url, href)
        if notice_url is None or notice_url in seen:
            continue
        seen.add(notice_url)
        urls.append(notice_url)

    if not urls:
        raise EuraListingStructureError(
            "EURA listing loaded, but no /hakuilmoitukset/hakuilmoitus/<id> links "
            "were found. Treat this as a possible source-structure change."
        )

    return urls


def _lines(root: Tag | BeautifulSoup) -> list[str]:
    return [
        normalized
        for raw in root.stripped_strings
        if (normalized := normalize_text(str(raw)))
    ]


def _extract_block(
    lines: list[str],
    label: str,
    *,
    stop_labels: tuple[str, ...],
) -> str | None:
    """Extract the first non-empty text block following an exact semantic label."""

    folded_label = label.casefold()
    folded_stops = tuple(item.casefold() for item in stop_labels)

    for index, line in enumerate(lines):
        if line.casefold().rstrip(":") != folded_label.rstrip(":"):
            continue

        parts: list[str] = []
        for candidate in lines[index + 1 :]:
            folded = candidate.casefold().rstrip(":")
            if any(folded == stop.rstrip(":") for stop in folded_stops):
                break
            parts.append(candidate)

        value = normalize_text(" ".join(parts))
        if value:
            return value

    return None


def _region_block(lines: list[str]) -> str | None:
    return _extract_block(
        lines,
        "Haun kohdealue",
        stop_labels=("Maakunnat", "Hankehaun kuvaus"),
    )


def _description_block(lines: list[str]) -> str | None:
    return _extract_block(
        lines,
        "Hankehaun kuvaus",
        stop_labels=(
            "Käytettävissä oleva myöntövaltuus",
            "Valintaperusteet ja pisteytysmalli",
            "Valintaperusteet",
            "Hakeminen",
            "Lisätiedot",
            "Lainsäädäntö",
        ),
    )


def _additional_info_block(lines: list[str]) -> str | None:
    return _extract_block(
        lines,
        "Lisätiedot",
        stop_labels=("Lainsäädäntö", "Mer information", "Hakeminen"),
    )


def _classify_region(region: str) -> bool:
    folded = region.casefold()
    return any(target in folded for target in _TARGET_REGIONS)


def _classify_eligibility(
    *,
    region: str,
    description: str | None,
    additional_info: str | None,
) -> tuple[RelevanceStatus, str, str | None]:
    if not _classify_region(region):
        return (
            RelevanceStatus.NOT_RELEVANT,
            "EURA-haun kohdealue ei ole Valtakunnallinen eikä Etelä-Suomi.",
            None,
        )

    corpus = normalize_text(" ".join(part for part in (description, additional_info) if part))
    folded = corpus.casefold()
    for term in _POSITIVE_ELIGIBILITY_TERMS:
        if term.casefold() in folded:
            return (
                RelevanceStatus.RELEVANT,
                f"Kohdealue täsmää ja hakuteksti sisältää VakeHyvälle soveltuvan "
                f"hakijailmauksen: {term}.",
                term,
            )

    return (
        RelevanceStatus.NEEDS_REVIEW,
        "Kohdealue on Valtakunnallinen/Etelä-Suomi, mutta hyvinvointialueen "
        "hakijakelpoisuutta ei voida ratkaista turvallisesti nykyisillä "
        "deterministisillä termeillä.",
        None,
    )


def parse_eura_detail_html(html: str, notice_url: str) -> FundingCallCandidate:
    """Parse one EURA notice using region-first, evidence-backed relevance logic."""

    soup = BeautifulSoup(html, "lxml")
    root = soup.find("main") or soup
    heading = root.find("h1")
    if not isinstance(heading, Tag):
        raise SourceStructureError(f"EURA notice {notice_url} loaded without an h1 title.")

    title = normalize_text(heading.get_text(" ", strip=True))
    if not title:
        raise SourceStructureError(f"EURA notice {notice_url} has an empty title.")

    notice_id = _notice_identity_from_url(notice_url)
    if notice_id is None:
        raise SourceStructureError(f"EURA notice URL has no stable notice id: {notice_url}")

    lines = _lines(root)
    region = _region_block(lines)
    if not region:
        raise SourceStructureError(
            f"EURA notice {notice_url} did not expose the required 'Haun kohdealue' block."
        )

    description = _description_block(lines)
    additional_info = _additional_info_block(lines)
    status, reason, matched_term = _classify_eligibility(
        region=region,
        description=description,
        additional_info=additional_info,
    )

    evidence: list[Evidence] = [
        Evidence(
            section="Haun kohdealue",
            text=region,
            source_url=HttpUrl(notice_url),
        )
    ]
    if description:
        evidence.append(
            Evidence(
                section="Hankehaun kuvaus",
                text=description,
                source_url=HttpUrl(notice_url),
            )
        )
    if additional_info:
        evidence.append(
            Evidence(
                section="Lisätiedot",
                text=additional_info,
                source_url=HttpUrl(notice_url),
            )
        )
    if matched_term:
        evidence.append(
            Evidence(
                section="Matched wellbeing/public-entity eligibility term",
                text=matched_term,
                source_url=HttpUrl(notice_url),
            )
        )

    description_text = normalize_text(
        " ".join(part for part in (description, additional_info) if part)
    ) or None

    return FundingCallCandidate(
        external_key=stable_external_key("EURA", identity=notice_id),
        source_code="EURA",
        title=title,
        source_url=HttpUrl(notice_url),
        description_text=description_text,
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
                    "document.querySelectorAll('a[href*=\"/hakuilmoitukset/hakuilmoitus/\"]').length > 0",
                    timeout=timeout_ms,
                )

                previous = -1
                stable_rounds = 0
                for _ in range(20):
                    count = await page.locator(
                        'a[href*="/hakuilmoitukset/hakuilmoitus/"]'
                    ).count()
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
        raise EuraListingStructureError(
            "Rendered EURA listing did not expose notice links before timeout."
        ) from exc
    except PlaywrightError as exc:
        raise RuntimeError(
            "EURA browser rendering failed. Ensure Playwright Chromium is installed."
        ) from exc


class EuraScanner:
    source_code = "EURA"

    def __init__(
        self,
        settings: Settings,
        *,
        html_renderer: EuraHtmlRenderer | None = None,
        detail_concurrency: int = 6,
    ) -> None:
        self._settings = settings
        self._html_renderer = html_renderer
        self._detail_concurrency = detail_concurrency

    async def scan(self) -> list[FundingCallCandidate]:
        source_url = str(self._settings.eura_url)
        headers = {"User-Agent": self._settings.user_agent}

        async with httpx.AsyncClient(
            headers=headers,
            timeout=self._settings.http_timeout_seconds,
            follow_redirects=True,
        ) as client:
            listing = await client.get(source_url)
            listing.raise_for_status()
            try:
                notice_urls = parse_eura_listing_html(listing.text, source_url)
            except EuraListingStructureError:
                if self._html_renderer is not None:
                    rendered = await self._html_renderer()
                else:
                    rendered = await _render_listing_html(
                        source_url,
                        user_agent=self._settings.user_agent,
                        timeout_seconds=self._settings.http_timeout_seconds,
                    )
                notice_urls = parse_eura_listing_html(rendered, source_url)

            semaphore = asyncio.Semaphore(self._detail_concurrency)

            async def fetch_notice(notice_url: str) -> FundingCallCandidate:
                async with semaphore:
                    response = await client.get(notice_url)
                    response.raise_for_status()
                return parse_eura_detail_html(response.text, notice_url)

            return list(
                await asyncio.gather(*(fetch_notice(url) for url in notice_urls))
            )
