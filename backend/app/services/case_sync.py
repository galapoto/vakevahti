from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import FundingCallRecord
from app.services.case_automation import sync_case_automation_tasks
from app.services.case_requirements import sync_case_requirements
from app.services.case_starter_drafts import ensure_case_starter_drafts
from app.services.funding_cases import ensure_funding_case


async def ensure_cases_for_source_snapshot(
    session: AsyncSession,
    *,
    source_code: str,
    observed_at: datetime,
) -> int:
    """Synchronize case requirements, starter drafts and tasks after a successful scan."""

    result = await session.execute(
        select(FundingCallRecord).where(
            FundingCallRecord.source_code == source_code,
            FundingCallRecord.last_seen_at == observed_at,
        )
    )
    count = 0
    for record in result.scalars():
        case = await ensure_funding_case(session, record, observed_at=observed_at)
        if case is not None:
            await sync_case_requirements(
                session,
                case=case,
                record=record,
                observed_at=observed_at,
            )
            await ensure_case_starter_drafts(
                session,
                case=case,
                record=record,
                observed_at=observed_at,
            )
            await sync_case_automation_tasks(
                session,
                case=case,
                record=record,
                observed_at=observed_at,
            )
            count += 1
    return count
