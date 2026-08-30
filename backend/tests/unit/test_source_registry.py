import pytest

from app.config import Settings
from app.scanners.registry import UnknownFundingSourceError, build_scanners


def test_enabled_source_codes_normalize_comma_separated_config() -> None:
    settings = Settings(enabled_sources=" stm, STM ")

    assert settings.enabled_source_codes == ("STM", "STM")


def test_registry_builds_configured_stm_adapter() -> None:
    settings = Settings(enabled_sources="STM")

    scanners = build_scanners(settings)

    assert len(scanners) == 1
    assert scanners[0].source_code == "STM"


def test_registry_rejects_unregistered_source() -> None:
    settings = Settings(enabled_sources="UNKNOWN")

    with pytest.raises(UnknownFundingSourceError, match="UNKNOWN"):
        build_scanners(settings)
