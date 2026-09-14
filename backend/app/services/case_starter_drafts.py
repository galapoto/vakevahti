import json
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.case_models import FundingCase, FundingCaseArtifact
from app.db.models import FundingCallRecord
from app.domain.funding_call import RelevanceStatus

_AUTOMATION_SOURCE = "VAKEVAHTI_AUTOMATION"


@dataclass(frozen=True)
class StarterDraft:
    artifact_type: str
    external_artifact_id: str
    title: str
    summary: str
    content_text: str


def _deadline_text(record: FundingCallRecord) -> str:
    if record.application_deadline_at is not None:
        value = record.application_deadline_at
        return f"{value.day}.{value.month}.{value.year} klo {value.hour:02d}.{value.minute:02d}"
    if record.application_deadline_on is not None:
        value = record.application_deadline_on
        return f"{value.day}.{value.month}.{value.year}"
    return "Tarkistettava"


def _evidence_lines(record: FundingCallRecord) -> list[str]:
    lines: list[str] = []
    for item in record.evidence[:8]:
        readable = "; ".join(
            f"{key}: {json.dumps(value, ensure_ascii=False, default=str)}"
            for key, value in sorted(item.items())
        )
        if readable:
            lines.append(f"- {readable[:900]}")
    return lines or ["- Tarkistettava lähdeaineistosta"]


def _known_context(record: FundingCallRecord) -> str:
    description = record.description_text.strip() if record.description_text else "Tarkistettava"
    evidence = "\n".join(_evidence_lines(record))
    eligibility = (
        "VakeHyvälle relevantiksi vahvistettu nykyisillä säännöillä"
        if record.relevance_status == RelevanceStatus.RELEVANT.value
        else "Tarkistettava ennen valmistelun jatkamista"
    )
    return (
        f"Rahoitushaku: {record.title}\n"
        f"Lähde: {record.source_code}\n"
        f"Lähdeosoite: {record.source_url}\n"
        f"Hakuaika päättyy: {_deadline_text(record)}\n"
        f"Hakukelpoisuus: {eligibility}\n"
        f"Miksi VakeHyvälle: {record.relevance_reason}\n\n"
        f"Lähteen kuvaus:\n{description[:5000]}\n\n"
        f"Lähteestä tallennettu näyttö:\n{evidence}"
    )


def _process_draft(record: FundingCallRecord) -> StarterDraft:
    known = _known_context(record)
    body = (
        "AUTOMAATTINEN LUONNOS · tarkista ennen hyväksyntää\n\n"
        f"{known}\n\n"
        "Prosessin omistaja: Tarkistettava\n"
        "Hakemuksen valmisteluvastuu: Tarkistettava\n"
        "Budjetin/talouden valmistelu: Tarkistettava\n"
        "Pakolliset liitteet: Tarkistettava lähdeaineistosta\n"
        "Sisäinen päätöspiste: Tarkistettava\n"
        "Hakemuksen lähetysvastuu: Tarkistettava\n\n"
        "Ehdotettu prosessirunko:\n"
        "1. Varmista hakukelpoisuus ja haun rajaukset.\n"
        "2. Nimeä omistaja ja valmisteluvastuut.\n"
        "3. Tarkista rahoittajan vaatimat asiakirjat ja budjettiehdot.\n"
        "4. Valmistele sisältö, talous ja tarvittavat hyväksynnät.\n"
        "5. Tee sisäinen hyväksyntä ennen lähettämistä.\n"
        "6. Lähetä hakemus ja tallenna lähetyksen todiste samaan caseen.\n"
    )
    return StarterDraft(
        artifact_type="PROCESS_DESCRIPTION",
        external_artifact_id="automatic-process-description",
        title="Automaattinen prosessikuvausluonnos",
        summary=(
            "VakeVahti muodosti rahoitushaun tunnetuista tiedoista prosessikuvauksen "
            "aloitusluonnoksen. Tuntemattomat kohdat on merkitty Tarkistettava."
        ),
        content_text=body,
    )


def _reporting_draft(record: FundingCallRecord) -> StarterDraft:
    known = _known_context(record)
    body = (
        "AUTOMAATTINEN LUONNOS · tarkista ennen hyväksyntää\n\n"
        f"{known}\n\n"
        "Raportoinnin vastuuhenkilö: Tarkistettava\n"
        "Rahoittajan raportointijaksot: Tarkistettava lähdeaineistosta\n"
        "Pakolliset KPI:t/mittarit: Tarkistettava lähdeaineistosta\n"
        "Talousseurannan vaatimukset: Tarkistettava lähdeaineistosta\n"
        "Väliraportin määräpäivä: Tarkistettava\n"
        "Loppuraportin määräpäivä: Tarkistettava\n"
        "Säilytettävät tositteet/liitteet: Tarkistettava\n\n"
        "Ehdotettu raportointirunko:\n"
        "1. Tavoite ja rahoitettu toiminta.\n"
        "2. Sovitut tulos- ja vaikutusmittarit.\n"
        "3. Toteuma suhteessa tavoitteisiin.\n"
        "4. Talouden toteuma ja poikkeamat.\n"
        "5. Riskit, muutokset ja korjaavat toimet.\n"
        "6. Rahoittajalle toimitettavat raportit ja liitteet.\n"
    )
    return StarterDraft(
        artifact_type="REPORTING",
        external_artifact_id="automatic-reporting-plan",
        title="Automaattinen raportointisuunnitelmaluonnos",
        summary=(
            "VakeVahti muodosti tunnetuista rahoitustiedoista raportoinnin aloitusluonnoksen. "
            "Rahoittajakohtaiset tuntemattomat vaatimukset on merkitty Tarkistettava."
        ),
        content_text=body,
    )


def _checksum(draft: StarterDraft) -> str:
    material = "\x1f".join([draft.title, draft.summary, draft.content_text])
    return sha256(material.encode()).hexdigest()


async def ensure_case_starter_drafts(
    session: AsyncSession,
    *,
    case: FundingCase,
    record: FundingCallRecord,
    observed_at: datetime,
) -> int:
    """Create idempotent editable starter drafts for the current funding-call version."""

    drafts = (_process_draft(record), _reporting_draft(record))
    created = 0
    for draft in drafts:
        existing = await session.scalar(
            select(FundingCaseArtifact).where(
                FundingCaseArtifact.case_id == case.id,
                FundingCaseArtifact.source_app == _AUTOMATION_SOURCE,
                FundingCaseArtifact.artifact_type == draft.artifact_type,
                FundingCaseArtifact.external_artifact_id == draft.external_artifact_id,
                FundingCaseArtifact.version == record.current_version,
            )
        )
        if existing is not None:
            continue

        session.add(
            FundingCaseArtifact(
                id=uuid4(),
                case_id=case.id,
                source_app=_AUTOMATION_SOURCE,
                artifact_type=draft.artifact_type,
                external_artifact_id=draft.external_artifact_id,
                version=record.current_version,
                status="DRAFT",
                title=draft.title,
                summary=draft.summary,
                content_url=None,
                content_text=draft.content_text,
                mime_type="text/plain",
                checksum=_checksum(draft),
                artifact_metadata={
                    "generated_by": "VakeVahti",
                    "funding_call_version": record.current_version,
                    "source_code": record.source_code,
                    "requires_review": True,
                },
                created_at=observed_at,
                updated_at=observed_at,
                approved_at=None,
            )
        )
        created += 1

    if created:
        case.updated_at = observed_at
        await session.flush()
    return created
