from app.config import Settings
from app.scanners.registry import build_scanners


def test_worker_registry_returns_each_configured_source_once() -> None:
    settings = Settings(enabled_sources="STM,stm, STM")

    scanners = build_scanners(settings)

    assert [scanner.source_code for scanner in scanners] == ["STM"]
