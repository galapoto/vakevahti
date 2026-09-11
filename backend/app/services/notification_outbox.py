from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import FundingCallRecord, NotificationOutbox
from app.domain.funding_call import FundingCallCandidate, RelevanceStatus


class OutboxStatus(StrEnum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class FundingNotificationEvent(StrEnum):
    DISCOVERED = "funding.opportunity.discovered.v1"
    CHANGED = "funding.opportunity.changed.v1"
    REVIEW_REQUIRED = "funding.opportunity.review_required.v1"


def notification_event_type(
    *,
    baseline: bool,
    change_status: str,
    relevance_status: RelevanceStatus,
) -> FundingNotificationEvent | None:
    """Map persisted Funding facts to one durable notification intent.

    The first source baseline is suppressed. Proven NOT_RELEVANT rows remain stored for
    lineage but never create operator notifications. New reviewable rows create a review
    event; changed reviewable rows do the same. Other visible material changes use the
    versioned changed event so transport policy can decide how to surface them.
    """

    if baseline or relevance_status is RelevanceStatus.NOT_RELEVANT:
        return None

    if change_status == "NEW":
        if relevance_status is RelevanceStatus.NEEDS_REVIEW:
            return FundingNotificationEvent.REVIEW_REQUIRED
        return FundingNotificationEvent.DISCOVERED

    if change_status == "CHANGED":
        if relevance_status is RelevanceStatus.NEEDS_REVIEW:
            return FundingNotificationEvent.REVIEW_REQUIRED
        return FundingNotificationEvent.CHANGED

    return None


def notification_dedupe_key(
    *,
    event_type: FundingNotificationEvent,
    funding_call_id: int,
    source_scan_run_id: UUID,
) -> str:
    """Identify one call event within one authoritative source-scan occurrence."""

    return f"{event_type.value}|{funding_call_id}|{source_scan_run_id}"


async def enqueue_notification_intent(
    session: AsyncSession,
    *,
    event_type: FundingNotificationEvent,
    record: FundingCallRecord,
    candidate: FundingCallCandidate,
    source_scan_run_id: UUID,
    observed_at: datetime,
) -> NotificationOutbox:
    """Add a transport-neutral outbox row inside the caller's database transaction."""

    outbox = NotificationOutbox(
        dedupe_key=notification_dedupe_key(
            event_type=event_type,
            funding_call_id=record.id,
            source_scan_run_id=source_scan_run_id,
        ),
        event_type=event_type.value,
        funding_call_id=record.id,
        funding_call_version=record.current_version,
        source_scan_run_id=source_scan_run_id,
        payload={
            "event_type": event_type.value,
            "funding_call_id": record.id,
            "funding_call_version": record.current_version,
            "source_code": record.source_code,
            "external_key": record.external_key,
            "title": candidate.title,
            "source_url": str(candidate.source_url),
            "relevance_status": candidate.relevance_status.value,
            "relevance_reason": candidate.relevance_reason,
            "source_scan_run_id": str(source_scan_run_id),
            "observed_at": observed_at.isoformat(),
        },
        status=OutboxStatus.PENDING.value,
        attempt_count=0,
        created_at=observed_at,
    )
    session.add(outbox)
    await session.flush()
    return outbox
