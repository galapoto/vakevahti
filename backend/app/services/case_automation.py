from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.case_models import FundingCase, FundingCaseArtifact, FundingCaseTask
from app.db.models import FundingCallRecord
from app.domain.funding_call import RelevanceStatus


@dataclass(frozen=True)
class TaskSpec:
    key: str
    title: str
    detail: str
    completed: bool


def _deadline(record: FundingCallRecord) -> date | None:
    if record.application_deadline_at is not None:
        return record.application_deadline_at.date()
    return record.application_deadline_on


async def sync_case_automation_tasks(
    session: AsyncSession,
    *,
    case: FundingCase,
    record: FundingCallRecord,
    observed_at: datetime,
) -> list[FundingCaseTask]:
    """Maintain deterministic next-step tasks from case facts and approved artifacts."""

    artifact_result = await session.execute(
        select(FundingCaseArtifact).where(FundingCaseArtifact.case_id == case.id)
    )
    artifacts = list(artifact_result.scalars())
    approved_types = {
        artifact.artifact_type
        for artifact in artifacts
        if artifact.status == "APPROVED"
    }

    specs = [
        TaskSpec(
            key="ELIGIBILITY_REVIEW",
            title="Varmista hakukelpoisuus",
            detail=(
                "Tarkista, että VakeHyvä kuuluu hakukelpoisiin organisaatioihin ja että "
                "rahoitushaun rajaukset täyttyvät."
            ),
            completed=record.relevance_status == RelevanceStatus.RELEVANT.value,
        ),
        TaskSpec(
            key="PROCESS_DESCRIPTION",
            title="Valmistele prosessikuvaus",
            detail=(
                "Liitä tai hyväksy caselle prosessikuvaus, jossa näkyvät omistaja, "
                "valmisteluvaiheet, päätöspisteet ja lähetysvastuu."
            ),
            completed="PROCESS_DESCRIPTION" in approved_types,
        ),
        TaskSpec(
            key="REPORTING_PLAN",
            title="Valmistele raportointisuunnitelma",
            detail=(
                "Liitä tai hyväksy raportointisuunnitelma, jossa kuvataan seuranta, "
                "vastuut, mittarit ja rahoittajan raportointipisteet."
            ),
            completed="REPORTING" in approved_types,
        ),
        TaskSpec(
            key="FUNDING_REPORT_REVIEW",
            title="Tarkista rahoitusraportti ja sähköpostipaketti",
            detail=(
                "Tarkista automaattinen rahoitusraportti, sähköpostin vastaanottajat, "
                "aihe, viesti ja mukaan valitut case-aineistot."
            ),
            completed="FUNDING_REPORT" in approved_types,
        ),
    ]

    existing_result = await session.execute(
        select(FundingCaseTask).where(FundingCaseTask.case_id == case.id)
    )
    existing = {task.task_key: task for task in existing_result.scalars()}
    due_on = _deadline(record)
    ordered: list[FundingCaseTask] = []

    for spec in specs:
        status = "COMPLETED" if spec.completed else "OPEN"
        task = existing.get(spec.key)
        if task is None:
            task = FundingCaseTask(
                case_id=case.id,
                task_key=spec.key,
                title=spec.title,
                detail=spec.detail,
                status=status,
                due_on=due_on,
                created_at=observed_at,
                updated_at=observed_at,
                completed_at=observed_at if spec.completed else None,
            )
            session.add(task)
        else:
            prior_status = task.status
            task.title = spec.title
            task.detail = spec.detail
            task.status = status
            task.due_on = due_on
            if prior_status != status:
                task.updated_at = observed_at
                task.completed_at = observed_at if spec.completed else None
        ordered.append(task)

    await session.flush()
    return ordered


def case_next_action(tasks: list[FundingCaseTask]) -> str:
    """Return the first unresolved automated step in business priority order."""

    for task in tasks:
        if task.status == "OPEN":
            return task.title
    return "Caseen liittyvät automaattiset valmisteluvaiheet ovat valmiit."
