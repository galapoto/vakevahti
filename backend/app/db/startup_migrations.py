import asyncio
import os
import sys
from pathlib import Path

from app.config import Settings

_BACKEND_ROOT = Path(__file__).resolve().parents[2]


class StartupMigrationError(RuntimeError):
    """Raised when the opt-in Alembic startup migration fails."""


async def run_startup_migrations(settings: Settings) -> None:
    """Upgrade the configured database to Alembic head in an isolated subprocess."""

    environment = os.environ.copy()
    environment["DATABASE_URL"] = settings.database_url

    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "alembic",
        "-c",
        "alembic.ini",
        "upgrade",
        "head",
        cwd=_BACKEND_ROOT,
        env=environment,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    return_code = await process.wait()
    if return_code != 0:
        raise StartupMigrationError(
            f"Alembic startup migration failed with exit code {return_code}."
        )
