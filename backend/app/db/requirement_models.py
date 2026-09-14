from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, Index, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FundingCaseRequirement(Base):
    """Versioned, source-grounded requirement projection for one funding case."""

    __tablename__ = "funding_case_requirements"
    __table_args__ = (
        UniqueConstraint(
            "case_id",
            "funding_call_version",
            "requirement_key",
            name="uq_funding_case_requirement_version_key",
        ),
        Index(
            "ix_funding_case_requirements_case_version",
            "case_id",
            "funding_call_version",
        ),
        Index(
            "ix_funding_case_requirements_certainty",
            "certainty",
            "category",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("funding_cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    funding_call_version: Mapped[int] = mapped_column(Integer, nullable=False)
    requirement_key: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    certainty: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
