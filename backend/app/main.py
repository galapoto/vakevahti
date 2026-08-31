from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.api.preview_routes import router as preview_api_router
from app.api.routes import router as api_router
from app.config import Settings, get_settings
from app.db.session import create_engine, create_session_factory
from app.scanners.stm import SourceStructureError, STMScanner
from app.ui.dashboard import DASHBOARD_HTML
from app.ui.theme import apply_dashboard_theme


def create_app(
    runtime_settings: Settings | None = None,
    *,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
) -> FastAPI:
    """Create the FastAPI application with an injectable database boundary."""

    settings = runtime_settings or get_settings()
    owned_engine: AsyncEngine | None = None

    if not settings.dashboard_preview_mode and session_factory is None:
        owned_engine = create_engine(settings)
        session_factory = create_session_factory(owned_engine)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            if owned_engine is not None:
                await owned_engine.dispose()

    application = FastAPI(
        title=settings.app_name,
        version="0.4.0",
        lifespan=lifespan,
    )
    application.state.settings = settings
    application.state.session_factory = session_factory
    selected_router = preview_api_router if settings.dashboard_preview_mode else api_router
    application.include_router(selected_router)

    @application.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def dashboard() -> HTMLResponse:
        """Serve the operator dashboard without triggering source scans."""

        html = apply_dashboard_theme(DASHBOARD_HTML)
        if settings.dashboard_preview_mode:
            html = html.replace(
                "Tallennettu tilannekuva",
                "Kehitysesikatselu · fixture-data",
                1,
            )
        return HTMLResponse(html)

    @application.get("/health/live", tags=["health"])
    async def live() -> dict[str, str]:
        """Liveness probe: proves the API process is running."""

        return {"status": "ok", "service": settings.app_name}

    @application.get("/api/demo/stm-calls", tags=["demo"])
    async def demo_stm_calls() -> dict[str, object]:
        """Run the real STM adapter and return validated calls for engineering diagnostics."""

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
