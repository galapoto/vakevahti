from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session, get_runtime_settings
from app.api.schemas import (
    FundingCallDetail,
    FundingCallListItem,
    FundingCallListResponse,
    SourceHealthItem,
    SourceHealthResponse,
)
from app.config import Settings
from app.services.reads import get_funding_call, list_funding_calls, list_source_health

router = APIRouter(prefix="/api")


@router.get(
    "/funding-calls",
    response_model=FundingCallListResponse,
    tags=["funding"],
)
async def funding_calls(
    source_code: str | None = Query(default=None, min_length=1, max_length=32),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
) -> FundingCallListResponse:
    """Read current persisted funding opportunities without touching live source sites."""

    page = await list_funding_calls(
        session,
        source_code=source_code,
        limit=limit,
        offset=offset,
    )
    return FundingCallListResponse(
        total=page.total,
        limit=page.limit,
        offset=page.offset,
        items=[FundingCallListItem.model_validate(record) for record in page.records],
    )


@router.get(
    "/funding-calls/{funding_call_id}",
    response_model=FundingCallDetail,
    tags=["funding"],
)
async def funding_call_detail(
    funding_call_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> FundingCallDetail:
    """Read one current persisted funding opportunity."""

    if funding_call_id <= 0:
        raise HTTPException(status_code=404, detail="Funding call not found.")

    record = await get_funding_call(session, funding_call_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Funding call not found.")
    return FundingCallDetail.model_validate(record)


@router.get(
    "/sources/health",
    response_model=SourceHealthResponse,
    tags=["health"],
)
async def source_health(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_runtime_settings),
) -> SourceHealthResponse:
    """Expose configured-source operational state from persisted audit facts."""

    snapshots = await list_source_health(
        session,
        source_codes=settings.enabled_source_codes,
    )
    return SourceHealthResponse(
        sources=[
            SourceHealthItem(
                source_code=snapshot.source_code,
                health=snapshot.health,
                current_call_count=snapshot.current_call_count,
                baseline_completed_at=snapshot.baseline_completed_at,
                last_successful_scan_at=snapshot.last_successful_scan_at,
                latest_scan_id=snapshot.latest_scan_id,
                latest_scan_status=snapshot.latest_scan_status,
                latest_scan_trigger=snapshot.latest_scan_trigger,
                latest_scan_started_at=snapshot.latest_scan_started_at,
                latest_scan_completed_at=snapshot.latest_scan_completed_at,
                latest_scan_baseline=snapshot.latest_scan_baseline,
                latest_discovered_count=snapshot.latest_discovered_count,
                latest_new_count=snapshot.latest_new_count,
                latest_unchanged_count=snapshot.latest_unchanged_count,
                latest_changed_count=snapshot.latest_changed_count,
                latest_error_type=snapshot.latest_error_type,
            )
            for snapshot in snapshots
        ]
    )
