import argparse
import asyncio
import logging

from app.config import Settings, get_settings
from app.db.session import create_engine, create_session_factory
from app.scanners.base import FundingSourceAdapter
from app.scanners.registry import build_scanners
from app.services.ingestion import IngestionRunResult, ScanTrigger, run_source_ingestion

logger = logging.getLogger(__name__)


def _log_result(result: IngestionRunResult) -> None:
    persistence = result.persistence
    logger.info(
        "source_run_succeeded run_id=%s source=%s baseline=%s new=%s unchanged=%s changed=%s",
        result.run_id,
        persistence.source_code,
        persistence.baseline,
        persistence.new_count,
        persistence.unchanged_count,
        persistence.changed_count,
    )


async def _run_scanner(
    scanner: FundingSourceAdapter,
    session_factory: object,
) -> IngestionRunResult:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    if not isinstance(session_factory, async_sessionmaker):
        raise TypeError("session_factory must be an async_sessionmaker")

    typed_factory: async_sessionmaker[AsyncSession] = session_factory
    return await run_source_ingestion(
        scanner,
        typed_factory,
        trigger=ScanTrigger.SCHEDULED,
    )


async def run_once(settings: Settings) -> None:
    """Run all configured funding sources once and exit.

    Every configured source is attempted. If one or more fail, successful sources
    still retain their own committed audit/persistence outcome and the process exits
    with an ExceptionGroup so an external scheduler can mark the run unhealthy.
    """

    engine = create_engine(settings)
    session_factory = create_session_factory(engine)
    scanners = build_scanners(settings)
    failures: list[Exception] = []

    try:
        for scanner in scanners:
            try:
                result = await run_source_ingestion(
                    scanner,
                    session_factory,
                    trigger=ScanTrigger.SCHEDULED,
                )
                _log_result(result)
            except Exception as exc:
                logger.exception("Scheduled ingestion failed for source=%s", scanner.source_code)
                failures.append(exc)
    finally:
        await engine.dispose()

    if failures:
        raise ExceptionGroup("One or more funding source ingestions failed.", failures)


async def run_loop(settings: Settings) -> None:
    """Run the v1 single-replica interval worker for all configured sources.

    Production platforms may instead invoke one-shot ingestion through cron, a
    managed scheduler, Kubernetes CronJob, or the future Vaketomate scheduler.
    """

    engine = create_engine(settings)
    session_factory = create_session_factory(engine)
    scanners = build_scanners(settings)
    interval_seconds = settings.scan_interval_minutes * 60

    try:
        if not settings.scan_run_on_startup:
            await asyncio.sleep(interval_seconds)

        while True:
            for scanner in scanners:
                try:
                    result = await run_source_ingestion(
                        scanner,
                        session_factory,
                        trigger=ScanTrigger.SCHEDULED,
                    )
                    _log_result(result)
                except Exception:
                    logger.exception(
                        "Scheduled ingestion failed for source=%s; next interval will retry.",
                        scanner.source_code,
                    )

            await asyncio.sleep(interval_seconds)
    finally:
        await engine.dispose()


async def _async_main(mode: str) -> None:
    settings = get_settings()
    if mode == "once":
        await run_once(settings)
    else:
        await run_loop(settings)


def main() -> None:
    parser = argparse.ArgumentParser(description="VakeVahti source-ingestion worker")
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["once", "loop"],
        default="loop",
        help="once = ingest configured sources once; loop = repeat at SCAN_INTERVAL_MINUTES",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    try:
        asyncio.run(_async_main(args.mode))
    except KeyboardInterrupt:
        logger.info("Worker stopped by operator.")


if __name__ == "__main__":
    main()
