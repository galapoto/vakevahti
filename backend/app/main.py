from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.api.live_test import router as live_test_router
from app.api.preview_routes import router as preview_api_router
from app.api.routes import router as api_router
from app.config import Settings, get_settings
from app.db.session import create_engine, create_session_factory
from app.db.startup_migrations import run_startup_migrations
from app.scanners.stm import SourceStructureError, STMScanner
from app.ui.dashboard import DASHBOARD_HTML
from app.ui.dashboard_certainty_filter import render_dashboard_certainty_filter
from app.ui.dashboard_customization import render_dashboard_html
from app.ui.dashboard_date_precision import render_dashboard_date_precision
from app.ui.live_source_test import LIVE_SOURCE_TEST_HTML
from app.ui.theme import apply_dashboard_theme


def create_app(
    runtime_settings: Settings | None = None,
    *,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
) -> FastAPI:
    """Create the FastAPI application with injectable persistence and preview boundaries."""

    settings = runtime_settings or get_settings()
    owned_engine: AsyncEngine | None = None

    if not settings.dashboard_preview_mode and session_factory is None:
        owned_engine = create_engine(settings)
        session_factory = create_session_factory(owned_engine)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if settings.migrate_database_on_startup and not settings.dashboard_preview_mode:
            await run_startup_migrations(settings)
        try:
            yield
        finally:
            if owned_engine is not None:
                await owned_engine.dispose()

    application = FastAPI(
        title=settings.app_name,
        version="0.11.0",
        lifespan=lifespan,
    )
    application.state.settings = settings
    application.state.session_factory = session_factory
    selected_router = preview_api_router if settings.dashboard_preview_mode else api_router
    application.include_router(selected_router)

    if settings.enable_live_test_routes:
        application.include_router(live_test_router)

        @application.get(
            "/test/live-sources",
            response_class=HTMLResponse,
            include_in_schema=False,
        )
        async def live_source_test_console() -> HTMLResponse:
            """Serve the database-free live source test console in opt-in environments."""

            return HTMLResponse(LIVE_SOURCE_TEST_HTML)

    @application.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def dashboard() -> HTMLResponse:
        """Serve the employee dashboard without triggering source acquisition."""

        customized = render_dashboard_html(DASHBOARD_HTML)
        precise = render_dashboard_date_precision(customized)
        filtered = render_dashboard_certainty_filter(precise)
        themed = apply_dashboard_theme(filtered)
        if settings.dashboard_preview_mode:
            themed = themed.replace(
                "Tallennettu tilannekuva",
                "Kehitysesikatselu · fixture-data",
                1,
            )
        return HTMLResponse(themed)

    @application.get("/health/live", tags=["health"])
    async def live() -> dict[str, str]:
        """Liveness probe: proves the API process is running."""

        return {"status": "ok", "service": settings.app_name}

    @application.get("/health/ready", tags=["health"])
    async def ready() -> JSONResponse:
        """Readiness probe for either fixture preview or persisted PostgreSQL mode."""

        if settings.dashboard_preview_mode:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "preview_ready",
                    "service": settings.app_name,
                    "database": "bypassed",
                    "storage": "fixture",
                },
            )

        if session_factory is None:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not_ready",
                    "service": settings.app_name,
                    "database": "unavailable",
                    "error_type": "SessionFactoryUnavailable",
                },
            )

        try:
            async with session_factory() as session:
                await session.execute(text("SELECT 1"))
        except Exception as exc:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not_ready",
                    "service": settings.app_name,
                    "database": "unavailable",
                    "error_type": type(exc).__name__,
                },
            )

        return JSONResponse(
            status_code=200,
            content={
                "status": "ready",
                "service": settings.app_name,
                "database": "ok",
            },
        )

    @application.get("/api/demo/stm-calls", tags=["demo"])
    async def demo_stm_calls() -> dict[str, object]:
        """Run the real STM adapter for engineering diagnostics only."""

        try:
            calls = await STMScanner(settings).scan()
        except (httpx.HTTPError, SourceStructureError) as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        return {
            "source": "STM",
            "count": len(calls),
            "calls": [call.model_dump(mode="json") for call in calls],
        }

    return application


app = create_app()
