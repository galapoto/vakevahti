from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


def _normalized_token(value: str) -> str:
    normalized = value.strip().upper().replace("-", "_").replace(" ", "_")
    if not normalized:
        raise ValueError("value must not be empty")
    return normalized


def _normalize_recipients(values: list[str]) -> list[str]:
    recipients: list[str] = []
    seen: set[str] = set()
    for raw in values:
        value = raw.strip()
        if not value:
            continue
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError(f"Invalid recipient email: {value}")
        key = value.casefold()
        if key not in seen:
            seen.add(key)
            recipients.append(value)
    if not recipients:
        raise ValueError("At least one recipient email is required")
    if len(recipients) > 50:
        raise ValueError("recipient_emails may contain at most 50 addresses")
    return recipients


class FundingCaseArtifactCreate(BaseModel):
    source_app: str = Field(min_length=1, max_length=64)
    artifact_type: str = Field(min_length=1, max_length=64)
    external_artifact_id: str = Field(min_length=1, max_length=256)
    version: int = Field(default=1, ge=1)
    status: str = Field(default="DRAFT", min_length=1, max_length=32)
    title: str = Field(min_length=1, max_length=500)
    summary: str | None = Field(default=None, max_length=10_000)
    content_url: str | None = Field(default=None, max_length=4_000)
    content_text: str | None = Field(default=None, max_length=30_000)
    mime_type: str | None = Field(default=None, max_length=128)
    checksum: str | None = Field(default=None, max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)
    approved_at: datetime | None = None

    @field_validator("source_app", "artifact_type", "status")
    @classmethod
    def normalize_tokens(cls, value: str) -> str:
        return _normalized_token(value)


class FundingCaseArtifactResponse(BaseModel):
    id: UUID
    case_id: UUID
    source_app: str
    artifact_type: str
    external_artifact_id: str
    version: int
    status: str
    title: str
    summary: str | None
    content_url: str | None
    content_text: str | None
    mime_type: str | None
    checksum: str | None
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    approved_at: datetime | None


class FundingCaseTaskResponse(BaseModel):
    id: int
    task_key: str
    title: str
    detail: str
    status: str
    due_on: date | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


class FundingCaseCallSummary(BaseModel):
    id: int
    source_code: str
    title: str
    source_url: str
    application_deadline_on: date | None
    application_deadline_at: datetime | None
    relevance_status: str
    relevance_reason: str
    current_version: int


class FundingCaseResponse(BaseModel):
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    funding_call: FundingCaseCallSummary
    artifacts: list[FundingCaseArtifactResponse] = Field(default_factory=list)
    tasks: list[FundingCaseTaskResponse] = Field(default_factory=list)
    next_action: str = ""


class FundingCaseEmailPackage(BaseModel):
    case_id: UUID
    subject: str
    body: str
    included_artifacts: list[FundingCaseArtifactResponse]


class FundingCaseEmailSendRequest(BaseModel):
    recipient_emails: list[str]
    subject: str | None = Field(default=None, max_length=500)
    body: str | None = Field(default=None, max_length=50_000)
    artifact_ids: list[UUID] | None = Field(default=None, max_length=100)

    @field_validator("recipient_emails")
    @classmethod
    def validate_recipients(cls, values: list[str]) -> list[str]:
        return _normalize_recipients(values)


class FundingCaseEmailQueueResponse(BaseModel):
    case_id: UUID
    report_id: UUID
    delivery_id: int
    delivery_status: str
    recipients: list[str]
