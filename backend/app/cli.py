import argparse
import asyncio

from app.config import get_settings
from app.db.session import create_engine, create_session_factory
from app.scanners.stm import STMScanner
from app.services.persistence import persist_candidates


async def scan_stm() -> None:
    scanner = STMScanner(get_settings())
    calls = await scanner.scan()

    print(f"STM calls discovered: {len(calls)}")
    for index, call in enumerate(calls, start=1):
        print(f"{index:02d}. {call.title}")


async def scan_stm_persist() -> None:
    settings = get_settings()
    scanner = STMScanner(settings)
    calls = await scanner.scan()

    engine = create_engine(settings)
    session_factory = create_session_factory(engine)

    try:
        async with session_factory() as session:
            async with session.begin():
                result = await persist_candidates(session, calls)
    finally:
        await engine.dispose()

    print(
        "STM persistence complete: "
        f"baseline={result.baseline} "
        f"new={result.new_count} "
        f"unchanged={result.unchanged_count} "
        f"changed={result.changed_count}"
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
