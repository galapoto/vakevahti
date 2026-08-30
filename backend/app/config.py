from functools import lru_cache

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "VakeVahti"
    app_env: str = "development"
    timezone: str = "Europe/Helsinki"
    stm_url: HttpUrl = HttpUrl("https://stm.fi/vuoden-2026-valtionavustushaut")
    http_timeout_seconds: float = 30.0
    user_agent: str = "VakeVahti/0.1 (+maintainer-contact-not-configured)"
    database_url: str = (
        "postgresql+asyncpg://vakevahti:vakevahti@localhost:5432/vakevahti"
    )
    enabled_sources: str = "STM"
    scan_interval_minutes: int = Field(default=60, ge=5, le=1440)
    scan_run_on_startup: bool = True

    @property
    def enabled_source_codes(self) -> tuple[str, ...]:
        """Return normalized comma-separated source codes from configuration."""

        codes = tuple(
            source.strip().upper()
            for source in self.enabled_sources.split(",")
            if source.strip()
        )
        if not codes:
            raise ValueError("ENABLED_SOURCES must contain at least one source code.")
        return codes


@lru_cache
def get_settings() -> Settings:
    return Settings()
