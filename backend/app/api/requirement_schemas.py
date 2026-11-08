from typing import Any

from pydantic import BaseModel, Field


class FundingCaseRequirementResponse(BaseModel):
    requirement_key: str
    category: str
    certainty: str
    title: str
    statement: str
    source_url: str
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    funding_call_version: int = Field(ge=1)
