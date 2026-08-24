from fastapi import FastAPI

from app.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")


@app.get("/health/live", tags=["health"])
async def live() -> dict[str, str]:
    """Liveness probe: proves the API process is running."""

    return {"status": "ok", "service": settings.app_name}
