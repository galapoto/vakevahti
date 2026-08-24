import argparse
import asyncio

from app.config import get_settings
from app.scanners.stm import STMScanner


async def scan_stm() -> None:
    scanner = STMScanner(get_settings())
    calls = await scanner.scan()

    print(f"STM calls discovered: {len(calls)}")
    for index, call in enumerate(calls, start=1):
        print(f"{index:02d}. {call.title}")


def main() -> None:
    parser = argparse.ArgumentParser(description="VakeVahti development CLI")
    parser.add_argument("command", choices=["scan-stm"])
    args = parser.parse_args()

    if args.command == "scan-stm":
        asyncio.run(scan_stm())


if __name__ == "__main__":
    main()
