import argparse
import asyncio
import logging

from app.config import Settings, get_settings
from app.db.session import create_engine, create_session_factory
from app.scanners.stm import STMScanner
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


async def run_once(settings: Settings) -> None:
    """Run one scheduled-style STM ingestion and exit."""

    engine = create_engine(settings)
    session_factory = create_session_factory(engine)
    scanner = STMScanner(settings)

    try:
        result = await run_source_ingestion(
            scanner,
            session_factory,
            trigger=ScanTrigger.SCHEDULED,
        )
        _log_result(result)
    finally:
        await engine.dispose()


async def run_loop(settings: Settings) -> None:
    """Run the v1 single-replica interval worker.

    Production platforms may instead invoke the same one-shot ingestion through
    cron, a managed scheduler, Kubernetes CronJob, or the future Vaketomate scheduler.
    """

    engine = create_engine(settings)
    session_factory = create_session_factory(engine)
    scanner = STMScanner(settings)
    interval_seconds = settings.scan_interval_minutes * 60

    try:
        if not settings.scan_run_on_startup:
            await asyncio.sleep(interval_seconds)

        while True:
            try:
                result = await run_source_ingestion(
                    scanner,
                    session_factory,
                    trigger=ScanTrigger.SCHEDULED,
                )
                _log_result(result)
            except Exception:
                logger.exception("Scheduled STM ingestion failed; next interval will retry.")

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
        help="once = run one ingestion and exit; loop = repeat at SCAN_INTERVAL_MINUTES",
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
