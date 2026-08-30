from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import FundingCallRecord, SourceScanRun, SourceState
from app.services.ingestion import ScanRunStatus


@dataclass(frozen=True)
class FundingCallPage:
    """One bounded page of current persisted funding calls."""

    records: tuple[FundingCallRecord, ...]
    total: int
    limit: int
    offset: int


class SourceHealthStatus(StrEnum):
    """Operational health derived only from facts already stored by ingestion."""

    NEVER_SCANNED = "NEVER_SCANNED"
    RUNNING = "RUNNING"
    HEALTHY = "HEALTHY"
    FAILING = "FAILING"


@dataclass(frozen=True)
class SourceHealthSnapshot:
    source_code: str
    health: SourceHealthStatus
    current_call_count: int
    baseline_completed_at: datetime | None
    last_successful_scan_at: datetime | None
    latest_scan_id: UUID | None
    latest_scan_status: str | None
    latest_scan_trigger: str | None
    latest_scan_started_at: datetime | None
    latest_scan_completed_at: datetime | None
    latest_scan_baseline: bool | None
    latest_discovered_count: int | None
    latest_new_count: int | None
    latest_unchanged_count: int | None
    latest_changed_count: int | None
    latest_error_type: str | None


async def list_funding_calls(
    session: AsyncSession,
    *,
    source_code: str | None,
    limit: int,
    offset: int,
) -> FundingCallPage:
    """Return a stable bounded page from the current-state funding table."""

    filters = []
    normalized_source = source_code.strip().upper() if source_code else None
    if normalized_source:
        filters.append(FundingCallRecord.source_code == normalized_source)

    count_statement = select(func.count()).select_from(FundingCallRecord).where(*filters)
    total = int((await session.scalar(count_statement)) or 0)

    statement = (
        select(FundingCallRecord)
        .where(*filters)
        .order_by(
            FundingCallRecord.application_deadline_at.asc().nulls_last(),
            FundingCallRecord.id.asc(),
        )
        .limit(limit)
        .offset(offset)
    )
    records = tuple((await session.scalars(statement)).all())

    return FundingCallPage(records=records, total=total, limit=limit, offset=offset)


async def get_funding_call(
    session: AsyncSession,
    funding_call_id: int,
) -> FundingCallRecord | None:
    """Read one current funding call by internal API identifier."""

    return await session.get(FundingCallRecord, funding_call_id)


def _health_from_latest_run(latest_run: SourceScanRun | None) -> SourceHealthStatus:
    if latest_run is None:
        return SourceHealthStatus.NEVER_SCANNED

    try:
        status = ScanRunStatus(latest_run.status)
    except ValueError as exc:
        raise RuntimeError(
            f"Unknown persisted scan status for {latest_run.source_code}: {latest_run.status}"
        ) from exc

    if status is ScanRunStatus.RUNNING:
        return SourceHealthStatus.RUNNING
    if status is ScanRunStatus.SUCCEEDED:
        return SourceHealthStatus.HEALTHY
    return SourceHealthStatus.FAILING


async def list_source_health(
    session: AsyncSession,
    *,
    source_codes: tuple[str, ...],
) -> tuple[SourceHealthSnapshot, ...]:
    """Read source operational state without inventing a freshness threshold.

    The configured source list defines which adapters are expected to operate in this
    process. PostgreSQL remains the source of truth for their latest persisted state.
    """

    normalized_codes = tuple(dict.fromkeys(code.strip().upper() for code in source_codes))
    if not normalized_codes:
        return ()

    states = {
        state.source_code: state
        for state in (
            await session.scalars(
                select(SourceState).where(SourceState.source_code.in_(normalized_codes))
            )
        ).all()
    }

    latest_runs = {
        run.source_code: run
        for run in (
            await session.scalars(
                select(SourceScanRun)
                .where(SourceScanRun.source_code.in_(normalized_codes))
                .distinct(SourceScanRun.source_code)
                .order_by(SourceScanRun.source_code, SourceScanRun.started_at.desc())
            )
        ).all()
    }

    count_rows = await session.execute(
        select(FundingCallRecord.source_code, func.count(FundingCallRecord.id))
        .where(FundingCallRecord.source_code.in_(normalized_codes))
        .group_by(FundingCallRecord.source_code)
    )
    call_counts = {source_code: int(count) for source_code, count in count_rows.all()}

    snapshots: list[SourceHealthSnapshot] = []
    for source_code in normalized_codes:
        state = states.get(source_code)
        latest = latest_runs.get(source_code)
        snapshots.append(
            SourceHealthSnapshot(
                source_code=source_code,
                health=_health_from_latest_run(latest),
                current_call_count=call_counts.get(source_code, 0),
                baseline_completed_at=state.baseline_completed_at if state else None,
                last_successful_scan_at=state.last_successful_scan_at if state else None,
                latest_scan_id=latest.id if latest else None,
                latest_scan_status=latest.status if latest else None,
                latest_scan_trigger=latest.trigger_type if latest else None,
                latest_scan_started_at=latest.started_at if latest else None,
                latest_scan_completed_at=latest.completed_at if latest else None,
                latest_scan_baseline=latest.baseline if latest else None,
                latest_discovered_count=latest.discovered_count if latest else None,
                latest_new_count=latest.new_count if latest else None,
                latest_unchanged_count=latest.unchanged_count if latest else None,
                latest_changed_count=latest.changed_count if latest else None,
                latest_error_type=latest.error_type if latest else None,
            )
        )

    return tuple(snapshots)
