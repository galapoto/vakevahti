from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.api.preview_routes import _PREVIEW_CALLS
from app.api.requirement_schemas import FundingCaseRequirementResponse
from app.services.case_requirements import derive_requirement_specs
from app.services.funding_cases import stable_case_id

router = APIRouter(prefix="/api/cases", tags=["funding-case-requirements-preview"])


def _call_for_case(case_id: UUID):  # type: ignore[no-untyped-def]
    for call in _PREVIEW_CALLS:
        if stable_case_id(call.source_code, str(call.id)) == case_id:
            return call
    raise HTTPException(status_code=404, detail="Funding case not found.")


@router.get(
    "/{case_id}/requirements",
    response_model=list[FundingCaseRequirementResponse],
)
async def preview_case_requirements(
    case_id: UUID,
) -> list[FundingCaseRequirementResponse]:
    call = _call_for_case(case_id)
    evidence = list(call.evidence)
    if call.relevance_status == "RELEVANT":
        evidence.append(
            {
                "section": "Kehitysesikatselun lähdenäyttö",
                "text": (
                    "Fixture-hakuilmoituksessa kuvataan vaadittavia liitteitä, budjettia ja "
                    "raportointia. Täsmälliset ehdot on silti tarkistettava lähteestä."
                ),
                "source_url": call.source_url,
            }
        )

    specs = derive_requirement_specs(
        source_url=call.source_url,
        relevance_status=call.relevance_status,
        relevance_reason=call.relevance_reason,
        description_text=call.description_text,
        evidence=evidence,
        application_deadline_on=call.application_deadline_on,
        application_deadline_at=call.application_deadline_at,
    )
    return [
        FundingCaseRequirementResponse(
            requirement_key=spec.requirement_key,
            category=spec.category,
            certainty=spec.certainty.value,
            title=spec.title,
            statement=spec.statement,
            source_url=spec.source_url,
            evidence=spec.evidence,
            funding_call_version=call.current_version,
        )
        for spec in specs
    ]
