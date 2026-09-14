from datetime import UTC, date, datetime
from uuid import NAMESPACE_URL, UUID, uuid5

from fastapi import APIRouter, HTTPException, status

from app.api.case_schemas import (
    FundingCaseArtifactResponse,
    FundingCaseCallSummary,
    FundingCaseEmailPackage,
    FundingCaseEmailQueueResponse,
    FundingCaseEmailSendRequest,
    FundingCaseResponse,
    FundingCaseTaskResponse,
)
from app.api.preview_routes import _OBSERVED_AT, _PREVIEW_CALLS
from app.api.schemas import FundingCallDetail
from app.services.funding_cases import compose_case_email_package, stable_case_id

router = APIRouter(prefix="/api/cases", tags=["funding-cases-preview"])


def _artifact_id(case_id: UUID, artifact_type: str, version: int) -> UUID:
    return uuid5(NAMESPACE_URL, f"vakevahti-preview:{case_id}:{artifact_type}:{version}")


def _artifact(
    *,
    case_id: UUID,
    call: FundingCallDetail,
    artifact_type: str,
    source_app: str,
    status_value: str,
    title: str,
    summary: str,
    content_text: str | None,
    content_url: str | None,
    version: int,
    approved_at: datetime | None,
) -> FundingCaseArtifactResponse:
    return FundingCaseArtifactResponse(
        id=_artifact_id(case_id, f"{source_app}-{artifact_type}", version),
        case_id=case_id,
        source_app=source_app,
        artifact_type=artifact_type,
        external_artifact_id=f"{artifact_type.lower()}-{call.id}",
        version=version,
        status=status_value,
        title=title,
        summary=summary,
        content_url=content_url,
        content_text=content_text,
        mime_type="text/plain" if content_url is None else "text/html",
        checksum=None,
        metadata={
            "preview_fixture": True,
            "automated": source_app == "VAKEVAHTI_AUTOMATION",
            "requires_review": status_value == "DRAFT",
        },
        created_at=_OBSERVED_AT,
        updated_at=approved_at or _OBSERVED_AT,
        approved_at=approved_at,
    )


def _artifacts(case_id: UUID, call: FundingCallDetail) -> list[FundingCaseArtifactResponse]:
    approved_at = datetime(2026, 9, 12, 9, 30, tzinfo=UTC)
    review_case = call.relevance_status == "NEEDS_REVIEW"

    if review_case:
        process = _artifact(
            case_id=case_id,
            call=call,
            artifact_type="PROCESS_DESCRIPTION",
            source_app="VAKEVAHTI_AUTOMATION",
            status_value="DRAFT",
            title="Automaattinen prosessikuvausluonnos",
            summary=(
                "VakeVahti loi aloitusluonnoksen tunnetuista rahoitustiedoista. "
                "Tuntemattomat kohdat on merkitty Tarkistettava."
            ),
            content_text=(
                "Prosessin omistaja: Tarkistettava\n"
                "Hakemuksen valmisteluvastuu: Tarkistettava\n"
                "Pakolliset liitteet: Tarkistettava lähdeaineistosta\n"
                "Sisäinen päätöspiste: Tarkistettava\n"
                "Hakemuksen lähetysvastuu: Tarkistettava"
            ),
            content_url=None,
            version=call.current_version,
            approved_at=None,
        )
        reporting = _artifact(
            case_id=case_id,
            call=call,
            artifact_type="REPORTING",
            source_app="VAKEVAHTI_AUTOMATION",
            status_value="DRAFT",
            title="Automaattinen raportointisuunnitelmaluonnos",
            summary=(
                "VakeVahti loi raportoinnin aloitusrungon. Rahoittajakohtaiset "
                "tuntemattomat vaatimukset on merkitty Tarkistettava."
            ),
            content_text=(
                "Raportoinnin vastuuhenkilö: Tarkistettava\n"
                "Raportointijaksot: Tarkistettava lähdeaineistosta\n"
                "Pakolliset KPI:t/mittarit: Tarkistettava lähdeaineistosta\n"
                "Loppuraportin määräpäivä: Tarkistettava"
            ),
            content_url=None,
            version=call.current_version,
            approved_at=None,
        )
    else:
        process = _artifact(
            case_id=case_id,
            call=call,
            artifact_type="PROCESS_DESCRIPTION",
            source_app="PROSESSIKUVAUS",
            status_value="APPROVED",
            title="Hakuprosessin prosessikuvaus",
            summary=(
                "Hyväksytty prosessikuvaus sisältää omistajan, valmisteluvaiheet, "
                "päätöspisteet ja hakemuksen lähetysvastuun."
            ),
            content_text=None,
            content_url=f"https://intra.example.test/process/{call.id}/v2",
            version=2,
            approved_at=approved_at,
        )
        reporting = _artifact(
            case_id=case_id,
            call=call,
            artifact_type="REPORTING",
            source_app="RAPORTOINTI",
            status_value="APPROVED",
            title="Rahoituksen raportointisuunnitelma",
            summary=(
                "Raportointirunko sisältää keskeiset KPI:t, vastuut, seurannan ja "
                "rahoittajan raportointipisteet."
            ),
            content_text="Kvartaaliseuranta, vastuuhenkilö ja päätösraportin tarkistuspisteet.",
            content_url=f"https://intra.example.test/reporting/{call.id}/v1",
            version=1,
            approved_at=approved_at,
        )

    funding_report = _artifact(
        case_id=case_id,
        call=call,
        artifact_type="FUNDING_REPORT",
        source_app="VAKEVAHTI",
        status_value="DRAFT",
        title="VakeHyvän rahoitusraportti",
        summary="Automaattisesti muodostettu rahoitushaun yhteenveto ja soveltuvuusperuste.",
        content_text=None,
        content_url=None,
        version=1,
        approved_at=None,
    )
    return [process, reporting, funding_report]


def _task(
    *,
    call_id: int,
    position: int,
    key: str,
    title: str,
    detail: str,
    completed: bool,
    due_on: date | None,
) -> FundingCaseTaskResponse:
    return FundingCaseTaskResponse(
        id=call_id * 10 + position,
        task_key=key,
        title=title,
        detail=detail,
        status="COMPLETED" if completed else "OPEN",
        due_on=due_on,
        created_at=_OBSERVED_AT,
        updated_at=_OBSERVED_AT,
        completed_at=_OBSERVED_AT if completed else None,
    )


def _tasks(call: FundingCallDetail) -> tuple[list[FundingCaseTaskResponse], str]:
    due_on = call.application_deadline_on
    relevant = call.relevance_status == "RELEVANT"
    tasks = [
        _task(
            call_id=call.id,
            position=1,
            key="ELIGIBILITY_REVIEW",
            title="Varmista hakukelpoisuus",
            detail="Tarkista VakeHyvän hakukelpoisuus ja rahoitushaun rajaukset.",
            completed=relevant,
            due_on=due_on,
        ),
        _task(
            call_id=call.id,
            position=2,
            key="PROCESS_DESCRIPTION",
            title="Valmistele prosessikuvaus",
            detail=(
                "Prosessikuvaus on hyväksytty."
                if relevant
                else "Automaattinen luonnos on valmis tarkistettavaksi."
            ),
            completed=relevant,
            due_on=due_on,
        ),
        _task(
            call_id=call.id,
            position=3,
            key="REPORTING_PLAN",
            title="Valmistele raportointisuunnitelma",
            detail=(
                "Raportointisuunnitelma on hyväksytty."
                if relevant
                else "Automaattinen luonnos on valmis tarkistettavaksi."
            ),
            completed=relevant,
            due_on=due_on,
        ),
        _task(
            call_id=call.id,
            position=4,
            key="FUNDING_REPORT_REVIEW",
            title="Tarkista rahoitusraportti ja sähköpostipaketti",
            detail="Tarkista raportti, vastaanottajat, viesti ja mukaan valitut aineistot.",
            completed=False,
            due_on=due_on,
        ),
    ]
    next_action = (
        "Tarkista rahoitusraportti ja sähköpostipaketti"
        if relevant
        else "Varmista hakukelpoisuus"
    )
    return tasks, next_action


def _preview_cases() -> list[FundingCaseResponse]:
    cases: list[FundingCaseResponse] = []
    for call in _PREVIEW_CALLS:
        case_id = stable_case_id(call.source_code, str(call.id))
        tasks, next_action = _tasks(call)
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
                artifacts=_artifacts(case_id, call),
                tasks=tasks,
                next_action=next_action,
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
    compose_case_email_package(case, artifact_ids=payload.artifact_ids)
    return FundingCaseEmailQueueResponse(
        case_id=case_id,
        report_id=uuid5(NAMESPACE_URL, f"vakevahti-preview-report:{case_id}"),
        delivery_id=case.funding_call.id,
        delivery_status="PREVIEW_QUEUED",
        recipients=payload.recipient_emails,
    )
