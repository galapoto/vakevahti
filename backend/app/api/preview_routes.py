from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_runtime_settings
from app.api.schemas import (
    FundingCallDetail,
    FundingCallListItem,
    FundingCallListResponse,
    SourceHealthItem,
    SourceHealthResponse,
)
from app.config import Settings
from app.services.reads import SourceHealthStatus

router = APIRouter(prefix="/api")

SettingsDependency = Annotated[Settings, Depends(get_runtime_settings)]
SourceCodeQuery = Annotated[str | None, Query(min_length=1, max_length=32)]
LimitQuery = Annotated[int, Query(ge=1, le=100)]
OffsetQuery = Annotated[int, Query(ge=0)]

_SOURCE_URLS = {
    "STM": "https://stm.fi/vuoden-2026-valtionavustushaut",
    "SITRA": "https://asiointi.sitra.fi/",
    "ACADEMY": "https://www.aka.fi/tutkimusrahoitus/hae-rahoitusta/haut/",
}
_SOURCE_COUNTS = {"STM": 9, "SITRA": 1, "ACADEMY": 7}
_OBSERVED_AT = datetime(2026, 8, 30, 16, 51, tzinfo=timezone.utc)


def _preview_calls() -> tuple[FundingCallDetail, ...]:
    """Return clearly synthetic public-data fixtures for database-free UI development."""

    calls: list[FundingCallDetail] = []
    next_id = 9001
    for source_code, count in _SOURCE_COUNTS.items():
        for index in range(1, count + 1):
            deadline = _OBSERVED_AT + timedelta(days=14 + index * 3)
            calls.append(
                FundingCallDetail(
                    id=next_id,
                    source_code=source_code,
                    title=f"{source_code} – esimerkkihaku {index}",
                    source_url=_SOURCE_URLS[source_code],
                    application_opens_at=None,
                    application_deadline_at=deadline,
                    relevance_status="RELEVANT",
                    current_version=1,
                    first_seen_at=_OBSERVED_AT,
                    last_seen_at=_OBSERVED_AT,
                    description_text=(
                        "Kehitysesikatselun fixture-dataa. Tätä tietuetta käytetään vain "
                        "käyttöliittymän testaamiseen ilman PostgreSQL-tietokantaa."
                    ),
                    relevance_reason="Preview fixture; ei tuotantodataa.",
                    evidence=[{"kind": "preview_fixture", "synthetic": True}],
                )
            )
            next_id += 1
    return tuple(calls)


_PREVIEW_CALLS = _preview_calls()


@router.get(
    "/funding-calls",
    response_model=FundingCallListResponse,
    tags=["funding"],
)
async def funding_calls(
    source_code: SourceCodeQuery = None,
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
) -> FundingCallListResponse:
    normalized_source = source_code.strip().upper() if source_code else None
    records = [
        call
        for call in _PREVIEW_CALLS
        if normalized_source is None or call.source_code == normalized_source
    ]
    records.sort(key=lambda call: (call.application_deadline_at or datetime.max.replace(tzinfo=timezone.utc), call.id))
    page = records[offset : offset + limit]
    return FundingCallListResponse(
        total=len(records),
        limit=limit,
        offset=offset,
        items=[FundingCallListItem.model_validate(call) for call in page],
    )


@router.get(
    "/funding-calls/{funding_call_id}",
    response_model=FundingCallDetail,
    tags=["funding"],
)
async def funding_call_detail(funding_call_id: int) -> FundingCallDetail:
    for call in _PREVIEW_CALLS:
        if call.id == funding_call_id:
            return call
    raise HTTPException(status_code=404, detail="Funding call not found.")


@router.get(
    "/sources/health",
    response_model=SourceHealthResponse,
    tags=["health"],
)
async def source_health(settings: SettingsDependency) -> SourceHealthResponse:
    sources: list[SourceHealthItem] = []
    for index, source_code in enumerate(settings.enabled_source_codes, start=1):
        sources.append(
            SourceHealthItem(
                source_code=source_code,
                health=SourceHealthStatus.HEALTHY,
                current_call_count=_SOURCE_COUNTS.get(source_code, 0),
                baseline_completed_at=_OBSERVED_AT,
                last_successful_scan_at=_OBSERVED_AT,
                latest_scan_id=UUID(f"00000000-0000-0000-0000-{index:012d}"),
                latest_scan_status="SUCCEEDED",
                latest_scan_trigger="PREVIEW_FIXTURE",
                latest_scan_started_at=_OBSERVED_AT,
                latest_scan_completed_at=_OBSERVED_AT,
                latest_scan_baseline=False,
                latest_discovered_count=_SOURCE_COUNTS.get(source_code, 0),
                latest_new_count=0,
                latest_unchanged_count=_SOURCE_COUNTS.get(source_code, 0),
                latest_changed_count=0,
                latest_error_type=None,
            )
        )
    return SourceHealthResponse(sources=sources)
