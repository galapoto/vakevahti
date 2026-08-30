from collections.abc import AsyncIterator
from typing import cast

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import Settings


def get_session_factory(request: Request) -> async_sessionmaker[AsyncSession]:
    """Return the application-owned async session factory."""

    return cast(async_sessionmaker[AsyncSession], request.app.state.session_factory)


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Provide one read session per request without leaking transaction ownership."""

    session_factory = get_session_factory(request)
    async with session_factory() as session:
        yield session


def get_runtime_settings(request: Request) -> Settings:
    """Expose the resolved runtime configuration to routes that need contract context."""

    return cast(Settings, request.app.state.settings)
