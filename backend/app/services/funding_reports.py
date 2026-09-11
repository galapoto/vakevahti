from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.report_schemas import (
    FundingReportDraftCreate,
    FundingReportItemResponse,
    FundingReportResponse,
    FundingReportStatus,
)
from app.db.models import FundingCallRecord
from app.db.report_models import FundingReport, FundingReportItem


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
        notes=report.notes,
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
    """Persist a report draft and immutable snapshots of its selected funding calls."""

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
        notes=draft.notes.strip() if draft.notes and draft.notes.strip() else None,
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
