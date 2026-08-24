from datetime import datetime
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
    """Source-independent representation produced by every scanner adapter."""

    model_config = ConfigDict(frozen=True)

    external_key: str
    source_code: str
    title: str
    source_url: HttpUrl
    application_opens_at: datetime | None = None
    application_deadline_at: datetime | None = None
    description_text: str | None = None
    relevance_status: RelevanceStatus
    relevance_reason: str
    evidence: tuple[Evidence, ...] = ()
