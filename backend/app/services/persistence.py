from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import FundingCallRecord, FundingCallVersion, SourceState
from app.domain.funding_call import FundingCallCandidate
from app.services.change_detection import candidate_content_hash, candidate_snapshot


class ChangeStatus(StrEnum):
    NEW = "NEW"
    UNCHANGED = "UNCHANGED"
    CHANGED = "CHANGED"


@dataclass(frozen=True)
class PersistOutcome:
    external_key: str
    status: ChangeStatus
    notification_eligible: bool


@dataclass(frozen=True)
class PersistBatchResult:
    source_code: str
    baseline: bool
    outcomes: tuple[PersistOutcome, ...]

    @property
    def new_count(self) -> int:
        return sum(outcome.status is ChangeStatus.NEW for outcome in self.outcomes)

    @property
    def unchanged_count(self) -> int:
        return sum(outcome.status is ChangeStatus.UNCHANGED for outcome in self.outcomes)

    @property
    def changed_count(self) -> int:
        return sum(outcome.status is ChangeStatus.CHANGED for outcome in self.outcomes)


def _resolve_source_code(
    candidates: Sequence[FundingCallCandidate],
    source_code: str | None,
) -> str:
    """Resolve one source code, including a legitimate empty source snapshot."""

    candidate_sources = {candidate.source_code for candidate in candidates}
    if len(candidate_sources) > 1:
        raise ValueError("A persistence batch must contain calls from exactly one source.")

    normalized_explicit = source_code.strip().upper() if source_code else None
    if normalized_explicit:
        if candidate_sources and candidate_sources != {normalized_explicit}:
            raise ValueError(
                "Explicit source_code does not match the candidates in the persistence batch."
            )
        return normalized_explicit

    if not candidate_sources:
        raise ValueError(
            "source_code is required when persisting a successful empty source snapshot."
        )

    return next(iter(candidate_sources))


async def _serialize_source_transaction(session: AsyncSession, source_code: str) -> None:
    """Serialize persistence for one source inside the current PostgreSQL transaction.

    The transaction-scoped advisory lock closes the race where two first-time scans
    could both observe a missing SourceState and attempt to create the same source row.
    It also keeps version calculations deterministic when manual and scheduled runs overlap.
    """

    await session.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:source_code, 0))"),
        {"source_code": source_code},
    )


def _apply_candidate(record: FundingCallRecord, candidate: FundingCallCandidate) -> None:
    record.title = candidate.title
    record.source_url = str(candidate.source_url)
    record.application_opens_at = candidate.application_opens_at
    record.application_deadline_at = candidate.application_deadline_at
    record.description_text = candidate.description_text
    record.relevance_status = candidate.relevance_status.value
    record.relevance_reason = candidate.relevance_reason
    record.evidence = [evidence.model_dump(mode="json") for evidence in candidate.evidence]


async def persist_candidates(
    session: AsyncSession,
    candidates: Sequence[FundingCallCandidate],
    *,
    source_code: str | None = None,
    observed_at: datetime | None = None,
) -> PersistBatchResult:
    """Persist one authoritative successful source snapshot without committing.

    Current membership is represented by a snapshot watermark rather than deleting
    disappeared records. Every candidate observed in this successful scan gets the
    same ``last_seen_at`` value, and ``SourceState.last_successful_scan_at`` advances
    to that value in the same transaction. A record is therefore current exactly
    when its ``last_seen_at`` equals its source's latest successful snapshot time.

    ``source_code`` is required only when a legitimate successful scan contains zero
    candidates, because there is then no candidate from which to infer the source.
    """

    resolved_source = _resolve_source_code(candidates, source_code)
    observed_at = observed_at or datetime.now(UTC)

    await _serialize_source_transaction(session, resolved_source)

    state = await session.get(SourceState, resolved_source, with_for_update=True)
    baseline = state is None or state.baseline_completed_at is None
    previous_snapshot_at = state.last_successful_scan_at if state else None

    if state is None:
        state = SourceState(source_code=resolved_source)
        session.add(state)
        await session.flush()

    outcomes: list[PersistOutcome] = []

    for candidate in candidates:
        content_hash = candidate_content_hash(candidate)
        statement = (
            select(FundingCallRecord)
            .where(
                FundingCallRecord.source_code == candidate.source_code,
                FundingCallRecord.external_key == candidate.external_key,
            )
            .with_for_update()
        )
        record = (await session.execute(statement)).scalar_one_or_none()

        if record is None:
            record = FundingCallRecord(
                source_code=candidate.source_code,
                external_key=candidate.external_key,
                title=candidate.title,
                source_url=str(candidate.source_url),
                application_opens_at=candidate.application_opens_at,
                application_deadline_at=candidate.application_deadline_at,
                description_text=candidate.description_text,
                relevance_status=candidate.relevance_status.value,
                relevance_reason=candidate.relevance_reason,
                evidence=[
                    evidence.model_dump(mode="json") for evidence in candidate.evidence
                ],
                content_hash=content_hash,
                current_version=1,
                first_seen_at=observed_at,
                last_seen_at=observed_at,
            )
            session.add(record)
            await session.flush()

            session.add(
                FundingCallVersion(
                    funding_call_id=record.id,
                    version_number=1,
                    content_hash=content_hash,
                    snapshot=candidate_snapshot(candidate),
                    observed_at=observed_at,
                )
            )
            status = ChangeStatus.NEW

        else:
            was_current = (
                previous_snapshot_at is not None
                and record.last_seen_at == previous_snapshot_at
            )
            content_changed = record.content_hash != content_hash

            if content_changed:
                record.current_version += 1
                _apply_candidate(record, candidate)
                record.content_hash = content_hash
                session.add(
                    FundingCallVersion(
                        funding_call_id=record.id,
                        version_number=record.current_version,
                        content_hash=content_hash,
                        snapshot=candidate_snapshot(candidate),
                        observed_at=observed_at,
                    )
                )

            record.last_seen_at = observed_at

            if not was_current:
                # Reappearance after absence is NEW relative to the previous current
                # source snapshot, even though historical identity is preserved.
                status = ChangeStatus.NEW
            elif content_changed:
                status = ChangeStatus.CHANGED
            else:
                status = ChangeStatus.UNCHANGED

        outcomes.append(
            PersistOutcome(
                external_key=candidate.external_key,
                status=status,
                notification_eligible=not baseline
                and status in {ChangeStatus.NEW, ChangeStatus.CHANGED},
            )
        )

    state.last_successful_scan_at = observed_at
    if baseline:
        state.baseline_completed_at = observed_at

    await session.flush()

    return PersistBatchResult(
        source_code=resolved_source,
        baseline=baseline,
        outcomes=tuple(outcomes),
    )
