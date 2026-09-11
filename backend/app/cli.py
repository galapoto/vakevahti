import argparse
import asyncio
from collections import Counter

from sqlalchemy import func, select

from app.config import get_settings
from app.db.models import FundingCallRecord, SourceState
from app.db.session import create_engine, create_session_factory
from app.domain.funding_call import RelevanceStatus
from app.scanners.registry import build_scanners, registered_source_codes
from app.services.ingestion import ScanTrigger, run_source_ingestion


def _source_code(value: str) -> str:
    normalized = value.strip().upper()
    available = registered_source_codes()
    if normalized not in available:
        choices = ", ".join(available)
        raise argparse.ArgumentTypeError(
            f"Unknown funding source {normalized!r}. Registered sources: {choices}."
        )
    return normalized


async def scan_source(source_code: str) -> None:
    settings = get_settings()
    scanner = build_scanners(settings, [source_code])[0]
    calls = await scanner.scan()

    distribution: Counter[str] = Counter(call.relevance_status.value for call in calls)
    print(f"{scanner.source_code} calls discovered: {len(calls)}")
    print(
        "Relevance distribution: "
        + " ".join(
            f"{status.value}={distribution[status.value]}" for status in RelevanceStatus
        )
    )
    for index, call in enumerate(calls, start=1):
        print(f"{index:03d}. [{call.relevance_status.value}] {call.title}")
        print(f"     {call.relevance_reason}")


async def scan_source_persist(source_code: str) -> None:
    settings = get_settings()
    scanner = build_scanners(settings, [source_code])[0]
    engine = create_engine(settings)
    session_factory = create_session_factory(engine)

    try:
        result = await run_source_ingestion(
            scanner,
            session_factory,
            trigger=ScanTrigger.MANUAL_CLI,
        )
    finally:
        await engine.dispose()

    persistence = result.persistence
    print(
        f"{scanner.source_code} persistence complete: "
        f"run_id={result.run_id} "
        f"baseline={persistence.baseline} "
        f"new={persistence.new_count} "
        f"unchanged={persistence.unchanged_count} "
        f"changed={persistence.changed_count}"
    )


async def source_distribution(source_code: str) -> None:
    """Print the current persisted classification distribution including exclusions."""

    settings = get_settings()
    engine = create_engine(settings)
    session_factory = create_session_factory(engine)

    try:
        async with session_factory() as session:
            state = await session.get(SourceState, source_code)
            if state is None or state.last_successful_scan_at is None:
                print(f"{source_code}: no successful persisted snapshot")
                return

            current = (
                FundingCallRecord.source_code == source_code,
                FundingCallRecord.last_seen_at == state.last_successful_scan_at,
            )
            count_rows = (
                await session.execute(
                    select(FundingCallRecord.relevance_status, func.count(FundingCallRecord.id))
                    .where(*current)
                    .group_by(FundingCallRecord.relevance_status)
                    .order_by(FundingCallRecord.relevance_status)
                )
            ).all()
            counts = {status: int(count) for status, count in count_rows}

            records = (
                await session.scalars(
                    select(FundingCallRecord)
                    .where(*current)
                    .order_by(
                        FundingCallRecord.relevance_status,
                        FundingCallRecord.application_deadline_on.asc().nulls_last(),
                        FundingCallRecord.id,
                    )
                )
            ).all()

        print(f"{source_code} current persisted snapshot: {len(records)} calls")
        distribution = " ".join(
            f"{status.value}={counts.get(status.value, 0)}"
            for status in RelevanceStatus
        )
        print(f"Relevance distribution: {distribution}")
        for index, record in enumerate(records, start=1):
            print(f"{index:03d}. [{record.relevance_status}] {record.title}")
            print(f"     {record.relevance_reason}")
            print(f"     {record.source_url}")
    finally:
        await engine.dispose()


async def scan_stm() -> None:
    """Compatibility alias for the original STM-only development command."""

    await scan_source("STM")


async def scan_stm_persist() -> None:
    """Compatibility alias for the original STM-only persistence command."""

    await scan_source_persist("STM")


def main() -> None:
    parser = argparse.ArgumentParser(description="VakeVahti development CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser(
        "scan-source",
        help="Scan one registered public funding source without persistence.",
    )
    scan_parser.add_argument("source", type=_source_code)

    persist_parser = subparsers.add_parser(
        "scan-source-persist",
        help="Scan and persist one registered funding source.",
    )
    persist_parser.add_argument("source", type=_source_code)

    distribution_parser = subparsers.add_parser(
        "source-distribution",
        help="Print the current persisted relevance distribution for one source.",
    )
    distribution_parser.add_argument("source", type=_source_code)

    subparsers.add_parser("scan-stm", help="Compatibility alias for scan-source STM.")
    subparsers.add_parser(
        "scan-stm-persist",
        help="Compatibility alias for scan-source-persist STM.",
    )

    args = parser.parse_args()

    if args.command == "scan-source":
        asyncio.run(scan_source(args.source))
    elif args.command == "scan-source-persist":
        asyncio.run(scan_source_persist(args.source))
    elif args.command == "source-distribution":
        asyncio.run(source_distribution(args.source))
    elif args.command == "scan-stm":
        asyncio.run(scan_stm())
    elif args.command == "scan-stm-persist":
        asyncio.run(scan_stm_persist())


if __name__ == "__main__":
    main()
