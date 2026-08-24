from typing import Protocol

from app.domain.funding_call import FundingCallCandidate


class FundingSourceAdapter(Protocol):
    """Contract implemented by each external funding source."""

    source_code: str

    async def scan(self) -> list[FundingCallCandidate]:
        """Fetch, parse, normalize, and return current source candidates."""
        ...
