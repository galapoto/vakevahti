from datetime import UTC, date, datetime, timedelta
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
from app.services.reads import OperatorRelevanceFilter, SourceHealthStatus

router = APIRouter(prefix="/api")

SettingsDependency = Annotated[Settings, Depends(get_runtime_settings)]
SourceCodeQuery = Annotated[str | None, Query(min_length=1, max_length=32)]
RelevanceQuery = Annotated[OperatorRelevanceFilter | None, Query()]
LimitQuery = Annotated[int, Query(ge=1, le=100)]
OffsetQuery = Annotated[int, Query(ge=0)]

_SOURCE_URLS = {
    "STM": "https://stm.fi/vuoden-2026-valtionavustushaut",
    "HAEAVUSTUKSIA": "https://www.haeavustuksia.fi/fi/?isAdditionalSearchOpen=true",
    "EURA": "https://eura2021.fi/hakuilmoitukset",
    "SITRA": "https://asiointi.sitra.fi/",
    "ACADEMY": "https://www.aka.fi/tutkimusrahoitus/hae-rahoitusta/haut/",
}
_SOURCE_COUNTS = {
    "STM": (4, 1),
    "HAEAVUSTUKSIA": (5, 2),
    "EURA": (3, 2),
    "SITRA": (2, 1),
    "ACADEMY": (4, 1),
}
_SOURCE_NAMES = {
    "STM": "STM",
    "HAEAVUSTUKSIA": "Haeavustuksia.fi",
    "EURA": "EURA 2021",
    "SITRA": "Sitra",
    "ACADEMY": "Suomen Akatemia",
}
_SOURCE_REASONS = {
    "STM": "Hyvinvointialue kuuluu haun mahdolliseen kohderyhmään ja teema tukee sosiaali- ja terveyspalvelujen kehittämistä.",
    "HAEAVUSTUKSIA": "Hakuilmoituksessa on julkisen toimijan tai hyvinvointialueen hakukelpoisuutta tukevaa näyttöä.",
    "EURA": "Haku kohdistuu Etelä-Suomeen tai valtakunnallisesti ja hakijaryhmä voi soveltua hyvinvointialueelle.",
    "SITRA": "Teema liittyy julkisen sektorin uudistamiseen, yhteistyöhön tai hyvinvointialueen kehittämiseen.",
    "ACADEMY": "Haku voi tukea VakeHyvän tutkimus-, kehittämis- tai kumppanuustavoitteita.",
}
_REVIEW_REASON = (
    "Hakukelpoisuudesta löytyi lupaavia viitteitä, mutta VakeVahti ei pystynyt varmistamaan "
    "soveltuvuutta automaattisesti. Haku tarvitsee henkilön tarkistuksen ennen raportointia."
)
_OBSERVED_AT = datetime(2026, 9, 11, 8, 45, tzinfo=UTC)


def _preview_calls() -> tuple[FundingCallDetail, ...]:
    """Return deterministic synthetic fixtures for database-free employee UI testing."""

    calls: list[FundingCallDetail] = []
    next_id = 9001
    for source_code, (relevant_count, review_count) in _SOURCE_COUNTS.items():
        total = relevant_count + review_count
        for index in range(1, total + 1):
            needs_review = index > relevant_count
            deadline_date = date(2026, 10, 1) + timedelta(days=index * 4)
            calls.append(
                FundingCallDetail(
                    id=next_id,
                    source_code=source_code,
                    title=f"{_SOURCE_NAMES[source_code]} – VakeHyvälle sopiva esimerkkihaku {index}",
                    source_url=_SOURCE_URLS[source_code],
                    application_opens_on=date(2026, 9, 1),
                    application_opens_at=None,
                    application_deadline_on=deadline_date,
                    application_deadline_at=None,
                    relevance_status="NEEDS_REVIEW" if needs_review else "RELEVANT",
                    relevance_reason=_REVIEW_REASON if needs_review else _SOURCE_REASONS[source_code],
                    current_version=1,
                    first_seen_at=_OBSERVED_AT,
                    last_seen_at=_OBSERVED_AT,
                    description_text=(
                        "Kehitysesikatselun fixture-dataa. Tietuetta käytetään vain VakeVahdin "
                        "käyttöliittymän ja raportointityönkulun testaamiseen ilman PostgreSQL-yhteyttä."
                    ),
                    evidence=[{"kind": "preview_fixture", "synthetic": True}],
                )
            )
            next_id += 1
    return tuple(calls)


_PREVIEW_CALLS = _preview_calls()


@router.get("/funding-calls", response_model=FundingCallListResponse, tags=["funding"])
async def funding_calls(
    source_code: SourceCodeQuery = None,
    relevance_status: RelevanceQuery = None,
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
) -> FundingCallListResponse:
    normalized_source = source_code.strip().upper() if source_code else None
    normalized_relevance = relevance_status.value if relevance_status else None
    records = [
        call
        for call in _PREVIEW_CALLS
        if (normalized_source is None or call.source_code == normalized_source)
        and (normalized_relevance is None or call.relevance_status == normalized_relevance)
    ]
    records.sort(
        key=lambda call: (
            call.application_deadline_on or date.max,
            call.application_deadline_at or datetime.max.replace(tzinfo=UTC),
            call.id,
        )
    )
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


@router.get("/sources/health", response_model=SourceHealthResponse, tags=["health"])
async def source_health(settings: SettingsDependency) -> SourceHealthResponse:
    sources: list[SourceHealthItem] = []
    for index, source_code in enumerate(settings.enabled_source_codes, start=1):
        relevant_count, review_count = _SOURCE_COUNTS.get(source_code, (0, 0))
        total = relevant_count + review_count
        sources.append(
            SourceHealthItem(
                source_code=source_code,
                health=SourceHealthStatus.HEALTHY,
                current_call_count=total,
                relevant_call_count=relevant_count,
                review_call_count=review_count,
                baseline_completed_at=_OBSERVED_AT,
                last_successful_scan_at=_OBSERVED_AT,
                latest_scan_id=UUID(f"00000000-0000-0000-0000-{index:012d}"),
                latest_scan_status="SUCCEEDED",
                latest_scan_trigger="PREVIEW_FIXTURE",
                latest_scan_started_at=_OBSERVED_AT,
                latest_scan_completed_at=_OBSERVED_AT,
                latest_scan_baseline=False,
                latest_discovered_count=total,
                latest_new_count=0,
                latest_unchanged_count=total,
                latest_changed_count=0,
                latest_error_type=None,
            )
        )
    return SourceHealthResponse(sources=sources)
