import json
from datetime import UTC, datetime
from hashlib import sha256
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.api.preview_routes import _PREVIEW_CALLS
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
from app.api.schemas import FundingCallDetail

router = APIRouter(prefix="/api/reports", tags=["reports"])
ReportStatusQuery = Annotated[FundingReportStatus | None, Query(alias="status")]
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


def _approval_snapshot(report: FundingReportResponse) -> dict[str, object]:
    return {
        "report_id": str(report.id),
        "case_id": str(report.case_id) if report.case_id else None,
        "included_artifact_ids": [str(value) for value in report.included_artifact_ids],
        "title": report.title,
        "origin": report.origin.value,
        "automation_key": report.automation_key,
        "notes": report.notes,
        "email_subject": report.email_subject,
        "email_body": report.email_body,
        "recipient_emails": list(report.recipient_emails),
        "items": [item.model_dump(mode="json") for item in report.items],
    }


def _approval_hash(snapshot: dict[str, object]) -> str:
    canonical = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode("utf-8")).hexdigest()


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
        case_id=None,
        included_artifact_ids=[],
        title=draft.title.strip(),
        status=FundingReportStatus.DRAFT,
        origin=FundingReportOrigin.MANUAL,
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


@router.get("", response_model=FundingReportListResponse)
async def report_queue(
    status_filter: ReportStatusQuery = None,
    limit: int = 25,
    offset: int = 0,
) -> FundingReportListResponse:
    if limit < 1 or limit > 50 or offset < 0:
        raise HTTPException(status_code=422, detail="Invalid report queue pagination.")
    items = list(_REPORTS.values())
    if status_filter is not None:
        items = [item for item in items if item.status is status_filter]
    items.sort(key=lambda item: (item.updated_at, str(item.id)), reverse=True)
    return FundingReportListResponse(
        total=len(items),
        limit=limit,
        offset=offset,
        items=items[offset : offset + limit],
    )


@router.get("/latest", response_model=FundingReportResponse | None)
async def latest_report(response: Response) -> FundingReportResponse | None:
    if not _REPORTS:
        response.status_code = status.HTTP_204_NO_CONTENT
        return None
    return max(_REPORTS.values(), key=lambda report: report.created_at)


@router.get("/{report_id}", response_model=FundingReportResponse)
async def report_detail(report_id: UUID) -> FundingReportResponse:
    report = _REPORTS.get(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Funding report not found.")
    return report


@router.patch("/{report_id}", response_model=FundingReportResponse)
async def edit_report(
    report_id: UUID,
    update: FundingReportUpdate,
) -> FundingReportResponse:
    report = _REPORTS.get(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Funding report not found.")

    if report.status is FundingReportStatus.APPROVED:
        raise HTTPException(
            status_code=409,
            detail="Approved reports are immutable; create a new report version to make changes.",
        )

    changes = update.model_dump(exclude_unset=True)
    if "title" in changes and changes["title"] is not None:
        changes["title"] = str(changes["title"]).strip()
    for field in ("notes", "email_subject", "email_body"):
        if field in changes:
            value = changes[field]
            changes[field] = str(value).strip() if value else None
    if changes:
        changes["updated_at"] = datetime.now(UTC)
        if report.status in {
            FundingReportStatus.WAITING_APPROVAL,
            FundingReportStatus.REJECTED,
        }:
            changes["status"] = FundingReportStatus.DRAFT
            changes["submitted_for_approval_at"] = None

    edited = report.model_copy(update=changes)
    _REPORTS[report_id] = edited
    return edited


@router.post("/{report_id}/submit", response_model=FundingReportResponse)
async def submit_report(report_id: UUID) -> FundingReportResponse:
    report = _REPORTS.get(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Funding report not found.")
    if report.status is FundingReportStatus.WAITING_APPROVAL:
        return report
    if report.status is not FundingReportStatus.DRAFT:
        raise HTTPException(
            status_code=409,
            detail=f"Report in status {report.status.value} cannot be submitted for approval.",
        )

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


@router.post("/{report_id}/revise", response_model=FundingReportResponse)
async def revise_report(report_id: UUID) -> FundingReportResponse:
    report = _REPORTS.get(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Funding report not found.")
    if report.status is not FundingReportStatus.APPROVED:
        raise HTTPException(
            status_code=409,
            detail="Only an approved report can be revised into a successor version.",
        )

    existing = next(
        (
            candidate
            for candidate in _REPORTS.values()
            if candidate.supersedes_report_id == report.id
        ),
        None,
    )
    if existing is not None:
        return existing

    now = datetime.now(UTC)
    successor = report.model_copy(
        update={
            "id": uuid4(),
            "status": FundingReportStatus.DRAFT,
            "origin": FundingReportOrigin.MANUAL,
            "automation_key": None,
            "version_number": report.version_number + 1,
            "supersedes_report_id": report.id,
            "created_at": now,
            "updated_at": now,
            "submitted_for_approval_at": None,
            "approval_events": [],
        }
    )
    _REPORTS[successor.id] = successor
    return successor


@router.post("/{report_id}/decision", response_model=FundingReportResponse)
async def decide_report(
    report_id: UUID,
    decision: FundingReportDecisionRequest,
) -> FundingReportResponse:
    report = _REPORTS.get(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Funding report not found.")

    snapshot = _approval_snapshot(report)
    content_hash = _approval_hash(snapshot)
    latest = report.approval_events[-1] if report.approval_events else None
    if report.status is not FundingReportStatus.WAITING_APPROVAL:
        if (
            latest is not None
            and latest.decision is decision.decision
            and latest.content_hash == content_hash
        ):
            return report
        raise HTTPException(
            status_code=409,
            detail=f"Report in status {report.status.value} is not waiting for approval.",
        )

    now = datetime.now(UTC)
    event = FundingReportApprovalEventResponse(
        id=uuid4(),
        report_id=report.id,
        decision=decision.decision,
        actor_id=decision.actor_id,
        actor_display_name=decision.actor_display_name,
        actor_source="PREVIEW_FIXTURE",
        comment=decision.comment,
        decided_at=now,
        content_hash=content_hash,
        snapshot=snapshot,
    )
    if decision.decision is FundingReportApprovalDecision.APPROVE:
        next_status = FundingReportStatus.APPROVED
        submitted_at = report.submitted_for_approval_at
    elif decision.decision is FundingReportApprovalDecision.RETURN_FOR_EDIT:
        next_status = FundingReportStatus.DRAFT
        submitted_at = None
    else:
        next_status = FundingReportStatus.REJECTED
        submitted_at = report.submitted_for_approval_at

    decided = report.model_copy(
        update={
            "status": next_status,
            "updated_at": now,
            "submitted_for_approval_at": submitted_at,
            "approval_events": [*report.approval_events, event],
        }
    )
    _REPORTS[report_id] = decided
    return decided
