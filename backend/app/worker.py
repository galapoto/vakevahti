import argparse
import asyncio
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import Settings, get_settings
from app.db.session import create_engine, create_session_factory
from app.scanners.base import FundingSourceAdapter
from app.scanners.registry import build_scanners
from app.services.funding_reports import create_automated_funding_report
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


async def _ingest_scanner(
    scanner: FundingSourceAdapter,
    session_factory: async_sessionmaker[AsyncSession],
) -> IngestionRunResult:
    return await run_source_ingestion(
        scanner,
        session_factory,
        trigger=ScanTrigger.SCHEDULED,
    )


async def _compose_cycle_report(
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    run_ids: tuple[UUID, ...],
) -> None:
    if not settings.automatic_report_enabled or not run_ids:
        return

    async with session_factory() as session:
        report = await create_automated_funding_report(
            session,
            scan_run_ids=run_ids,
            recipient_emails=settings.report_recipient_emails,
        )
    if report is None:
        logger.info("automatic_report_skipped reason=no_material_findings")
        return

    logger.info(
        "automatic_report_ready report_id=%s findings=%s recipients=%s subject=%r",
        report.id,
        len(report.items),
        len(report.recipient_emails),
        report.email_subject,
    )


async def run_once(settings: Settings) -> None:
    """Run all configured funding sources and automatically compose the cycle report."""

    engine = create_engine(settings)
    session_factory = create_session_factory(engine)
    scanners = build_scanners(settings)
    failures: list[Exception] = []
    successful_run_ids: list[UUID] = []

    try:
        for scanner in scanners:
            try:
                result = await _ingest_scanner(scanner, session_factory)
                successful_run_ids.append(result.run_id)
                _log_result(result)
            except Exception as exc:
                logger.exception("Scheduled ingestion failed for source=%s", scanner.source_code)
                failures.append(exc)

        try:
            await _compose_cycle_report(
                settings,
                session_factory,
                tuple(successful_run_ids),
            )
        except Exception as exc:
            logger.exception("Automatic funding report composition failed.")
            failures.append(exc)
    finally:
        await engine.dispose()

    if failures:
        raise ExceptionGroup("One or more automated funding tasks failed.", failures)


async def run_loop(settings: Settings) -> None:
    """Run unattended scan cycles and compose a report after each material cycle."""

    engine = create_engine(settings)
    session_factory = create_session_factory(engine)
    scanners = build_scanners(settings)
    interval_seconds = settings.scan_interval_minutes * 60

    try:
        if not settings.scan_run_on_startup:
            await asyncio.sleep(interval_seconds)

        while True:
            successful_run_ids: list[UUID] = []
            for scanner in scanners:
                try:
                    result = await _ingest_scanner(scanner, session_factory)
                    successful_run_ids.append(result.run_id)
                    _log_result(result)
                except Exception:
                    logger.exception(
                        "Scheduled ingestion failed for source=%s; next interval will retry.",
                        scanner.source_code,
                    )

            try:
                await _compose_cycle_report(
                    settings,
                    session_factory,
                    tuple(successful_run_ids),
                )
            except Exception:
                logger.exception(
                    "Automatic report composition failed; next interval will retry scanning."
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
        help="once = run one automated cycle; loop = repeat at SCAN_INTERVAL_MINUTES",
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
