from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import select
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


def _validate_batch(candidates: Sequence[FundingCallCandidate]) -> str:
    if not candidates:
        raise ValueError("Persistence batch must contain at least one funding call.")

    source_codes = {candidate.source_code for candidate in candidates}
    if len(source_codes) != 1:
        raise ValueError("A persistence batch must contain calls from exactly one source.")

    return next(iter(source_codes))


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
    observed_at: datetime | None = None,
) -> PersistBatchResult:
    """Persist one successful source scan without committing the caller's transaction."""

    source_code = _validate_batch(candidates)
    observed_at = observed_at or datetime.now(UTC)

    state = await session.get(SourceState, source_code, with_for_update=True)
    baseline = state is None or state.baseline_completed_at is None

    if state is None:
        state = SourceState(source_code=source_code)
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

        elif record.content_hash == content_hash:
            record.last_seen_at = observed_at
            status = ChangeStatus.UNCHANGED

        else:
            record.current_version += 1
            _apply_candidate(record, candidate)
            record.content_hash = content_hash
            record.last_seen_at = observed_at

            session.add(
                FundingCallVersion(
                    funding_call_id=record.id,
                    version_number=record.current_version,
                    content_hash=content_hash,
                    snapshot=candidate_snapshot(candidate),
                    observed_at=observed_at,
                )
            )
            status = ChangeStatus.CHANGED

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
        source_code=source_code,
        baseline=baseline,
        outcomes=tuple(outcomes),
    )
