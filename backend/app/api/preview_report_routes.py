from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status

from app.api.preview_routes import _PREVIEW_CALLS
from app.api.report_schemas import (
    FundingReportDraftCreate,
    FundingReportItemResponse,
    FundingReportResponse,
    FundingReportStatus,
)
from app.api.schemas import FundingCallDetail

router = APIRouter(prefix="/api/reports", tags=["reports"])
_REPORTS: dict[UUID, FundingReportResponse] = {}


def _snapshot(funding_call: FundingCallDetail) -> dict[str, object]:
    return {
        "source_code": funding_call.source_code,
        "title": funding_call.title,
        "source_url": funding_call.source_url,
        "application_opens_on": (
            funding_call.application_opens_on.isoformat()
            if funding_call.application_opens_on
            else None
        ),
        "application_opens_at": (
            funding_call.application_opens_at.isoformat()
            if funding_call.application_opens_at
            else None
        ),
        "application_deadline_on": (
            funding_call.application_deadline_on.isoformat()
            if funding_call.application_deadline_on
            else None
        ),
        "application_deadline_at": (
            funding_call.application_deadline_at.isoformat()
            if funding_call.application_deadline_at
            else None
        ),
        "relevance_status": funding_call.relevance_status,
        "relevance_reason": funding_call.relevance_reason,
    }


@router.post(
    "",
    response_model=FundingReportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_report(draft: FundingReportDraftCreate) -> FundingReportResponse:
    calls = {call.id: call for call in _PREVIEW_CALLS}
    missing = [call_id for call_id in draft.funding_call_ids if call_id not in calls]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"missing_funding_call_ids": missing},
        )

    now = datetime.now(UTC)
    report = FundingReportResponse(
        id=uuid4(),
        title=draft.title.strip(),
        status=FundingReportStatus.DRAFT,
        notes=draft.notes.strip() if draft.notes and draft.notes.strip() else None,
        created_at=now,
        updated_at=now,
        submitted_for_approval_at=None,
        items=[
            FundingReportItemResponse(
                funding_call_id=call_id,
                funding_call_version=calls[call_id].current_version,
                position=position,
                snapshot=_snapshot(calls[call_id]),
            )
            for position, call_id in enumerate(draft.funding_call_ids, start=1)
        ],
    )
    _REPORTS[report.id] = report
    return report


@router.get("/{report_id}", response_model=FundingReportResponse)
async def report_detail(report_id: UUID) -> FundingReportResponse:
    report = _REPORTS.get(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Funding report not found.")
    return report


@router.post("/{report_id}/submit", response_model=FundingReportResponse)
async def submit_report(report_id: UUID) -> FundingReportResponse:
    report = _REPORTS.get(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Funding report not found.")
    if report.status is FundingReportStatus.WAITING_APPROVAL:
        return report

    now = datetime.now(UTC)
    submitted = report.model_copy(
        update={
            "status": FundingReportStatus.WAITING_APPROVAL,
            "updated_at": now,
            "submitted_for_approval_at": now,
        }
    )
    _REPORTS[report_id] = submitted
    return submitted
