from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class FundingReportStatus(StrEnum):
    DRAFT = "DRAFT"
    WAITING_APPROVAL = "WAITING_APPROVAL"


class FundingReportDraftCreate(BaseModel):
    title: str = Field(default="VakeHyvän rahoitusraportti", min_length=1, max_length=200)
    notes: str | None = Field(default=None, max_length=10_000)
    funding_call_ids: list[int] = Field(min_length=1, max_length=100)

    @field_validator("funding_call_ids")
    @classmethod
    def validate_call_ids(cls, values: list[int]) -> list[int]:
        if any(value <= 0 for value in values):
            raise ValueError("funding_call_ids must contain positive IDs")
        if len(set(values)) != len(values):
            raise ValueError("funding_call_ids must not contain duplicates")
        return values


class FundingReportItemResponse(BaseModel):
    funding_call_id: int
    funding_call_version: int
    position: int
    snapshot: dict[str, Any]


class FundingReportResponse(BaseModel):
    id: UUID
    title: str
    status: FundingReportStatus
    notes: str | None
    created_at: datetime
    updated_at: datetime
    submitted_for_approval_at: datetime | None
    items: list[FundingReportItemResponse]
