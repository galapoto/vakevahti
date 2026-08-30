import argparse
import asyncio

from app.config import get_settings
from app.db.session import create_engine, create_session_factory
from app.scanners.stm import STMScanner
from app.services.ingestion import ScanTrigger, run_source_ingestion


async def scan_stm() -> None:
    scanner = STMScanner(get_settings())
    calls = await scanner.scan()

    print(f"STM calls discovered: {len(calls)}")
    for index, call in enumerate(calls, start=1):
        print(f"{index:02d}. {call.title}")


async def scan_stm_persist() -> None:
    settings = get_settings()
    scanner = STMScanner(settings)
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
        "STM persistence complete: "
        f"run_id={result.run_id} "
        f"baseline={persistence.baseline} "
        f"new={persistence.new_count} "
        f"unchanged={persistence.unchanged_count} "
        f"changed={persistence.changed_count}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="VakeVahti development CLI")
    parser.add_argument("command", choices=["scan-stm", "scan-stm-persist"])
    args = parser.parse_args()

    if args.command == "scan-stm":
        asyncio.run(scan_stm())
    elif args.command == "scan-stm-persist":
        asyncio.run(scan_stm_persist())


if __name__ == "__main__":
    main()
