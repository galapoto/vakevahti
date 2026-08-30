import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import SourceScanRun
from app.scanners.base import FundingSourceAdapter
from app.services.persistence import PersistBatchResult, persist_candidates

logger = logging.getLogger(__name__)


class ScanTrigger(StrEnum):
    MANUAL_CLI = "MANUAL_CLI"
    MANUAL_API = "MANUAL_API"
    SCHEDULED = "SCHEDULED"


class ScanRunStatus(StrEnum):
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class IngestionRunResult:
    run_id: UUID
    persistence: PersistBatchResult


async def _create_scan_run(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    run_id: UUID,
    source_code: str,
    trigger: ScanTrigger,
    started_at: datetime,
) -> None:
    async with session_factory() as session:
        async with session.begin():
            session.add(
                SourceScanRun(
                    id=run_id,
                    source_code=source_code,
                    trigger_type=trigger.value,
                    status=ScanRunStatus.RUNNING.value,
                    started_at=started_at,
                )
            )


async def _mark_scan_failed(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    run_id: UUID,
    completed_at: datetime,
    error: Exception,
    discovered_count: int | None,
) -> None:
    async with session_factory() as session:
        async with session.begin():
            run = await session.get(SourceScanRun, run_id, with_for_update=True)
            if run is None:
                raise RuntimeError(f"Source scan run {run_id} disappeared before failure audit.")

            run.status = ScanRunStatus.FAILED.value
            run.completed_at = completed_at
            run.discovered_count = discovered_count
            run.error_type = type(error).__name__[:255]
            run.error_message = str(error)[:2000]


async def run_source_ingestion(
    scanner: FundingSourceAdapter,
    session_factory: async_sessionmaker[AsyncSession],
    *,
    trigger: ScanTrigger,
    observed_at: datetime | None = None,
) -> IngestionRunResult:
    """Run one auditable source ingestion using the shared production path.

    The RUNNING audit row is committed before network I/O. Persistence and the
    SUCCEEDED audit update are committed together. A source/parsing/persistence
    exception records a FAILED run and is re-raised to the caller.
    """

    run_id = uuid4()
    started_at = datetime.now(UTC)
    await _create_scan_run(
        session_factory,
        run_id=run_id,
        source_code=scanner.source_code,
        trigger=trigger,
        started_at=started_at,
    )

    discovered_count: int | None = None

    try:
        candidates = await scanner.scan()
        discovered_count = len(candidates)

        if any(candidate.source_code != scanner.source_code for candidate in candidates):
            raise ValueError(
                "Scanner returned candidates whose source_code does not match the adapter."
            )

        persistence_observed_at = observed_at or datetime.now(UTC)
        async with session_factory() as session:
            async with session.begin():
                persistence = await persist_candidates(
                    session,
                    candidates,
                    observed_at=persistence_observed_at,
                )

                run = await session.get(SourceScanRun, run_id, with_for_update=True)
                if run is None:
                    raise RuntimeError(
                        f"Source scan run {run_id} disappeared before success audit."
                    )

                run.status = ScanRunStatus.SUCCEEDED.value
                run.completed_at = datetime.now(UTC)
                run.baseline = persistence.baseline
                run.discovered_count = discovered_count
                run.new_count = persistence.new_count
                run.unchanged_count = persistence.unchanged_count
                run.changed_count = persistence.changed_count
                run.error_type = None
                run.error_message = None

        return IngestionRunResult(run_id=run_id, persistence=persistence)

    except Exception as exc:
        try:
            await _mark_scan_failed(
                session_factory,
                run_id=run_id,
                completed_at=datetime.now(UTC),
                error=exc,
                discovered_count=discovered_count,
            )
        except Exception:
            logger.exception(
                "Failed to persist failure audit for source run %s after %s",
                run_id,
                type(exc).__name__,
            )
        raise
