import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from app.config import get_settings
from app.scanners.stm import SourceStructureError, STMScanner
from app.ui.dashboard import DASHBOARD_HTML

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.2.0")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def dashboard() -> HTMLResponse:
    """Development dashboard for demonstrating currently implemented capabilities."""

    return HTMLResponse(DASHBOARD_HTML)


@app.get("/health/live", tags=["health"])
async def live() -> dict[str, str]:
    """Liveness probe: proves the API process is running."""

    return {"status": "ok", "service": settings.app_name}


@app.get("/api/demo/stm-calls", tags=["demo"])
async def demo_stm_calls() -> dict[str, object]:
    """Run the real STM adapter and return validated calls for the development UI."""

    try:
        calls = await STMScanner(settings).scan()
    except (httpx.HTTPError, SourceStructureError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {
        "source": "STM",
        "count": len(calls),
        "calls": [call.model_dump(mode="json") for call in calls],
    }
