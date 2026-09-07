import hashlib
import re
from datetime import date, datetime
from urllib.parse import urljoin, urlsplit, urlunsplit
from zoneinfo import ZoneInfo

from bs4 import Tag

_WHITESPACE = re.compile(r"\s+")
_FI_DATE = re.compile(
    r"(?P<day>\d{1,2})\.(?P<month>\d{1,2})\.(?P<year>\d{4})",
    re.IGNORECASE,
)
_EXPLICIT_FI_DATETIME = re.compile(
    r"(?P<day>\d{1,2})\.(?P<month>\d{1,2})\.(?P<year>\d{4})"
    r"(?:\s+klo)?\s+(?P<hour>\d{1,2})[.:](?P<minute>\d{2})",
    re.IGNORECASE,
)


class SourceStructureError(RuntimeError):
    """Raised when a source loads but its expected funding structure is missing."""


def normalize_text(value: str) -> str:
    return _WHITESPACE.sub(" ", value).strip()


def canonical_url(base_url: str, href: str | None) -> str:
    """Build a stable canonical HTTP URL while dropping fragments."""

    resolved = urljoin(base_url, href or "")
    split = urlsplit(resolved)
    return urlunsplit((split.scheme, split.netloc, split.path, split.query, ""))


def stable_external_key(source_code: str, *, identity: str) -> str:
    canonical = f"{source_code.upper()}|{normalize_text(identity).casefold()}"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def heading_link(heading: Tag, base_url: str) -> str | None:
    anchor = heading.find("a", href=True)
    if not isinstance(anchor, Tag):
        return None
    href = anchor.attrs.get("href")
    return canonical_url(base_url, href if isinstance(href, str) else None)


def parse_finnish_date(text: str) -> date | None:
    """Parse the first numeric Finnish calendar date without inventing a time."""

    match = _FI_DATE.search(text)
    if match is None:
        return None

    return date(
        int(match.group("year")),
        int(match.group("month")),
        int(match.group("day")),
    )


def parse_explicit_finnish_datetime(text: str, timezone: str) -> datetime | None:
    """Parse only Finnish dates that explicitly include a clock time.

    A bare date is intentionally left unknown in the datetime field because exact
    timestamps must not invent midnight or end-of-day semantics. Callers can use
    :func:`parse_finnish_date` to preserve the known calendar date separately.
    """

    match = _EXPLICIT_FI_DATETIME.search(text)
    if match is None:
        return None

    return datetime(
        int(match.group("year")),
        int(match.group("month")),
        int(match.group("day")),
        int(match.group("hour")),
        int(match.group("minute")),
        tzinfo=ZoneInfo(timezone),
    )
