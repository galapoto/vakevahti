from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.api.requirement_schemas import FundingCaseRequirementResponse
from app.services.case_requirements import list_case_requirements
from app.services.funding_cases import FundingCaseNotFoundError

router = APIRouter(prefix="/api/cases", tags=["funding-case-requirements"])
SessionDependency = Annotated[AsyncSession, Depends(get_db_session)]


@router.get(
    "/{case_id}/requirements",
    response_model=list[FundingCaseRequirementResponse],
)
async def case_requirements(
    case_id: UUID,
    session: SessionDependency,
) -> list[FundingCaseRequirementResponse]:
    try:
        return await list_case_requirements(session, case_id)
    except FundingCaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Funding case not found.") from exc
