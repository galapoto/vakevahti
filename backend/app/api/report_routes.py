from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.api.report_schemas import (
    FundingReportDecisionRequest,
    FundingReportDraftCreate,
    FundingReportListResponse,
    FundingReportResponse,
    FundingReportStatus,
    FundingReportUpdate,
)
from app.services.funding_reports import (
    FundingReportCallsNotFoundError,
    FundingReportNotFoundError,
    FundingReportStateConflictError,
    create_funding_report,
    decide_funding_report,
    get_funding_report,
    get_latest_funding_report,
    list_funding_reports,
    revise_approved_funding_report,
    submit_funding_report_for_approval,
    update_funding_report,
)

router = APIRouter(prefix="/api/reports", tags=["reports"])
SessionDependency = Annotated[AsyncSession, Depends(get_db_session)]
ReportStatusQuery = Annotated[FundingReportStatus | None, Query(alias="status")]


@router.post(
    "",
    response_model=FundingReportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_report(
    draft: FundingReportDraftCreate,
    session: SessionDependency,
) -> FundingReportResponse:
    try:
        return await create_funding_report(session, draft)
    except FundingReportCallsNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"missing_funding_call_ids": exc.missing_ids},
        ) from exc


@router.get("", response_model=FundingReportListResponse)
async def report_queue(
    session: SessionDependency,
    status_filter: ReportStatusQuery = None,
    limit: int = 25,
    offset: int = 0,
) -> FundingReportListResponse:
    try:
        return await list_funding_reports(
            session,
            status=status_filter,
            limit=limit,
            offset=offset,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/latest", response_model=FundingReportResponse | None)
async def latest_report(
    session: SessionDependency,
    response: Response,
) -> FundingReportResponse | None:
    report = await get_latest_funding_report(session)
    if report is None:
        response.status_code = status.HTTP_204_NO_CONTENT
    return report


@router.get("/{report_id}", response_model=FundingReportResponse)
async def report_detail(
    report_id: UUID,
    session: SessionDependency,
) -> FundingReportResponse:
    try:
        return await get_funding_report(session, report_id)
    except FundingReportNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Funding report not found.") from exc


@router.patch("/{report_id}", response_model=FundingReportResponse)
async def edit_report(
    report_id: UUID,
    update: FundingReportUpdate,
    session: SessionDependency,
) -> FundingReportResponse:
    try:
        return await update_funding_report(session, report_id, update)
    except FundingReportNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Funding report not found.") from exc
    except FundingReportStateConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{report_id}/submit", response_model=FundingReportResponse)
async def submit_report(
    report_id: UUID,
    session: SessionDependency,
) -> FundingReportResponse:
    try:
        return await submit_funding_report_for_approval(session, report_id)
    except FundingReportNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Funding report not found.") from exc
    except FundingReportStateConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{report_id}/revise", response_model=FundingReportResponse)
async def revise_report(
    report_id: UUID,
    session: SessionDependency,
) -> FundingReportResponse:
    """Create or return the immutable successor draft for an approved report."""

    try:
        return await revise_approved_funding_report(session, report_id)
    except FundingReportNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Funding report not found.") from exc
    except FundingReportStateConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{report_id}/decision", response_model=FundingReportResponse)
async def decide_report(
    report_id: UUID,
    decision: FundingReportDecisionRequest,
    session: SessionDependency,
) -> FundingReportResponse:
    """Record a staging actor assertion and immutable coordinator decision event."""

    try:
        return await decide_funding_report(session, report_id, decision)
    except FundingReportNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Funding report not found.") from exc
    except FundingReportStateConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
