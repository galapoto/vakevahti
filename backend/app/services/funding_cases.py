import json
from datetime import UTC, datetime
from hashlib import md5, sha256
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.case_schemas import (
    FundingCaseArtifactCreate,
    FundingCaseArtifactResponse,
    FundingCaseCallSummary,
    FundingCaseEmailPackage,
    FundingCaseEmailQueueResponse,
    FundingCaseEmailSendRequest,
    FundingCaseResponse,
    FundingCaseTaskResponse,
)
from app.api.report_schemas import FundingReportDraftCreate
from app.db.case_models import FundingCase, FundingCaseArtifact, FundingCaseTask
from app.db.models import FundingCallRecord
from app.domain.funding_call import RelevanceStatus
from app.services.case_automation import case_next_action
from app.services.funding_reports import create_funding_report
from app.services.report_email_delivery import enqueue_report_email


class FundingCaseNotFoundError(LookupError):
    pass


class FundingCaseArtifactConflictError(RuntimeError):
    pass


class FundingCaseArtifactSelectionError(ValueError):
    def __init__(self, missing_ids: list[UUID]) -> None:
        self.missing_ids = missing_ids
        super().__init__(f"Artifacts are not attached to this funding case: {missing_ids}")


def stable_case_id(source_code: str, external_key: str) -> UUID:
    """Return the same cross-app case ID for the same upstream opportunity identity."""

    material = f"vakevahti-case:{source_code}:{external_key}".encode()
    digest = md5(material, usedforsecurity=False).hexdigest()
    return UUID(hex=digest)


async def ensure_funding_case(
    session: AsyncSession,
    record: FundingCallRecord,
    *,
    observed_at: datetime,
) -> FundingCase | None:
    """Synchronize one opportunity with its stable cross-app funding case."""

    result = await session.execute(
        select(FundingCase).where(FundingCase.funding_call_id == record.id)
    )
    existing = result.scalar_one_or_none()

    if record.relevance_status == RelevanceStatus.NOT_RELEVANT.value:
        if existing is not None:
            existing.status = "NOT_RELEVANT"
            existing.updated_at = observed_at
        return None

    if existing is not None:
        existing.status = "OPEN"
        existing.updated_at = observed_at
        return existing

    case = FundingCase(
        id=stable_case_id(record.source_code, record.external_key),
        funding_call_id=record.id,
        status="OPEN",
        created_at=observed_at,
        updated_at=observed_at,
    )
    session.add(case)
    await session.flush()
    return case


def _artifact_response(row: FundingCaseArtifact) -> FundingCaseArtifactResponse:
    return FundingCaseArtifactResponse(
        id=row.id,
        case_id=row.case_id,
        source_app=row.source_app,
        artifact_type=row.artifact_type,
        external_artifact_id=row.external_artifact_id,
        version=row.version,
        status=row.status,
        title=row.title,
        summary=row.summary,
        content_url=row.content_url,
        content_text=row.content_text,
        mime_type=row.mime_type,
        checksum=row.checksum,
        metadata=dict(row.artifact_metadata),
        created_at=row.created_at,
        updated_at=row.updated_at,
        approved_at=row.approved_at,
    )


def _task_response(row: FundingCaseTask) -> FundingCaseTaskResponse:
    return FundingCaseTaskResponse(
        id=row.id,
        task_key=row.task_key,
        title=row.title,
        detail=row.detail,
        status=row.status,
        due_on=row.due_on,
        created_at=row.created_at,
        updated_at=row.updated_at,
        completed_at=row.completed_at,
    )


def _call_summary(record: FundingCallRecord) -> FundingCaseCallSummary:
    return FundingCaseCallSummary(
        id=record.id,
        source_code=record.source_code,
        title=record.title,
        source_url=record.source_url,
        application_deadline_on=record.application_deadline_on,
        application_deadline_at=record.application_deadline_at,
        relevance_status=record.relevance_status,
        relevance_reason=record.relevance_reason,
        current_version=record.current_version,
    )


async def _case_response(
    session: AsyncSession,
    case: FundingCase,
) -> FundingCaseResponse:
    record = await session.get(FundingCallRecord, case.funding_call_id)
    if record is None:
        raise FundingCaseNotFoundError(str(case.id))
    artifact_result = await session.execute(
        select(FundingCaseArtifact)
        .where(FundingCaseArtifact.case_id == case.id)
        .order_by(
            FundingCaseArtifact.artifact_type.asc(),
            FundingCaseArtifact.source_app.asc(),
            FundingCaseArtifact.external_artifact_id.asc(),
            FundingCaseArtifact.version.desc(),
        )
    )
    artifacts = [_artifact_response(row) for row in artifact_result.scalars()]
    task_result = await session.execute(
        select(FundingCaseTask)
        .where(FundingCaseTask.case_id == case.id)
        .order_by(FundingCaseTask.id.asc())
    )
    task_rows = list(task_result.scalars())
    return FundingCaseResponse(
        id=case.id,
        status=case.status,
        created_at=case.created_at,
        updated_at=case.updated_at,
        funding_call=_call_summary(record),
        artifacts=artifacts,
        tasks=[_task_response(row) for row in task_rows],
        next_action=case_next_action(task_rows),
    )


async def list_funding_cases(session: AsyncSession) -> list[FundingCaseResponse]:
    result = await session.execute(
        select(FundingCase)
        .where(FundingCase.status == "OPEN")
        .order_by(FundingCase.updated_at.desc(), FundingCase.id.asc())
    )
    return [await _case_response(session, case) for case in result.scalars()]


async def get_funding_case(
    session: AsyncSession,
    case_id: UUID,
) -> FundingCaseResponse:
    case = await session.get(FundingCase, case_id)
    if case is None:
        raise FundingCaseNotFoundError(str(case_id))
    return await _case_response(session, case)


def _normalized_artifact_content(draft: FundingCaseArtifactCreate) -> str:
    metadata = json.dumps(
        draft.metadata,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )
    return "\x1f".join(
        [
            draft.title.strip(),
            draft.summary.strip() if draft.summary else "",
            draft.content_url.strip() if draft.content_url else "",
            draft.content_text.strip() if draft.content_text else "",
            draft.mime_type.strip() if draft.mime_type else "",
            metadata,
        ]
    )


def _artifact_checksum(draft: FundingCaseArtifactCreate) -> str:
    if draft.checksum:
        return draft.checksum.lower()
    return sha256(_normalized_artifact_content(draft).encode()).hexdigest()


async def register_case_artifact(
    session: AsyncSession,
    case_id: UUID,
    draft: FundingCaseArtifactCreate,
) -> FundingCaseArtifactResponse:
    """Register immutable artifact content while allowing idempotent status promotion."""

    case = await session.get(FundingCase, case_id)
    if case is None:
        raise FundingCaseNotFoundError(str(case_id))

    statement = select(FundingCaseArtifact).where(
        FundingCaseArtifact.case_id == case_id,
        FundingCaseArtifact.source_app == draft.source_app,
        FundingCaseArtifact.artifact_type == draft.artifact_type,
        FundingCaseArtifact.external_artifact_id == draft.external_artifact_id,
        FundingCaseArtifact.version == draft.version,
    )
    existing = (await session.scalars(statement)).one_or_none()
    checksum = _artifact_checksum(draft)
    now = datetime.now(UTC)

    if existing is not None:
        if existing.checksum != checksum:
            raise FundingCaseArtifactConflictError(
                "The same artifact version is already registered with different content."
            )
        if existing.status != draft.status or draft.approved_at is not None:
            existing.status = draft.status
            existing.updated_at = now
            existing.approved_at = (
                draft.approved_at
                or existing.approved_at
                or (now if draft.status == "APPROVED" else None)
            )
            if draft.status != "APPROVED" and draft.approved_at is None:
                existing.approved_at = None
            case.updated_at = now
            await session.commit()
        return _artifact_response(existing)

    artifact = FundingCaseArtifact(
        id=uuid4(),
        case_id=case_id,
        source_app=draft.source_app,
        artifact_type=draft.artifact_type,
        external_artifact_id=draft.external_artifact_id,
        version=draft.version,
        status=draft.status,
        title=draft.title.strip(),
        summary=draft.summary.strip() if draft.summary and draft.summary.strip() else None,
        content_url=(
            draft.content_url.strip()
            if draft.content_url and draft.content_url.strip()
            else None
        ),
        content_text=(
            draft.content_text.strip()
            if draft.content_text and draft.content_text.strip()
            else None
        ),
        mime_type=draft.mime_type.strip() if draft.mime_type else None,
        checksum=checksum,
        artifact_metadata=dict(draft.metadata),
        created_at=now,
        updated_at=now,
        approved_at=draft.approved_at or (now if draft.status == "APPROVED" else None),
    )
    session.add(artifact)
    case.updated_at = now
    await session.commit()
    return _artifact_response(artifact)


def _preferred_artifacts(
    artifacts: list[FundingCaseArtifactResponse],
    artifact_ids: list[UUID] | None = None,
) -> list[FundingCaseArtifactResponse]:
    if artifact_ids is not None:
        requested = set(artifact_ids)
        requested_artifacts = [
            artifact for artifact in artifacts if artifact.id in requested
        ]
        found = {artifact.id for artifact in requested_artifacts}
        missing = sorted(requested - found, key=str)
        if missing:
            raise FundingCaseArtifactSelectionError(missing)
        return requested_artifacts

    grouped: dict[tuple[str, str, str], list[FundingCaseArtifactResponse]] = {}
    for artifact in artifacts:
        key = (artifact.source_app, artifact.artifact_type, artifact.external_artifact_id)
        grouped.setdefault(key, []).append(artifact)

    preferred: list[FundingCaseArtifactResponse] = []
    for versions in grouped.values():
        approved = [artifact for artifact in versions if artifact.status == "APPROVED"]
        pool = approved or versions
        preferred.append(max(pool, key=lambda artifact: artifact.version))
    return sorted(preferred, key=lambda artifact: (artifact.artifact_type, artifact.title))


def _deadline_text(case: FundingCaseResponse) -> str:
    call = case.funding_call
    if call.application_deadline_at is not None:
        exact_deadline = call.application_deadline_at
        return (
            f"{exact_deadline.day}.{exact_deadline.month}.{exact_deadline.year} "
            f"klo {exact_deadline.hour:02d}.{exact_deadline.minute:02d}"
        )
    if call.application_deadline_on is not None:
        deadline_date = call.application_deadline_on
        return f"{deadline_date.day}.{deadline_date.month}.{deadline_date.year}"
    return "Ei ilmoitettu"


def compose_case_email_package(
    case: FundingCaseResponse,
    *,
    artifact_ids: list[UUID] | None = None,
) -> FundingCaseEmailPackage:
    """Compose one editable email package from the funding case and linked artifacts."""

    selected = _preferred_artifacts(case.artifacts, artifact_ids)
    call = case.funding_call
    lines = [
        "VakeHyvän rahoituscase",
        "",
        call.title,
        f"Lähde: {call.source_code}",
        f"Hakuaika päättyy: {_deadline_text(case)}",
        f"Miksi VakeHyvälle: {call.relevance_reason}",
        f"Rahoitushaku: {call.source_url}",
        "",
    ]

    labels = {
        "PROCESS_DESCRIPTION": "Prosessikuvaus",
        "REPORTING": "Raportointi",
        "FUNDING_REPORT": "Rahoitusraportti",
        "ATTACHMENT": "Liite",
    }
    for artifact in selected:
        label = labels.get(
            artifact.artifact_type,
            artifact.artifact_type.replace("_", " ").title(),
        )
        lines.extend(
            [
                label,
                f"{artifact.title} · versio {artifact.version} · {artifact.status}",
            ]
        )
        if artifact.summary:
            lines.append(artifact.summary)
        if artifact.content_text:
            lines.append(artifact.content_text[:5_000])
        if artifact.content_url:
            lines.append(f"Avaa: {artifact.content_url}")
        lines.append("")

    lines.extend(
        [
            "Case-tunnus",
            str(case.id),
            "",
            "Koonti on muodostettu VakeTomatti-kokonaisuuden samaan rahoituscaseen "
            "liitetyistä tiedoista.",
        ]
    )
    body = "\n".join(lines)[:50_000]
    return FundingCaseEmailPackage(
        case_id=case.id,
        subject=f"VakeHyvä: {call.title}"[:500],
        body=body,
        included_artifacts=selected,
    )


async def get_case_email_package(
    session: AsyncSession,
    case_id: UUID,
    *,
    artifact_ids: list[UUID] | None = None,
) -> FundingCaseEmailPackage:
    case = await get_funding_case(session, case_id)
    return compose_case_email_package(case, artifact_ids=artifact_ids)


async def queue_case_email(
    session: AsyncSession,
    case_id: UUID,
    request: FundingCaseEmailSendRequest,
) -> FundingCaseEmailQueueResponse:
    """Snapshot and queue an editable case package through durable report delivery."""

    case = await get_funding_case(session, case_id)
    package = compose_case_email_package(case, artifact_ids=request.artifact_ids)
    subject = (
        request.subject.strip()
        if request.subject and request.subject.strip()
        else package.subject
    )
    body = request.body.strip() if request.body and request.body.strip() else package.body
    report = await create_funding_report(
        session,
        FundingReportDraftCreate(
            title=f"VakeHyvän rahoituscase · {case.funding_call.title}"[:200],
            notes=f"Case {case.id} · koottu VakeTomatti-artefakteista.",
            email_subject=subject,
            email_body=body,
            recipient_emails=request.recipient_emails,
            funding_call_ids=[case.funding_call.id],
        ),
        case_id=case.id,
        included_artifact_ids=tuple(
            artifact.id for artifact in package.included_artifacts
        ),
    )
    delivery = await enqueue_report_email(session, report)
    if delivery is None:
        raise RuntimeError(
            "Case email was not queueable despite validated recipients and content."
        )
    await session.commit()
    return FundingCaseEmailQueueResponse(
        case_id=case.id,
        report_id=report.id,
        delivery_id=delivery.id,
        delivery_status=delivery.status,
        recipients=list(delivery.recipient_emails),
    )
