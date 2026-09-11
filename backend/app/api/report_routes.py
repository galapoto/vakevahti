from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.api.report_schemas import FundingReportDraftCreate, FundingReportResponse
from app.services.funding_reports import (
    FundingReportCallsNotFoundError,
    FundingReportNotFoundError,
    create_funding_report,
    get_funding_report,
    submit_funding_report_for_approval,
)

router = APIRouter(prefix="/api/reports", tags=["reports"])
SessionDependency = Annotated[AsyncSession, Depends(get_db_session)]


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


@router.get("/{report_id}", response_model=FundingReportResponse)
async def report_detail(
    report_id: UUID,
    session: SessionDependency,
) -> FundingReportResponse:
    try:
        return await get_funding_report(session, report_id)
    except FundingReportNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Funding report not found.") from exc


@router.post("/{report_id}/submit", response_model=FundingReportResponse)
async def submit_report(
    report_id: UUID,
    session: SessionDependency,
) -> FundingReportResponse:
    try:
        return await submit_funding_report_for_approval(session, report_id)
    except FundingReportNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Funding report not found.") from exc
