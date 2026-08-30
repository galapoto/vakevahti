from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.services.reads import SourceHealthStatus


class FundingCallListItem(BaseModel):
    """Stable current-state summary exposed by the funding list API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    source_code: str
    title: str
    source_url: str
    application_opens_at: datetime | None
    application_deadline_at: datetime | None
    relevance_status: str
    current_version: int
    first_seen_at: datetime
    last_seen_at: datetime


class FundingCallDetail(FundingCallListItem):
    description_text: str | None
    relevance_reason: str
    evidence: list[dict[str, Any]]


class FundingCallListResponse(BaseModel):
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)
    items: list[FundingCallListItem]


class SourceHealthItem(BaseModel):
    source_code: str
    health: SourceHealthStatus
    current_call_count: int = Field(ge=0)
    baseline_completed_at: datetime | None
    last_successful_scan_at: datetime | None
    latest_scan_id: UUID | None
    latest_scan_status: str | None
    latest_scan_trigger: str | None
    latest_scan_started_at: datetime | None
    latest_scan_completed_at: datetime | None
    latest_scan_baseline: bool | None
    latest_discovered_count: int | None = Field(default=None, ge=0)
    latest_new_count: int | None = Field(default=None, ge=0)
    latest_unchanged_count: int | None = Field(default=None, ge=0)
    latest_changed_count: int | None = Field(default=None, ge=0)
    latest_error_type: str | None


class SourceHealthResponse(BaseModel):
    sources: list[SourceHealthItem]
