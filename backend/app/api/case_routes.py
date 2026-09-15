from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.case_schemas import (
    FundingCaseArtifactCreate,
    FundingCaseArtifactResponse,
    FundingCaseEmailPackage,
    FundingCaseEmailQueueResponse,
    FundingCaseEmailSendRequest,
    FundingCaseResponse,
)
from app.api.dependencies import get_db_session
from app.config import Settings
from app.security.identity import ActorContext, FundingPermission, require_permission
from app.services.case_automation import refresh_case_automation
from app.services.funding_cases import (
    FundingCaseArtifactConflictError,
    FundingCaseArtifactSelectionError,
    FundingCaseNotFoundError,
    get_case_email_package,
    get_funding_case,
    list_funding_cases,
    queue_case_email,
    register_case_artifact,
)

router = APIRouter(prefix="/api/cases", tags=["funding-cases"])
SessionDependency = Annotated[AsyncSession, Depends(get_db_session)]
ReadActor = Annotated[
    ActorContext,
    Depends(require_permission(FundingPermission.OPPORTUNITIES_READ)),
]
EditActor = Annotated[
    ActorContext,
    Depends(require_permission(FundingPermission.APPLICATIONS_EDIT)),
]


def _require_case_writes(request: Request) -> None:
    settings: Settings = request.app.state.settings
    if not settings.enable_case_write_routes:
        raise HTTPException(status_code=404, detail="Case write routes are disabled.")


@router.get("", response_model=list[FundingCaseResponse])
async def cases(
    session: SessionDependency,
    _actor: ReadActor,
) -> list[FundingCaseResponse]:
    return await list_funding_cases(session)


@router.get("/{case_id}", response_model=FundingCaseResponse)
async def case_detail(
    case_id: UUID,
    session: SessionDependency,
    _actor: ReadActor,
) -> FundingCaseResponse:
    try:
        return await get_funding_case(session, case_id)
    except FundingCaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Funding case not found.") from exc


@router.get("/{case_id}/email-package", response_model=FundingCaseEmailPackage)
async def email_package(
    case_id: UUID,
    session: SessionDependency,
    _actor: ReadActor,
) -> FundingCaseEmailPackage:
    try:
        return await get_case_email_package(session, case_id)
    except FundingCaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Funding case not found.") from exc


@router.post(
    "/{case_id}/artifacts",
    response_model=FundingCaseArtifactResponse,
    status_code=status.HTTP_201_CREATED,
)
async def attach_artifact(
    case_id: UUID,
    artifact: FundingCaseArtifactCreate,
    request: Request,
    session: SessionDependency,
    _actor: EditActor,
) -> FundingCaseArtifactResponse:
    _require_case_writes(request)
    try:
        response = await register_case_artifact(session, case_id, artifact)
        await refresh_case_automation(session, case_id)
        return response
    except FundingCaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Funding case not found.") from exc
    except FundingCaseArtifactConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/{case_id}/email",
    response_model=FundingCaseEmailQueueResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def send_case_email(
    case_id: UUID,
    payload: FundingCaseEmailSendRequest,
    request: Request,
    session: SessionDependency,
    _actor: EditActor,
) -> FundingCaseEmailQueueResponse:
    """Queue a case email to oneself or any validated recipient list."""

    _require_case_writes(request)
    try:
        return await queue_case_email(session, case_id, payload)
    except FundingCaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Funding case not found.") from exc
    except FundingCaseArtifactSelectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"missing_artifact_ids": [str(value) for value in exc.missing_ids]},
        ) from exc
