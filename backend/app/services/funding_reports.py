from datetime import UTC, date, datetime
from hashlib import sha256
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.report_schemas import (
    FundingReportDraftCreate,
    FundingReportItemResponse,
    FundingReportOrigin,
    FundingReportResponse,
    FundingReportStatus,
    FundingReportUpdate,
)
from app.db.models import FundingCallRecord, NotificationOutbox
from app.db.report_models import FundingReport, FundingReportItem
from app.services.report_composer import ReportFinding, compose_automated_report


class FundingReportNotFoundError(LookupError):
    pass


class FundingReportCallsNotFoundError(LookupError):
    def __init__(self, missing_ids: list[int]) -> None:
        self.missing_ids = missing_ids
        super().__init__(f"Funding calls not found: {missing_ids}")


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


async def _response(session: AsyncSession, report: FundingReport) -> FundingReportResponse:
    item_result = await session.execute(
        select(FundingReportItem)
        .where(FundingReportItem.report_id == report.id)
        .order_by(FundingReportItem.position.asc())
    )
    items = list(item_result.scalars())
    return FundingReportResponse(
        id=report.id,
        title=report.title,
        status=FundingReportStatus(report.status),
        origin=FundingReportOrigin(report.origin),
        automation_key=report.automation_key,
        notes=report.notes,
        email_subject=report.email_subject,
        email_body=report.email_body,
        recipient_emails=list(report.recipient_emails),
        created_at=report.created_at,
        updated_at=report.updated_at,
        submitted_for_approval_at=report.submitted_for_approval_at,
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
) -> FundingReportResponse:
    """Persist a manually prepared report draft and immutable call snapshots."""

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
        title=draft.title.strip(),
        status=FundingReportStatus.DRAFT.value,
        origin=FundingReportOrigin.MANUAL.value,
        automation_key=None,
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
        title=composition.title,
        status=FundingReportStatus.DRAFT.value,
        origin=FundingReportOrigin.AUTOMATED.value,
        automation_key=automation_key,
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


async def update_funding_report(
    session: AsyncSession,
    report_id: UUID,
    update: FundingReportUpdate,
) -> FundingReportResponse:
    """Edit a generated/manual report and invalidate prior approval after any edit."""

    result = await session.execute(
        select(FundingReport).where(FundingReport.id == report_id).with_for_update()
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise FundingReportNotFoundError(str(report_id))

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
        if report.status == FundingReportStatus.WAITING_APPROVAL.value:
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

    if report.status == FundingReportStatus.DRAFT.value:
        now = datetime.now(UTC)
        report.status = FundingReportStatus.WAITING_APPROVAL.value
        report.updated_at = now
        report.submitted_for_approval_at = now
        await session.commit()

    return await _response(session, report)
