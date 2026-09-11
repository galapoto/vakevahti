from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from hashlib import sha256
from uuid import UUID, uuid4

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.report_schemas import FundingReportResponse
from app.db.report_models import FundingReportDelivery
from app.services.report_email_renderer import render_report_email_html


class ReportDeliveryStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SENT = "SENT"
    FAILED = "FAILED"


class StaleReportDeliveryClaimError(RuntimeError):
    """Raised when a worker tries to settle a report email lease it no longer owns."""


@dataclass(frozen=True)
class ReportEmailClaim:
    id: int
    report_id: UUID
    claim_token: UUID
    recipient_emails: tuple[str, ...]
    subject: str
    body_text: str
    body_html: str
    attempt_count: int
    claim_expires_at: datetime


def _delivery_key(report: FundingReportResponse) -> str:
    material = "\n".join(
        [
            str(report.id),
            "\x1f".join(report.recipient_emails),
            report.email_subject or "",
            report.email_body or "",
        ]
    )
    return "report-email:" + sha256(material.encode("utf-8")).hexdigest()


async def enqueue_report_email(
    session: AsyncSession,
    report: FundingReportResponse,
    *,
    created_at: datetime | None = None,
) -> FundingReportDelivery | None:
    """Durably snapshot one report email exactly once for the current composition."""

    recipients = [value.strip() for value in report.recipient_emails if value.strip()]
    subject = (report.email_subject or "").strip()
    body_text = (report.email_body or "").strip()
    if not recipients or not subject or not body_text:
        return None

    dedupe_key = _delivery_key(report)
    existing = (
        await session.scalars(
            select(FundingReportDelivery).where(
                FundingReportDelivery.dedupe_key == dedupe_key
            )
        )
    ).one_or_none()
    if existing is not None:
        return existing

    row = FundingReportDelivery(
        report_id=report.id,
        dedupe_key=dedupe_key,
        channel="EMAIL",
        recipient_emails=recipients,
        subject=subject,
        body_text=body_text,
        body_html=render_report_email_html(report),
        status=ReportDeliveryStatus.PENDING.value,
        attempt_count=0,
        created_at=created_at or datetime.now(UTC),
        next_attempt_at=None,
        claimed_at=None,
        claim_expires_at=None,
        claim_token=None,
        sent_at=None,
        last_error=None,
    )
    session.add(row)
    await session.flush()
    return row


def _clear_claim(row: FundingReportDelivery) -> None:
    row.claimed_at = None
    row.claim_expires_at = None
    row.claim_token = None


async def claim_report_emails(
    session: AsyncSession,
    *,
    limit: int = 10,
    now: datetime | None = None,
    lease_seconds: int = 120,
) -> tuple[ReportEmailClaim, ...]:
    """Lease report emails using PostgreSQL `FOR UPDATE SKIP LOCKED`."""

    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100")
    if lease_seconds < 1:
        raise ValueError("lease_seconds must be positive")

    now = now or datetime.now(UTC)
    lease_until = now + timedelta(seconds=lease_seconds)
    ready = and_(
        FundingReportDelivery.status.in_(
            [ReportDeliveryStatus.PENDING.value, ReportDeliveryStatus.FAILED.value]
        ),
        or_(
            FundingReportDelivery.next_attempt_at.is_(None),
            FundingReportDelivery.next_attempt_at <= now,
        ),
    )
    expired = and_(
        FundingReportDelivery.status == ReportDeliveryStatus.PROCESSING.value,
        FundingReportDelivery.claim_expires_at.is_not(None),
        FundingReportDelivery.claim_expires_at <= now,
    )
    statement = (
        select(FundingReportDelivery)
        .where(or_(ready, expired))
        .order_by(FundingReportDelivery.created_at, FundingReportDelivery.id)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    rows = (await session.scalars(statement)).all()

    claims: list[ReportEmailClaim] = []
    for row in rows:
        token = uuid4()
        row.status = ReportDeliveryStatus.PROCESSING.value
        row.attempt_count += 1
        row.claimed_at = now
        row.claim_expires_at = lease_until
        row.claim_token = token
        row.next_attempt_at = None
        claims.append(
            ReportEmailClaim(
                id=row.id,
                report_id=row.report_id,
                claim_token=token,
                recipient_emails=tuple(row.recipient_emails),
                subject=row.subject,
                body_text=row.body_text,
                body_html=row.body_html,
                attempt_count=row.attempt_count,
                claim_expires_at=lease_until,
            )
        )

    await session.flush()
    return tuple(claims)


async def _owned_delivery(
    session: AsyncSession,
    *,
    delivery_id: int,
    claim_token: UUID,
) -> FundingReportDelivery:
    row = (
        await session.scalars(
            select(FundingReportDelivery)
            .where(
                FundingReportDelivery.id == delivery_id,
                FundingReportDelivery.status == ReportDeliveryStatus.PROCESSING.value,
                FundingReportDelivery.claim_token == claim_token,
            )
            .with_for_update()
        )
    ).one_or_none()
    if row is None:
        raise StaleReportDeliveryClaimError(
            f"Report email delivery {delivery_id} is no longer owned by this claim."
        )
    return row


async def mark_report_email_sent(
    session: AsyncSession,
    *,
    delivery_id: int,
    claim_token: UUID,
    sent_at: datetime | None = None,
) -> None:
    row = await _owned_delivery(
        session,
        delivery_id=delivery_id,
        claim_token=claim_token,
    )
    row.status = ReportDeliveryStatus.SENT.value
    row.sent_at = sent_at or datetime.now(UTC)
    row.last_error = None
    row.next_attempt_at = None
    _clear_claim(row)
    await session.flush()


async def mark_report_email_failed(
    session: AsyncSession,
    *,
    delivery_id: int,
    claim_token: UUID,
    error: str,
    next_attempt_at: datetime,
) -> None:
    row = await _owned_delivery(
        session,
        delivery_id=delivery_id,
        claim_token=claim_token,
    )
    row.status = ReportDeliveryStatus.FAILED.value
    row.last_error = error[:2000]
    row.next_attempt_at = next_attempt_at
    _clear_claim(row)
    await session.flush()


def retry_delay_minutes(
    attempt_count: int,
    *,
    base_minutes: int,
    max_minutes: int,
) -> int:
    """Return capped exponential retry delay for a failed email attempt."""

    if attempt_count < 1:
        raise ValueError("attempt_count must be positive")
    return min(max_minutes, base_minutes * (2 ** (attempt_count - 1)))
