import argparse
import asyncio
from collections import Counter

from app.config import get_settings
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
    elif args.command == "scan-stm":
        asyncio.run(scan_stm())
    elif args.command == "scan-stm-persist":
        asyncio.run(scan_stm_persist())


if __name__ == "__main__":
    main()
