import json
from datetime import UTC, date, datetime
from hashlib import sha256
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.report_schemas import (
    FundingReportApprovalDecision,
    FundingReportApprovalEventResponse,
    FundingReportDecisionRequest,
    FundingReportDraftCreate,
    FundingReportItemResponse,
    FundingReportListResponse,
    FundingReportOrigin,
    FundingReportResponse,
    FundingReportStatus,
    FundingReportUpdate,
)
from app.db.models import FundingCallRecord, NotificationOutbox
from app.db.report_models import (
    FundingReport,
    FundingReportApprovalEvent,
    FundingReportItem,
)
from app.services.report_composer import ReportFinding, compose_automated_report


class FundingReportNotFoundError(LookupError):
    pass


class FundingReportCallsNotFoundError(LookupError):
    def __init__(self, missing_ids: list[int]) -> None:
        self.missing_ids = missing_ids
        super().__init__(f"Funding calls not found: {missing_ids}")


class FundingReportStateConflictError(RuntimeError):
    pass


def _iso_date(value: date | None) -> str | None:
    return value.isoformat() if value is not None else None


def _iso_datetime(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _snapshot(record: FundingCallRecord) -> dict[str, object]:
    """Freeze the employee-visible funding-call facts used in one report."""

    return {
        "source_code": record.source_code,
        "title": record.title,
        "source_url": record.source_url,
        "application_opens_on": _iso_date(record.application_opens_on),
        "application_opens_at": _iso_datetime(record.application_opens_at),
        "application_deadline_on": _iso_date(record.application_deadline_on),
        "application_deadline_at": _iso_datetime(record.application_deadline_at),
        "relevance_status": record.relevance_status,
        "relevance_reason": record.relevance_reason,
    }


async def _report_items(session: AsyncSession, report_id: UUID) -> list[FundingReportItem]:
    result = await session.execute(
        select(FundingReportItem)
        .where(FundingReportItem.report_id == report_id)
        .order_by(FundingReportItem.position.asc())
    )
    return list(result.scalars())


async def _approval_events(
    session: AsyncSession,
    report_id: UUID,
) -> list[FundingReportApprovalEvent]:
    result = await session.execute(
        select(FundingReportApprovalEvent)
        .where(FundingReportApprovalEvent.report_id == report_id)
        .order_by(
            FundingReportApprovalEvent.decided_at.asc(),
            FundingReportApprovalEvent.id.asc(),
        )
    )
    return list(result.scalars())


def _approval_snapshot(
    report: FundingReport,
    items: list[FundingReportItem],
) -> dict[str, object]:
    """Freeze the exact mutable report composition reviewed by a coordinator."""

    return {
        "report_id": str(report.id),
        "case_id": str(report.case_id) if report.case_id else None,
        "included_artifact_ids": list(report.included_artifact_ids),
        "title": report.title,
        "origin": report.origin,
        "automation_key": report.automation_key,
        "version_number": report.version_number,
        "supersedes_report_id": (
            str(report.supersedes_report_id) if report.supersedes_report_id else None
        ),
        "notes": report.notes,
        "email_subject": report.email_subject,
        "email_body": report.email_body,
        "recipient_emails": list(report.recipient_emails),
        "items": [
            {
                "funding_call_id": item.funding_call_id,
                "funding_call_version": item.funding_call_version,
                "position": item.position,
                "snapshot": item.snapshot,
            }
            for item in items
        ],
    }


def _approval_content_hash(snapshot: dict[str, object]) -> str:
    canonical = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode("utf-8")).hexdigest()


def _approval_event_response(
    event: FundingReportApprovalEvent,
) -> FundingReportApprovalEventResponse:
    return FundingReportApprovalEventResponse(
        id=event.id,
        report_id=event.report_id,
        decision=FundingReportApprovalDecision(event.decision),
        actor_id=event.actor_id,
        actor_display_name=event.actor_display_name,
        actor_source=event.actor_source,
        comment=event.comment,
        decided_at=event.decided_at,
        content_hash=event.content_hash,
        snapshot=event.snapshot,
    )


async def _response(session: AsyncSession, report: FundingReport) -> FundingReportResponse:
    items = await _report_items(session, report.id)
    approval_events = await _approval_events(session, report.id)
    return FundingReportResponse(
        id=report.id,
        case_id=report.case_id,
        included_artifact_ids=[UUID(value) for value in report.included_artifact_ids],
        title=report.title,
        status=FundingReportStatus(report.status),
        origin=FundingReportOrigin(report.origin),
        automation_key=report.automation_key,
        version_number=report.version_number,
        supersedes_report_id=report.supersedes_report_id,
        notes=report.notes,
        email_subject=report.email_subject,
        email_body=report.email_body,
        recipient_emails=list(report.recipient_emails),
        created_at=report.created_at,
        updated_at=report.updated_at,
        submitted_for_approval_at=report.submitted_for_approval_at,
        approval_events=[_approval_event_response(event) for event in approval_events],
        items=[
            FundingReportItemResponse(
                funding_call_id=item.funding_call_id,
                funding_call_version=item.funding_call_version,
                position=item.position,
                snapshot=item.snapshot,
            )
            for item in items
        ],
    )


async def create_funding_report(
    session: AsyncSession,
    draft: FundingReportDraftCreate,
    *,
    case_id: UUID | None = None,
    included_artifact_ids: tuple[UUID, ...] = (),
) -> FundingReportResponse:
    """Persist a report draft and immutable call/case/artifact references."""

    result = await session.execute(
        select(FundingCallRecord).where(FundingCallRecord.id.in_(draft.funding_call_ids))
    )
    records = {record.id: record for record in result.scalars()}
    missing_ids = [call_id for call_id in draft.funding_call_ids if call_id not in records]
    if missing_ids:
        raise FundingReportCallsNotFoundError(missing_ids)

    now = datetime.now(UTC)
    report = FundingReport(
        id=uuid4(),
        case_id=case_id,
        included_artifact_ids=[str(value) for value in included_artifact_ids],
        title=draft.title.strip(),
        status=FundingReportStatus.DRAFT.value,
        origin=FundingReportOrigin.MANUAL.value,
        automation_key=None,
        version_number=1,
        supersedes_report_id=None,
        notes=draft.notes.strip() if draft.notes and draft.notes.strip() else None,
        email_subject=(
            draft.email_subject.strip()
            if draft.email_subject and draft.email_subject.strip()
            else None
        ),
        email_body=(
            draft.email_body.strip()
            if draft.email_body and draft.email_body.strip()
            else None
        ),
        recipient_emails=list(draft.recipient_emails),
        created_at=now,
        updated_at=now,
        submitted_for_approval_at=None,
    )
    session.add(report)
    for position, call_id in enumerate(draft.funding_call_ids, start=1):
        record = records[call_id]
        session.add(
            FundingReportItem(
                report_id=report.id,
                funding_call_id=record.id,
                funding_call_version=record.current_version,
                position=position,
                snapshot=_snapshot(record),
            )
        )

    await session.commit()
    return await _response(session, report)


def _automation_key(scan_run_ids: tuple[UUID, ...]) -> str:
    canonical = "|".join(sorted(str(run_id) for run_id in set(scan_run_ids)))
    return "scan-cycle:" + sha256(canonical.encode("utf-8")).hexdigest()


async def create_automated_funding_report(
    session: AsyncSession,
    *,
    scan_run_ids: tuple[UUID, ...],
    recipient_emails: tuple[str, ...] = (),
    generated_at: datetime | None = None,
) -> FundingReportResponse | None:
    """Create one idempotent report from material events produced by a scan cycle."""

    if not scan_run_ids:
        return None

    automation_key = _automation_key(scan_run_ids)
    existing_result = await session.execute(
        select(FundingReport).where(FundingReport.automation_key == automation_key)
    )
    existing = existing_result.scalar_one_or_none()
    if existing is not None:
        return await _response(session, existing)

    event_result = await session.execute(
        select(NotificationOutbox)
        .where(NotificationOutbox.source_scan_run_id.in_(scan_run_ids))
        .order_by(NotificationOutbox.created_at.asc(), NotificationOutbox.id.asc())
    )
    events = list(event_result.scalars())
    if not events:
        return None

    call_ids: list[int] = []
    event_by_call: dict[int, str] = {}
    for event in events:
        if event.funding_call_id not in event_by_call:
            call_ids.append(event.funding_call_id)
            event_by_call[event.funding_call_id] = event.event_type

    record_result = await session.execute(
        select(FundingCallRecord).where(FundingCallRecord.id.in_(call_ids))
    )
    records = {record.id: record for record in record_result.scalars()}
    missing_ids = [call_id for call_id in call_ids if call_id not in records]
    if missing_ids:
        raise FundingReportCallsNotFoundError(missing_ids)

    findings = [
        ReportFinding(
            funding_call_id=record.id,
            source_code=record.source_code,
            title=record.title,
            source_url=record.source_url,
            relevance_status=record.relevance_status,
            relevance_reason=record.relevance_reason,
            event_type=event_by_call[record.id],
            application_deadline_on=record.application_deadline_on,
            application_deadline_at=record.application_deadline_at,
        )
        for record in (records[call_id] for call_id in call_ids)
    ]
    now = generated_at or datetime.now(UTC)
    composition = compose_automated_report(
        findings,
        generated_at=now,
        recipient_emails=recipient_emails,
    )

    report = FundingReport(
        id=uuid4(),
        case_id=None,
        included_artifact_ids=[],
        title=composition.title,
        status=FundingReportStatus.DRAFT.value,
        origin=FundingReportOrigin.AUTOMATED.value,
        automation_key=automation_key,
        version_number=1,
        supersedes_report_id=None,
        notes=composition.notes,
        email_subject=composition.email_subject,
        email_body=composition.email_body,
        recipient_emails=list(composition.recipient_emails),
        created_at=now,
        updated_at=now,
        submitted_for_approval_at=None,
    )
    session.add(report)
    for position, finding in enumerate(findings, start=1):
        record = records[finding.funding_call_id]
        snapshot = _snapshot(record)
        snapshot["event_type"] = finding.event_type
        session.add(
            FundingReportItem(
                report_id=report.id,
                funding_call_id=record.id,
                funding_call_version=record.current_version,
                position=position,
                snapshot=snapshot,
            )
        )

    await session.commit()
    return await _response(session, report)


async def get_funding_report(
    session: AsyncSession,
    report_id: UUID,
) -> FundingReportResponse:
    result = await session.execute(
        select(FundingReport).where(FundingReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise FundingReportNotFoundError(str(report_id))
    return await _response(session, report)


async def list_funding_reports(
    session: AsyncSession,
    *,
    status: FundingReportStatus | None = None,
    limit: int = 25,
    offset: int = 0,
) -> FundingReportListResponse:
    """Return a bounded coordinator queue without exposing report tables directly."""

    if limit < 1 or limit > 50:
        raise ValueError("limit must be between 1 and 50")
    if offset < 0:
        raise ValueError("offset must be non-negative")

    filters = []
    if status is not None:
        filters.append(FundingReport.status == status.value)

    total = int(
        (
            await session.scalar(
                select(func.count(FundingReport.id)).where(*filters)
            )
        )
        or 0
    )
    rows = list(
        (
            await session.scalars(
                select(FundingReport)
                .where(*filters)
                .order_by(FundingReport.updated_at.desc(), FundingReport.id.asc())
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )
    return FundingReportListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[await _response(session, report) for report in rows],
    )


async def get_latest_funding_report(
    session: AsyncSession,
) -> FundingReportResponse | None:
    result = await session.execute(
        select(FundingReport).order_by(FundingReport.created_at.desc()).limit(1)
    )
    report = result.scalar_one_or_none()
    if report is None:
        return None
    return await _response(session, report)


async def revise_approved_funding_report(
    session: AsyncSession,
    report_id: UUID,
) -> FundingReportResponse:
    """Create one idempotent successor draft without mutating the approved version."""

    result = await session.execute(
        select(FundingReport)
        .where(FundingReport.id == report_id)
        .with_for_update()
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise FundingReportNotFoundError(str(report_id))
    if report.status != FundingReportStatus.APPROVED.value:
        raise FundingReportStateConflictError(
            "Only an approved report can be revised into a successor version."
        )

    existing = (
        await session.scalars(
            select(FundingReport).where(FundingReport.supersedes_report_id == report.id)
        )
    ).one_or_none()
    if existing is not None:
        return await _response(session, existing)

    items = await _report_items(session, report.id)
    now = datetime.now(UTC)
    successor = FundingReport(
        id=uuid4(),
        case_id=report.case_id,
        included_artifact_ids=list(report.included_artifact_ids),
        title=report.title,
        status=FundingReportStatus.DRAFT.value,
        origin=FundingReportOrigin.MANUAL.value,
        automation_key=None,
        version_number=report.version_number + 1,
        supersedes_report_id=report.id,
        notes=report.notes,
        email_subject=report.email_subject,
        email_body=report.email_body,
        recipient_emails=list(report.recipient_emails),
        created_at=now,
        updated_at=now,
        submitted_for_approval_at=None,
    )
    session.add(successor)
    for item in items:
        session.add(
            FundingReportItem(
                report_id=successor.id,
                funding_call_id=item.funding_call_id,
                funding_call_version=item.funding_call_version,
                position=item.position,
                snapshot=dict(item.snapshot),
            )
        )

    await session.commit()
    return await _response(session, successor)


async def update_funding_report(
    session: AsyncSession,
    report_id: UUID,
    update: FundingReportUpdate,
) -> FundingReportResponse:
    """Edit a report while preserving completed approval evidence."""

    result = await session.execute(
        select(FundingReport).where(FundingReport.id == report_id).with_for_update()
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise FundingReportNotFoundError(str(report_id))
    if report.status == FundingReportStatus.APPROVED.value:
        raise FundingReportStateConflictError(
            "Approved reports are immutable; create a new report version to make changes."
        )

    fields = update.model_fields_set
    if "title" in fields and update.title is not None:
        report.title = update.title.strip()
    if "notes" in fields:
        report.notes = update.notes.strip() if update.notes and update.notes.strip() else None
    if "email_subject" in fields:
        report.email_subject = (
            update.email_subject.strip()
            if update.email_subject and update.email_subject.strip()
            else None
        )
    if "email_body" in fields:
        report.email_body = (
            update.email_body.strip()
            if update.email_body and update.email_body.strip()
            else None
        )
    if "recipient_emails" in fields and update.recipient_emails is not None:
        report.recipient_emails = list(update.recipient_emails)

    if fields:
        report.updated_at = datetime.now(UTC)
        if report.status in {
            FundingReportStatus.WAITING_APPROVAL.value,
            FundingReportStatus.REJECTED.value,
        }:
            report.status = FundingReportStatus.DRAFT.value
            report.submitted_for_approval_at = None
        await session.commit()

    return await _response(session, report)


async def submit_funding_report_for_approval(
    session: AsyncSession,
    report_id: UUID,
) -> FundingReportResponse:
    """Move one persisted draft to the coordinator-approval queue idempotently."""

    result = await session.execute(
        select(FundingReport)
        .where(FundingReport.id == report_id)
        .with_for_update()
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise FundingReportNotFoundError(str(report_id))

    if report.status == FundingReportStatus.WAITING_APPROVAL.value:
        return await _response(session, report)
    if report.status != FundingReportStatus.DRAFT.value:
        raise FundingReportStateConflictError(
            f"Report in status {report.status} cannot be submitted for approval."
        )

    now = datetime.now(UTC)
    report.status = FundingReportStatus.WAITING_APPROVAL.value
    report.updated_at = now
    report.submitted_for_approval_at = now
    await session.commit()
    return await _response(session, report)


async def decide_funding_report(
    session: AsyncSession,
    report_id: UUID,
    decision: FundingReportDecisionRequest,
    *,
    actor_source: str = "CLIENT_ASSERTED",
) -> FundingReportResponse:
    """Record one append-only coordinator decision against an immutable composition snapshot."""

    result = await session.execute(
        select(FundingReport)
        .where(FundingReport.id == report_id)
        .with_for_update()
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise FundingReportNotFoundError(str(report_id))

    items = await _report_items(session, report.id)
    snapshot = _approval_snapshot(report, items)
    content_hash = _approval_content_hash(snapshot)
    events = await _approval_events(session, report.id)
    latest = events[-1] if events else None

    if report.status != FundingReportStatus.WAITING_APPROVAL.value:
        if (
            latest is not None
            and latest.decision == decision.decision.value
            and latest.content_hash == content_hash
        ):
            return await _response(session, report)
        raise FundingReportStateConflictError(
            f"Report in status {report.status} is not waiting for approval."
        )

    now = datetime.now(UTC)
    event = FundingReportApprovalEvent(
        id=uuid4(),
        report_id=report.id,
        decision=decision.decision.value,
        actor_id=decision.actor_id,
        actor_display_name=decision.actor_display_name,
        actor_source=actor_source,
        comment=decision.comment,
        decided_at=now,
        content_hash=content_hash,
        snapshot=snapshot,
    )
    session.add(event)

    if decision.decision is FundingReportApprovalDecision.APPROVE:
        report.status = FundingReportStatus.APPROVED.value
    elif decision.decision is FundingReportApprovalDecision.RETURN_FOR_EDIT:
        report.status = FundingReportStatus.DRAFT.value
        report.submitted_for_approval_at = None
    else:
        report.status = FundingReportStatus.REJECTED.value
    report.updated_at = now

    await session.commit()
    return await _response(session, report)
