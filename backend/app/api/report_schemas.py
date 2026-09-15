from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class FundingReportStatus(StrEnum):
    DRAFT = "DRAFT"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class FundingReportApprovalDecision(StrEnum):
    APPROVE = "APPROVE"
    RETURN_FOR_EDIT = "RETURN_FOR_EDIT"
    REJECT = "REJECT"


class FundingReportOrigin(StrEnum):
    MANUAL = "MANUAL"
    AUTOMATED = "AUTOMATED"


def _normalize_recipients(values: list[str]) -> list[str]:
    recipients: list[str] = []
    seen: set[str] = set()
    for raw in values:
        value = raw.strip()
        if not value:
            continue
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError(f"Invalid recipient email: {value}")
        lowered = value.casefold()
        if lowered in seen:
            continue
        seen.add(lowered)
        recipients.append(value)
    if len(recipients) > 50:
        raise ValueError("recipient_emails may contain at most 50 addresses")
    return recipients


class FundingReportDraftCreate(BaseModel):
    title: str = Field(default="VakeHyvän rahoitusraportti", min_length=1, max_length=200)
    notes: str | None = Field(default=None, max_length=10_000)
    email_subject: str | None = Field(default=None, max_length=500)
    email_body: str | None = Field(default=None, max_length=50_000)
    recipient_emails: list[str] = Field(default_factory=list)
    funding_call_ids: list[int] = Field(min_length=1, max_length=100)

    @field_validator("funding_call_ids")
    @classmethod
    def validate_call_ids(cls, values: list[int]) -> list[int]:
        if any(value <= 0 for value in values):
            raise ValueError("funding_call_ids must contain positive IDs")
        if len(set(values)) != len(values):
            raise ValueError("funding_call_ids must not contain duplicates")
        return values

    @field_validator("recipient_emails")
    @classmethod
    def validate_recipients(cls, values: list[str]) -> list[str]:
        return _normalize_recipients(values)


class FundingReportUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    notes: str | None = Field(default=None, max_length=10_000)
    email_subject: str | None = Field(default=None, max_length=500)
    email_body: str | None = Field(default=None, max_length=50_000)
    recipient_emails: list[str] | None = None

    @field_validator("recipient_emails")
    @classmethod
    def validate_recipients(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return None
        return _normalize_recipients(values)


class FundingReportDecisionRequest(BaseModel):
    decision: FundingReportApprovalDecision
    actor_id: str = Field(min_length=1, max_length=255)
    actor_display_name: str | None = Field(default=None, max_length=255)
    comment: str | None = Field(default=None, max_length=4000)

    @field_validator("actor_id")
    @classmethod
    def strip_actor_id(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("actor_id must not be blank")
        return stripped

    @field_validator("actor_display_name", "comment")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    def require_decision_reason(self) -> "FundingReportDecisionRequest":
        if self.decision in {
            FundingReportApprovalDecision.RETURN_FOR_EDIT,
            FundingReportApprovalDecision.REJECT,
        } and not self.comment:
            raise ValueError("comment is required when returning or rejecting a report")
        return self


class FundingReportApprovalEventResponse(BaseModel):
    id: UUID
    report_id: UUID
    decision: FundingReportApprovalDecision
    actor_id: str
    actor_display_name: str | None
    actor_source: str
    comment: str | None
    decided_at: datetime
    content_hash: str
    snapshot: dict[str, Any]


class FundingReportItemResponse(BaseModel):
    funding_call_id: int
    funding_call_version: int
    position: int
    snapshot: dict[str, Any]


class FundingReportResponse(BaseModel):
    id: UUID
    case_id: UUID | None = None
    included_artifact_ids: list[UUID] = Field(default_factory=list)
    title: str
    status: FundingReportStatus
    origin: FundingReportOrigin
    automation_key: str | None
    version_number: int = 1
    supersedes_report_id: UUID | None = None
    notes: str | None
    email_subject: str | None
    email_body: str | None
    recipient_emails: list[str]
    created_at: datetime
    updated_at: datetime
    submitted_for_approval_at: datetime | None
    approval_events: list[FundingReportApprovalEventResponse] = Field(default_factory=list)
    items: list[FundingReportItemResponse]


class FundingReportListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[FundingReportResponse]
