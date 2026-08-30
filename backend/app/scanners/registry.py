from collections.abc import Callable, Sequence

from app.config import Settings
from app.scanners.academy import AcademyScanner
from app.scanners.base import FundingSourceAdapter
from app.scanners.sitra import SitraScanner
from app.scanners.stm import STMScanner

ScannerFactory = Callable[[Settings], FundingSourceAdapter]


class UnknownFundingSourceError(ValueError):
    """Raised when configuration names a source that has no registered adapter."""


def _stm_factory(settings: Settings) -> FundingSourceAdapter:
    return STMScanner(settings)


def _sitra_factory(settings: Settings) -> FundingSourceAdapter:
    return SitraScanner(settings)


def _academy_factory(settings: Settings) -> FundingSourceAdapter:
    return AcademyScanner(settings)


_SOURCE_FACTORIES: dict[str, ScannerFactory] = {
    "STM": _stm_factory,
    "SITRA": _sitra_factory,
    "ACADEMY": _academy_factory,
}


def registered_source_codes() -> tuple[str, ...]:
    """Return source codes that this build can instantiate."""

    return tuple(sorted(_SOURCE_FACTORIES))


def build_scanners(
    settings: Settings,
    source_codes: Sequence[str] | None = None,
) -> tuple[FundingSourceAdapter, ...]:
    """Build configured source adapters without coupling orchestration to concrete scanners."""

    requested = source_codes or settings.enabled_source_codes
    scanners: list[FundingSourceAdapter] = []

    for raw_code in requested:
        source_code = raw_code.strip().upper()
        factory = _SOURCE_FACTORIES.get(source_code)
        if factory is None:
            available = ", ".join(registered_source_codes()) or "none"
            raise UnknownFundingSourceError(
                f"Unknown funding source {source_code!r}. Registered sources: {available}."
            )
        scanners.append(factory(settings))

    if not scanners:
        raise ValueError("At least one funding source must be enabled.")

    return tuple(scanners)
