import pytest

from app.config import Settings
from app.scanners.registry import UnknownFundingSourceError, build_scanners


def test_enabled_source_codes_normalize_and_deduplicate_config() -> None:
    settings = Settings(
        enabled_sources=" stm, HAEAVUSTUKSIA, eura, STM, sitra, academy, SITRA "
    )

    assert settings.enabled_source_codes == (
        "STM",
        "HAEAVUSTUKSIA",
        "EURA",
        "SITRA",
        "ACADEMY",
    )


def test_registry_builds_all_required_source_adapters_in_order() -> None:
    settings = Settings(enabled_sources="STM,HAEAVUSTUKSIA,EURA,SITRA,ACADEMY")

    scanners = build_scanners(settings)

    assert [scanner.source_code for scanner in scanners] == [
        "STM",
        "HAEAVUSTUKSIA",
        "EURA",
        "SITRA",
        "ACADEMY",
    ]


def test_registry_rejects_unregistered_source() -> None:
    settings = Settings(enabled_sources="UNKNOWN")

    with pytest.raises(UnknownFundingSourceError, match="UNKNOWN"):
        build_scanners(settings)
