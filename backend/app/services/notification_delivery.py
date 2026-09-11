from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import NotificationOutbox
from app.services.notification_outbox import OutboxStatus


class StaleOutboxClaimError(RuntimeError):
    """Raised when a worker tries to settle an outbox row it no longer owns."""


@dataclass(frozen=True)
class OutboxDeliveryClaim:
    id: int
    claim_token: UUID
    dedupe_key: str
    event_type: str
    payload: dict[str, Any]
    attempt_count: int
    claim_expires_at: datetime


def _clear_claim(row: NotificationOutbox) -> None:
    row.claimed_at = None
    row.claim_expires_at = None
    row.claim_token = None


async def claim_notification_intents(
    session: AsyncSession,
    *,
    limit: int = 20,
    now: datetime | None = None,
    lease_seconds: int = 120,
) -> tuple[OutboxDeliveryClaim, ...]:
    """Lease pending/retryable intents using PostgreSQL row locking.

    `FOR UPDATE SKIP LOCKED` lets multiple transport workers claim different rows
    safely. An expired PROCESSING lease is reclaimable after a worker crash. The
    returned token must be supplied when settling the delivery so a stale worker
    cannot overwrite the result of a newer claim.
    """

    if limit < 1 or limit > 500:
        raise ValueError("limit must be between 1 and 500")
    if lease_seconds < 1:
        raise ValueError("lease_seconds must be positive")

    now = now or datetime.now(UTC)
    lease_until = now + timedelta(seconds=lease_seconds)

    ready_status = and_(
        NotificationOutbox.status.in_(
            [OutboxStatus.PENDING.value, OutboxStatus.FAILED.value]
        ),
        or_(
            NotificationOutbox.next_attempt_at.is_(None),
            NotificationOutbox.next_attempt_at <= now,
        ),
    )
    expired_lease = and_(
        NotificationOutbox.status == OutboxStatus.PROCESSING.value,
        NotificationOutbox.claim_expires_at.is_not(None),
        NotificationOutbox.claim_expires_at <= now,
    )

    statement = (
        select(NotificationOutbox)
        .where(or_(ready_status, expired_lease))
        .order_by(NotificationOutbox.created_at, NotificationOutbox.id)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    rows = (await session.scalars(statement)).all()

    claims: list[OutboxDeliveryClaim] = []
    for row in rows:
        token = uuid4()
        row.status = OutboxStatus.PROCESSING.value
        row.attempt_count += 1
        row.claimed_at = now
        row.claim_expires_at = lease_until
        row.claim_token = token
        row.next_attempt_at = None
        claims.append(
            OutboxDeliveryClaim(
                id=row.id,
                claim_token=token,
                dedupe_key=row.dedupe_key,
                event_type=row.event_type,
                payload=dict(row.payload),
                attempt_count=row.attempt_count,
                claim_expires_at=lease_until,
            )
        )

    await session.flush()
    return tuple(claims)


async def _owned_processing_row(
    session: AsyncSession,
    *,
    outbox_id: int,
    claim_token: UUID,
) -> NotificationOutbox:
    statement = (
        select(NotificationOutbox)
        .where(
            NotificationOutbox.id == outbox_id,
            NotificationOutbox.status == OutboxStatus.PROCESSING.value,
            NotificationOutbox.claim_token == claim_token,
        )
        .with_for_update()
    )
    row = (await session.scalars(statement)).one_or_none()
    if row is None:
        raise StaleOutboxClaimError(
            f"Notification outbox row {outbox_id} is not owned by claim {claim_token}."
        )
    return row


async def mark_notification_sent(
    session: AsyncSession,
    *,
    outbox_id: int,
    claim_token: UUID,
    sent_at: datetime | None = None,
) -> None:
    """Acknowledge successful platform delivery for the currently owned lease."""

    row = await _owned_processing_row(
        session,
        outbox_id=outbox_id,
        claim_token=claim_token,
    )
    row.status = OutboxStatus.SENT.value
    row.sent_at = sent_at or datetime.now(UTC)
    row.last_error = None
    row.next_attempt_at = None
    _clear_claim(row)
    await session.flush()


async def mark_notification_failed(
    session: AsyncSession,
    *,
    outbox_id: int,
    claim_token: UUID,
    error: str,
    next_attempt_at: datetime,
) -> None:
    """Record a transport failure without losing the durable event intent."""

    row = await _owned_processing_row(
        session,
        outbox_id=outbox_id,
        claim_token=claim_token,
    )
    row.status = OutboxStatus.FAILED.value
    row.last_error = error[:2000]
    row.next_attempt_at = next_attempt_at
    _clear_claim(row)
    await session.flush()
