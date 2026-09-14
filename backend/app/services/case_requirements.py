from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.requirement_schemas import FundingCaseRequirementResponse
from app.db.case_models import FundingCase
from app.db.models import FundingCallRecord
from app.db.requirement_models import FundingCaseRequirement
from app.domain.funding_call import RelevanceStatus
from app.services.funding_cases import FundingCaseNotFoundError


class RequirementCertainty(StrEnum):
    CONFIRMED = "CONFIRMED"
    EVIDENCE_FOUND = "EVIDENCE_FOUND"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


@dataclass(frozen=True)
class RequirementSpec:
    requirement_key: str
    category: str
    certainty: RequirementCertainty
    title: str
    statement: str
    source_url: str
    evidence: list[dict[str, Any]]


_CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "DOCUMENTS": (
        "liite",
        "asiakirj",
        "dokument",
        "hakemuslomake",
        "attachment",
        "document",
    ),
    "BUDGET": (
        "budjet",
        "omarahoit",
        "omavastuu",
        "kustann",
        "rahoitusosuus",
        "budget",
        "co-financ",
        "cost",
    ),
    "APPROVALS": (
        "hyväksynt",
        "hyväksy",
        "päätös",
        "approval",
        "decision",
    ),
    "REPORTING": (
        "raport",
        "seuranta",
        "mittari",
        "kpi",
        "report",
        "monitoring",
        "indicator",
    ),
}


def _deadline_text(
    deadline_on: date | None,
    deadline_at: datetime | None,
) -> str | None:
    if deadline_at is not None:
        return (
            f"{deadline_at.day}.{deadline_at.month}.{deadline_at.year} "
            f"klo {deadline_at.hour:02d}.{deadline_at.minute:02d}"
        )
    if deadline_on is not None:
        return f"{deadline_on.day}.{deadline_on.month}.{deadline_on.year}"
    return None


def _normalized_evidence(
    evidence: list[dict[str, Any]],
    *,
    default_source_url: str,
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for item in evidence:
        text = str(item.get("text", "")).strip()
        section = str(item.get("section", "")).strip()
        source_url = str(item.get("source_url", default_source_url)).strip()
        if not text and not section:
            continue
        normalized.append(
            {
                "section": section or "Lähdeaineisto",
                "text": text[:2_000],
                "source_url": source_url or default_source_url,
            }
        )
    return normalized


def _matching_evidence(
    *,
    description_text: str | None,
    evidence: list[dict[str, Any]],
    source_url: str,
    keywords: tuple[str, ...],
) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    if description_text:
        lowered = description_text.casefold()
        if any(keyword in lowered for keyword in keywords):
            matches.append(
                {
                    "section": "Lähteen kuvaus",
                    "text": description_text.strip()[:2_000],
                    "source_url": source_url,
                }
            )

    for item in _normalized_evidence(evidence, default_source_url=source_url):
        searchable = f"{item['section']} {item['text']}".casefold()
        if any(keyword in searchable for keyword in keywords):
            matches.append(item)
    return matches[:6]


def _reviewable_requirement(
    *,
    requirement_key: str,
    category: str,
    title: str,
    evidence_title: str,
    missing_statement: str,
    description_text: str | None,
    evidence: list[dict[str, Any]],
    source_url: str,
) -> RequirementSpec:
    matches = _matching_evidence(
        description_text=description_text,
        evidence=evidence,
        source_url=source_url,
        keywords=_CATEGORY_KEYWORDS[category],
    )
    if matches:
        return RequirementSpec(
            requirement_key=requirement_key,
            category=category,
            certainty=RequirementCertainty.EVIDENCE_FOUND,
            title=title,
            statement=(
                f"Lähdeaineistossa on {evidence_title} liittyvää tietoa. "
                "Tarkista täsmällinen vaatimus ennen hyväksyntää."
            ),
            source_url=source_url,
            evidence=matches,
        )
    return RequirementSpec(
        requirement_key=requirement_key,
        category=category,
        certainty=RequirementCertainty.REVIEW_REQUIRED,
        title=title,
        statement=missing_statement,
        source_url=source_url,
        evidence=[],
    )


def derive_requirement_specs(
    *,
    source_url: str,
    relevance_status: str,
    relevance_reason: str,
    description_text: str | None,
    evidence: list[dict[str, Any]],
    application_deadline_on: date | None,
    application_deadline_at: datetime | None,
) -> list[RequirementSpec]:
    """Derive conservative structured requirements without inventing source obligations."""

    normalized = _normalized_evidence(evidence, default_source_url=source_url)
    eligibility_confirmed = relevance_status == RelevanceStatus.RELEVANT.value
    eligibility = RequirementSpec(
        requirement_key="ELIGIBILITY",
        category="ELIGIBILITY",
        certainty=(
            RequirementCertainty.CONFIRMED
            if eligibility_confirmed
            else RequirementCertainty.REVIEW_REQUIRED
        ),
        title="Hakukelpoisuus",
        statement=(
            relevance_reason
            if eligibility_confirmed
            else f"Hakukelpoisuus on tarkistettava: {relevance_reason}"
        ),
        source_url=source_url,
        evidence=(
            normalized[:6]
            if normalized
            else [
                {
                    "section": "VakeHyvä-luokittelu",
                    "text": relevance_reason,
                    "source_url": source_url,
                }
            ]
        ),
    )

    deadline_text = _deadline_text(application_deadline_on, application_deadline_at)
    deadline = RequirementSpec(
        requirement_key="APPLICATION_DEADLINE",
        category="DEADLINE",
        certainty=(
            RequirementCertainty.CONFIRMED
            if deadline_text is not None
            else RequirementCertainty.REVIEW_REQUIRED
        ),
        title="Hakemuksen määräaika",
        statement=(
            f"Lähteen ilmoittama hakuaika päättyy {deadline_text}."
            if deadline_text is not None
            else "Hakemuksen määräaikaa ei ole tallennettu rakenteisena tietona; tarkista lähde."
        ),
        source_url=source_url,
        evidence=(
            [
                {
                    "section": "Rakenteinen hakuaika",
                    "text": deadline_text,
                    "source_url": source_url,
                }
            ]
            if deadline_text is not None
            else []
        ),
    )

    return [
        eligibility,
        deadline,
        _reviewable_requirement(
            requirement_key="REQUIRED_DOCUMENTS",
            category="DOCUMENTS",
            title="Pakolliset asiakirjat ja liitteet",
            evidence_title="asiakirjoihin tai liitteisiin",
            missing_statement=(
                "Pakollisia asiakirjoja tai liitteitä ei ole tunnistettu rakenteisesti; "
                "tarkista rahoittajan lähdeaineisto."
            ),
            description_text=description_text,
            evidence=evidence,
            source_url=source_url,
        ),
        _reviewable_requirement(
            requirement_key="BUDGET_AND_COFUNDING",
            category="BUDGET",
            title="Budjetti ja omarahoitus",
            evidence_title="budjettiin, kustannuksiin tai omarahoitukseen",
            missing_statement=(
                "Budjetti-, kustannus- tai omarahoitusehtoa ei ole tunnistettu rakenteisesti; "
                "tarkista rahoittajan lähdeaineisto."
            ),
            description_text=description_text,
            evidence=evidence,
            source_url=source_url,
        ),
        _reviewable_requirement(
            requirement_key="APPROVALS_AND_DECISIONS",
            category="APPROVALS",
            title="Hyväksynnät ja päätöspisteet",
            evidence_title="hyväksyntöihin tai päätöksiin",
            missing_statement=(
                "Rahoittajan tai sisäisiä hyväksyntävaatimuksia ei päätellä ilman lähdenäyttöä; "
                "tarkista tarvittavat päätöspisteet."
            ),
            description_text=description_text,
            evidence=evidence,
            source_url=source_url,
        ),
        _reviewable_requirement(
            requirement_key="REPORTING_OBLIGATIONS",
            category="REPORTING",
            title="Raportointivelvoitteet",
            evidence_title="raportointiin, seurantaan tai mittareihin",
            missing_statement=(
                "Raportointijaksoja, mittareita tai raportointimääräaikoja ei ole tunnistettu "
                "rakenteisesti; tarkista rahoittajan lähdeaineisto."
            ),
            description_text=description_text,
            evidence=evidence,
            source_url=source_url,
        ),
    ]


def _row_response(row: FundingCaseRequirement) -> FundingCaseRequirementResponse:
    return FundingCaseRequirementResponse(
        requirement_key=row.requirement_key,
        category=row.category,
        certainty=row.certainty,
        title=row.title,
        statement=row.statement,
        source_url=row.source_url,
        evidence=list(row.evidence),
        funding_call_version=row.funding_call_version,
    )


async def sync_case_requirements(
    session: AsyncSession,
    *,
    case: FundingCase,
    record: FundingCallRecord,
    observed_at: datetime,
) -> list[FundingCaseRequirement]:
    """Upsert the deterministic requirement projection for the current source version."""

    specs = derive_requirement_specs(
        source_url=record.source_url,
        relevance_status=record.relevance_status,
        relevance_reason=record.relevance_reason,
        description_text=record.description_text,
        evidence=list(record.evidence),
        application_deadline_on=record.application_deadline_on,
        application_deadline_at=record.application_deadline_at,
    )
    result = await session.execute(
        select(FundingCaseRequirement).where(
            FundingCaseRequirement.case_id == case.id,
            FundingCaseRequirement.funding_call_version == record.current_version,
        )
    )
    existing = {row.requirement_key: row for row in result.scalars()}
    rows: list[FundingCaseRequirement] = []

    for spec in specs:
        row = existing.get(spec.requirement_key)
        if row is None:
            row = FundingCaseRequirement(
                case_id=case.id,
                funding_call_version=record.current_version,
                requirement_key=spec.requirement_key,
                category=spec.category,
                certainty=spec.certainty.value,
                title=spec.title,
                statement=spec.statement,
                source_url=spec.source_url,
                evidence=spec.evidence,
                created_at=observed_at,
                updated_at=observed_at,
            )
            session.add(row)
        else:
            row.category = spec.category
            row.certainty = spec.certainty.value
            row.title = spec.title
            row.statement = spec.statement
            row.source_url = spec.source_url
            row.evidence = spec.evidence
            row.updated_at = observed_at
        rows.append(row)

    await session.flush()
    return rows


async def list_case_requirements(
    session: AsyncSession,
    case_id: UUID,
) -> list[FundingCaseRequirementResponse]:
    case = await session.get(FundingCase, case_id)
    if case is None:
        raise FundingCaseNotFoundError(str(case_id))
    record = await session.get(FundingCallRecord, case.funding_call_id)
    if record is None:
        raise FundingCaseNotFoundError(str(case_id))

    result = await session.execute(
        select(FundingCaseRequirement).where(
            FundingCaseRequirement.case_id == case_id,
            FundingCaseRequirement.funding_call_version == record.current_version,
        )
    )
    rows = list(result.scalars())
    order = {
        "ELIGIBILITY": 0,
        "APPLICATION_DEADLINE": 1,
        "REQUIRED_DOCUMENTS": 2,
        "BUDGET_AND_COFUNDING": 3,
        "APPROVALS_AND_DECISIONS": 4,
        "REPORTING_OBLIGATIONS": 5,
    }
    rows.sort(key=lambda row: (order.get(row.requirement_key, 99), row.requirement_key))
    return [_row_response(row) for row in rows]
