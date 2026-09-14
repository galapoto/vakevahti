from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import FundingCallRecord
from app.domain.funding_call import RelevanceStatus
from app.services.funding_cases import ensure_funding_case


async def ensure_cases_for_source_snapshot(
    session: AsyncSession,
    *,
    source_code: str,
    observed_at: datetime,
) -> int:
    """Ensure every employee-visible row in a successful source snapshot has a case."""

    result = await session.execute(
        select(FundingCallRecord).where(
            FundingCallRecord.source_code == source_code,
            FundingCallRecord.last_seen_at == observed_at,
            FundingCallRecord.relevance_status != RelevanceStatus.NOT_RELEVANT.value,
        )
    )
    count = 0
    for record in result.scalars():
        case = await ensure_funding_case(session, record, observed_at=observed_at)
        if case is not None:
            count += 1
    return count
