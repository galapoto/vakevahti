from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, HttpUrl


class RelevanceStatus(StrEnum):
    RELEVANT = "RELEVANT"
    NOT_RELEVANT = "NOT_RELEVANT"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class Evidence(BaseModel):
    model_config = ConfigDict(frozen=True)

    section: str
    text: str
    source_url: HttpUrl


class FundingCallCandidate(BaseModel):
    """Source-independent representation produced by every scanner adapter.

    ``*_on`` preserves a known calendar date even when the source provides no clock
    time. ``*_at`` is reserved for an explicitly timed source fact. A candidate may
    therefore have ``application_deadline_on`` without ``application_deadline_at``;
    this is intentionally more precise than inventing midnight or 23:59.
    """

    model_config = ConfigDict(frozen=True)

    external_key: str
    source_code: str
    title: str
    source_url: HttpUrl
    application_opens_on: date | None = None
    application_opens_at: datetime | None = None
    application_deadline_on: date | None = None
    application_deadline_at: datetime | None = None
    description_text: str | None = None
    relevance_status: RelevanceStatus
    relevance_reason: str
    evidence: tuple[Evidence, ...] = ()
