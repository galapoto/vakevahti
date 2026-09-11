import asyncio

import pytest

from app.config import Settings
from app.db.startup_migrations import StartupMigrationError, run_startup_migrations


class FakeProcess:
    def __init__(self, return_code: int) -> None:
        self._return_code = return_code

    async def wait(self) -> int:
        return self._return_code


@pytest.mark.asyncio
async def test_startup_migration_runs_alembic_with_configured_database(monkeypatch) -> None:
    captured = {}

    async def fake_create_subprocess_exec(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return FakeProcess(0)

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    settings = Settings(database_url="postgresql+asyncpg://user:secret@db.example/test")

    await run_startup_migrations(settings)

    assert captured["args"][1:] == ("-m", "alembic", "-c", "alembic.ini", "upgrade", "head")
    assert captured["kwargs"]["env"]["DATABASE_URL"] == settings.database_url
    assert captured["kwargs"]["stdout"] is asyncio.subprocess.DEVNULL
    assert captured["kwargs"]["stderr"] is asyncio.subprocess.DEVNULL


@pytest.mark.asyncio
async def test_startup_migration_failure_does_not_expose_database_url(monkeypatch) -> None:
    async def fake_create_subprocess_exec(*args, **kwargs):
        del args, kwargs
        return FakeProcess(7)

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    database_url = "postgresql+asyncpg://user:super-secret@db.example/test"

    with pytest.raises(StartupMigrationError) as exc_info:
        await run_startup_migrations(Settings(database_url=database_url))

    assert database_url not in str(exc_info.value)
    assert "exit code 7" in str(exc_info.value)
