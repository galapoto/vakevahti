from datetime import UTC, datetime
from uuid import NAMESPACE_URL, UUID, uuid5

from fastapi import APIRouter, HTTPException, status

from app.api.case_schemas import (
    FundingCaseArtifactResponse,
    FundingCaseCallSummary,
    FundingCaseEmailPackage,
    FundingCaseEmailQueueResponse,
    FundingCaseEmailSendRequest,
    FundingCaseResponse,
)
from app.api.preview_routes import _OBSERVED_AT, _PREVIEW_CALLS
from app.services.funding_cases import compose_case_email_package, stable_case_id

router = APIRouter(prefix="/api/cases", tags=["funding-cases-preview"])


def _artifact_id(case_id: UUID, artifact_type: str, version: int) -> UUID:
    return uuid5(NAMESPACE_URL, f"vakevahti-preview:{case_id}:{artifact_type}:{version}")


def _artifacts(case_id: UUID, call_id: int) -> list[FundingCaseArtifactResponse]:
    approved_at = datetime(2026, 9, 12, 9, 30, tzinfo=UTC)
    return [
        FundingCaseArtifactResponse(
            id=_artifact_id(case_id, "PROCESS_DESCRIPTION", 2),
            case_id=case_id,
            source_app="PROSESSIKUVAUS",
            artifact_type="PROCESS_DESCRIPTION",
            external_artifact_id=f"process-{call_id}",
            version=2,
            status="APPROVED",
            title="Hakuprosessin prosessikuvaus",
            summary=(
                "Hyväksytty prosessikuvaus sisältää omistajan, valmisteluvaiheet, "
                "päätöspisteet ja hakemuksen lähetysvastuun."
            ),
            content_url=f"https://intra.example.test/process/{call_id}/v2",
            content_text=None,
            mime_type="text/html",
            checksum=None,
            metadata={"preview_fixture": True},
            created_at=_OBSERVED_AT,
            updated_at=approved_at,
            approved_at=approved_at,
        ),
        FundingCaseArtifactResponse(
            id=_artifact_id(case_id, "REPORTING", 1),
            case_id=case_id,
            source_app="RAPORTOINTI",
            artifact_type="REPORTING",
            external_artifact_id=f"reporting-{call_id}",
            version=1,
            status="APPROVED",
            title="Rahoituksen raportointisuunnitelma",
            summary=(
                "Raportointirunko sisältää keskeiset KPI:t, vastuut, seurannan ja "
                "rahoittajan raportointipisteet."
            ),
            content_url=f"https://intra.example.test/reporting/{call_id}/v1",
            content_text="Kvartaaliseuranta, vastuuhenkilö ja päätösraportin tarkistuspisteet.",
            mime_type="text/html",
            checksum=None,
            metadata={"preview_fixture": True},
            created_at=_OBSERVED_AT,
            updated_at=approved_at,
            approved_at=approved_at,
        ),
        FundingCaseArtifactResponse(
            id=_artifact_id(case_id, "FUNDING_REPORT", 1),
            case_id=case_id,
            source_app="VAKEVAHTI",
            artifact_type="FUNDING_REPORT",
            external_artifact_id=f"funding-report-{call_id}",
            version=1,
            status="DRAFT",
            title="VakeHyvän rahoitusraportti",
            summary="Automaattisesti muodostettu rahoitushaun yhteenveto ja soveltuvuusperuste.",
            content_url=None,
            content_text=None,
            mime_type="text/plain",
            checksum=None,
            metadata={"preview_fixture": True, "automated": True},
            created_at=_OBSERVED_AT,
            updated_at=_OBSERVED_AT,
            approved_at=None,
        ),
    ]


def _preview_cases() -> list[FundingCaseResponse]:
    cases: list[FundingCaseResponse] = []
    for call in _PREVIEW_CALLS:
        case_id = stable_case_id(call.source_code, str(call.id))
        cases.append(
            FundingCaseResponse(
                id=case_id,
                status="OPEN",
                created_at=_OBSERVED_AT,
                updated_at=_OBSERVED_AT,
                funding_call=FundingCaseCallSummary(
                    id=call.id,
                    source_code=call.source_code,
                    title=call.title,
                    source_url=call.source_url,
                    application_deadline_on=call.application_deadline_on,
                    application_deadline_at=call.application_deadline_at,
                    relevance_status=call.relevance_status,
                    relevance_reason=call.relevance_reason,
                    current_version=call.current_version,
                ),
                artifacts=_artifacts(case_id, call.id),
            )
        )
    return cases


_PREVIEW_CASES = _preview_cases()


def _find_case(case_id: UUID) -> FundingCaseResponse:
    for case in _PREVIEW_CASES:
        if case.id == case_id:
            return case
    raise HTTPException(status_code=404, detail="Funding case not found.")


@router.get("", response_model=list[FundingCaseResponse])
async def cases() -> list[FundingCaseResponse]:
    return _PREVIEW_CASES


@router.get("/{case_id}", response_model=FundingCaseResponse)
async def case_detail(case_id: UUID) -> FundingCaseResponse:
    return _find_case(case_id)


@router.get("/{case_id}/email-package", response_model=FundingCaseEmailPackage)
async def email_package(case_id: UUID) -> FundingCaseEmailPackage:
    return compose_case_email_package(_find_case(case_id))


@router.post(
    "/{case_id}/email",
    response_model=FundingCaseEmailQueueResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def queue_preview_email(
    case_id: UUID,
    payload: FundingCaseEmailSendRequest,
) -> FundingCaseEmailQueueResponse:
    case = _find_case(case_id)
    selected = payload.artifact_ids
    compose_case_email_package(case, artifact_ids=selected)
    return FundingCaseEmailQueueResponse(
        case_id=case_id,
        report_id=uuid5(NAMESPACE_URL, f"vakevahti-preview-report:{case_id}"),
        delivery_id=case.funding_call.id,
        delivery_status="PREVIEW_QUEUED",
        recipients=payload.recipient_emails,
    )
