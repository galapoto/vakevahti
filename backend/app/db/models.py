from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
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


class FundingCallRecord(Base):
    __tablename__ = "funding_calls"
    __table_args__ = (
        UniqueConstraint(
            "source_code",
            "external_key",
            name="uq_funding_calls_source_external_key",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    source_code: Mapped[str] = mapped_column(String(32), nullable=False)
    external_key: Mapped[str] = mapped_column(String(256), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    application_opens_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    application_deadline_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    description_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    relevance_status: Mapped[str] = mapped_column(String(32), nullable=False)
    relevance_reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    current_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class FundingCallVersion(Base):
    __tablename__ = "funding_call_versions"
    __table_args__ = (
        UniqueConstraint(
            "funding_call_id",
            "version_number",
            name="uq_funding_call_versions_call_version",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    funding_call_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("funding_calls.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SourceState(Base):
    __tablename__ = "source_states"

    source_code: Mapped[str] = mapped_column(String(32), primary_key=True)
    baseline_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_successful_scan_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class SourceScanRun(Base):
    """Operational audit record for one source ingestion attempt."""

    __tablename__ = "source_scan_runs"
    __table_args__ = (
        Index("ix_source_scan_runs_source_started", "source_code", "started_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    source_code: Mapped[str] = mapped_column(String(32), nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    baseline: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    discovered_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    new_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unchanged_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    changed_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
