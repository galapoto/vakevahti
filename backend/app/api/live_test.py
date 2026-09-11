import asyncio
from collections import Counter
from time import perf_counter
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.dependencies import get_runtime_settings
from app.config import Settings
from app.domain.funding_call import FundingCallCandidate, RelevanceStatus
from app.scanners.registry import (
    UnknownFundingSourceError,
    build_scanners,
    registered_source_codes,
)

router = APIRouter(prefix="/api/test", tags=["live-source-test"])
SettingsDependency = Annotated[Settings, Depends(get_runtime_settings)]

_SOURCE_LABELS = {
    "STM": "Sosiaali- ja terveysministeriö",
    "HAEAVUSTUKSIA": "Haeavustuksia.fi",
    "EURA": "EURA 2021",
    "SITRA": "Sitra",
    "ACADEMY": "Suomen Akatemia",
}
_scan_locks: dict[str, asyncio.Lock] = {}


class LiveSourceOption(BaseModel):
    code: str
    label: str


class LiveSourceCatalog(BaseModel):
    sources: list[LiveSourceOption]


class LiveSourceDistribution(BaseModel):
    relevant: int
    needs_review: int
    not_relevant: int


class LiveSourceScanResponse(BaseModel):
    source_code: str
    source_label: str
    total: int
    duration_ms: int
    distribution: LiveSourceDistribution
    items: list[FundingCallCandidate]


def _source_label(source_code: str) -> str:
    return _SOURCE_LABELS.get(source_code, source_code)


def _scan_lock(source_code: str) -> asyncio.Lock:
    lock = _scan_locks.get(source_code)
    if lock is None:
        lock = asyncio.Lock()
        _scan_locks[source_code] = lock
    return lock


@router.get("/live-sources", response_model=LiveSourceCatalog)
async def live_source_catalog() -> LiveSourceCatalog:
    """List source adapters available to the opt-in live test console."""

    return LiveSourceCatalog(
        sources=[
            LiveSourceOption(code=code, label=_source_label(code))
            for code in registered_source_codes()
        ]
    )


@router.post("/live-sources/{source_code}", response_model=LiveSourceScanResponse)
async def run_live_source_test(
    source_code: str,
    settings: SettingsDependency,
) -> LiveSourceScanResponse:
    """Run one source adapter without persistence so operators can inspect live parsing."""

    normalized = source_code.strip().upper()
    try:
        scanner = build_scanners(settings, [normalized])[0]
    except UnknownFundingSourceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    lock = _scan_lock(normalized)
    if lock.locked():
        raise HTTPException(
            status_code=409,
            detail=f"A live test for {normalized} is already running.",
        )

    started = perf_counter()
    try:
        async with lock:
            candidates = await scanner.scan()
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "source_code": normalized,
                "error_type": type(exc).__name__,
                "message": str(exc)[:1000],
            },
        ) from exc

    counts = Counter(candidate.relevance_status for candidate in candidates)
    return LiveSourceScanResponse(
        source_code=normalized,
        source_label=_source_label(normalized),
        total=len(candidates),
        duration_ms=round((perf_counter() - started) * 1000),
        distribution=LiveSourceDistribution(
            relevant=counts[RelevanceStatus.RELEVANT],
            needs_review=counts[RelevanceStatus.NEEDS_REVIEW],
            not_relevant=counts[RelevanceStatus.NOT_RELEVANT],
        ),
        items=candidates,
    )
