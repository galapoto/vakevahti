import argparse
import asyncio
import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.report_schemas import FundingReportResponse
from app.config import Settings, get_settings
from app.db.session import create_engine, create_session_factory
from app.scanners.base import FundingSourceAdapter
from app.scanners.registry import build_scanners
from app.services.funding_reports import create_automated_funding_report
from app.services.ingestion import IngestionRunResult, ScanTrigger, run_source_ingestion
from app.services.report_email_delivery import (
    claim_report_emails,
    enqueue_report_email,
    mark_report_email_failed,
    mark_report_email_sent,
    retry_delay_minutes,
)
from app.services.smtp_report_sender import send_report_email

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
) -> FundingReportResponse | None:
    if not settings.automatic_report_enabled or not run_ids:
        return None

    async with session_factory() as session:
        report = await create_automated_funding_report(
            session,
            scan_run_ids=run_ids,
            recipient_emails=settings.report_recipient_emails,
        )
    if report is None:
        logger.info("automatic_report_skipped reason=no_material_findings")
        return None

    logger.info(
        "automatic_report_ready report_id=%s findings=%s recipients=%s subject=%r",
        report.id,
        len(report.items),
        len(report.recipient_emails),
        report.email_subject,
    )
    return report


async def _enqueue_automatic_report_email(
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    report: FundingReportResponse | None,
) -> None:
    if report is None or not settings.report_email_auto_send:
        return

    async with session_factory() as session:
        async with session.begin():
            delivery = await enqueue_report_email(session, report)
    if delivery is None:
        logger.info(
            "automatic_report_email_skipped report_id=%s reason=missing_recipient_or_content",
            report.id,
        )
        return

    logger.info(
        "automatic_report_email_queued report_id=%s delivery_id=%s recipients=%s",
        report.id,
        delivery.id,
        len(delivery.recipient_emails),
    )


async def _deliver_pending_report_emails(
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if not settings.report_email_auto_send or not settings.smtp_delivery_configured:
        return

    async with session_factory() as session:
        async with session.begin():
            claims = await claim_report_emails(session, limit=20)

    for claim in claims:
        try:
            await send_report_email(settings, claim)
        except Exception as exc:
            delay_minutes = retry_delay_minutes(
                claim.attempt_count,
                base_minutes=settings.report_email_retry_base_minutes,
                max_minutes=settings.report_email_retry_max_minutes,
            )
            next_attempt_at = datetime.now(UTC) + timedelta(minutes=delay_minutes)
            async with session_factory() as session:
                async with session.begin():
                    await mark_report_email_failed(
                        session,
                        delivery_id=claim.id,
                        claim_token=claim.claim_token,
                        error=type(exc).__name__,
                        next_attempt_at=next_attempt_at,
                    )
            logger.exception(
                "automatic_report_email_failed delivery_id=%s report_id=%s retry_minutes=%s",
                claim.id,
                claim.report_id,
                delay_minutes,
            )
            continue

        async with session_factory() as session:
            async with session.begin():
                await mark_report_email_sent(
                    session,
                    delivery_id=claim.id,
                    claim_token=claim.claim_token,
                )
        logger.info(
            "automatic_report_email_sent delivery_id=%s report_id=%s recipients=%s",
            claim.id,
            claim.report_id,
            len(claim.recipient_emails),
        )


async def _run_post_scan_automation(
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    run_ids: tuple[UUID, ...],
) -> None:
    report = await _compose_cycle_report(settings, session_factory, run_ids)
    await _enqueue_automatic_report_email(settings, session_factory, report)
    await _deliver_pending_report_emails(settings, session_factory)


async def run_once(settings: Settings) -> None:
    """Run all sources, compose any material report and process report email delivery."""

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
            await _run_post_scan_automation(
                settings,
                session_factory,
                tuple(successful_run_ids),
            )
        except Exception as exc:
            logger.exception("Automatic report or email processing failed.")
            failures.append(exc)
    finally:
        await engine.dispose()

    if failures:
        raise ExceptionGroup("One or more automated funding tasks failed.", failures)


async def run_loop(settings: Settings) -> None:
    """Run unattended scans, reports and report-email delivery continuously."""

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
                await _run_post_scan_automation(
                    settings,
                    session_factory,
                    tuple(successful_run_ids),
                )
            except Exception:
                logger.exception(
                    "Automatic report/email processing failed; next interval will retry."
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
        help="once = one unattended cycle; loop = repeat at SCAN_INTERVAL_MINUTES",
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
