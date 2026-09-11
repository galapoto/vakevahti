from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FundingReport(Base):
    """Persisted employee funding report and its editable delivery composition."""

    __tablename__ = "funding_reports"
    __table_args__ = (
        Index("ix_funding_reports_status_updated", "status", "updated_at"),
        UniqueConstraint(
            "automation_key",
            name="uq_funding_reports_automation_key",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    origin: Mapped[str] = mapped_column(String(32), nullable=False, default="MANUAL")
    automation_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    email_subject: Mapped[str | None] = mapped_column(Text, nullable=True)
    email_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    recipient_emails: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_for_approval_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class FundingReportItem(Base):
    """Immutable funding-call snapshot included in one report version."""

    __tablename__ = "funding_report_items"
    __table_args__ = (
        UniqueConstraint(
            "report_id",
            "funding_call_id",
            name="uq_funding_report_items_report_call",
        ),
        UniqueConstraint(
            "report_id",
            "position",
            name="uq_funding_report_items_report_position",
        ),
        Index("ix_funding_report_items_report_position", "report_id", "position"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    report_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("funding_reports.id", ondelete="CASCADE"),
        nullable=False,
    )
    funding_call_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("funding_calls.id"),
        nullable=False,
    )
    funding_call_version: Mapped[int] = mapped_column(Integer, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
