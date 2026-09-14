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
    haeavustuksia_url: HttpUrl = HttpUrl(
        "https://www.haeavustuksia.fi/fi/?isAdditionalSearchOpen=true"
    )
    eura_url: HttpUrl = HttpUrl("https://eura2021.fi/hakuilmoitukset")
    sitra_url: HttpUrl = HttpUrl("https://asiointi.sitra.fi/")
    academy_url: HttpUrl = HttpUrl(
        "https://www.aka.fi/tutkimusrahoitus/hae-rahoitusta/haut/"
    )
    http_timeout_seconds: float = 30.0
    user_agent: str = "VakeVahti/0.1 (+maintainer-contact-not-configured)"
    database_url: str = (
        "postgresql+asyncpg://vakevahti:vakevahti@localhost:5432/vakevahti"
    )
    enabled_sources: str = "STM"
    scan_interval_minutes: int = Field(default=60, ge=5, le=1440)
    scan_run_on_startup: bool = True
    enable_live_test_routes: bool = False
    dashboard_preview_mode: bool = False
    migrate_database_on_startup: bool = False
    enable_report_write_routes: bool = False
    automatic_report_enabled: bool = True
    report_email_recipients: str = ""
    report_email_enabled: bool = False
    report_email_auto_send: bool = True
    report_email_from: str = ""
    smtp_host: str = ""
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_starttls: bool = True
    smtp_ssl: bool = False
    smtp_timeout_seconds: float = Field(default=30.0, gt=0, le=120)
    report_email_retry_base_minutes: int = Field(default=5, ge=1, le=1440)
    report_email_retry_max_minutes: int = Field(default=240, ge=1, le=10080)

    @property
    def enabled_source_codes(self) -> tuple[str, ...]:
        """Return normalized, de-duplicated source codes in configured order."""

        codes: list[str] = []
        seen: set[str] = set()
        for raw_source in self.enabled_sources.split(","):
            source_code = raw_source.strip().upper()
            if source_code and source_code not in seen:
                seen.add(source_code)
                codes.append(source_code)

        if not codes:
            raise ValueError("ENABLED_SOURCES must contain at least one source code.")
        return tuple(codes)

    @property
    def report_recipient_emails(self) -> tuple[str, ...]:
        """Return normalized report recipients configured for unattended delivery."""

        normalized = self.report_email_recipients.replace(";", ",")
        recipients: list[str] = []
        seen: set[str] = set()
        for raw in normalized.split(","):
            value = raw.strip()
            if not value:
                continue
            lowered = value.casefold()
            if lowered in seen:
                continue
            seen.add(lowered)
            recipients.append(value)
        return tuple(recipients)

    @property
    def smtp_delivery_configured(self) -> bool:
        """Return whether automatic email has the minimum non-secret transport config."""

        return bool(
            self.report_email_enabled
            and self.report_email_from.strip()
            and self.smtp_host.strip()
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
