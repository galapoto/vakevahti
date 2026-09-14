from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.api.case_schemas import FundingCaseArtifactResponse
from app.services.funding_cases import _preferred_artifacts


def _artifact(
    *,
    source_app: str,
    artifact_type: str,
    external_id: str,
    status: str = "DRAFT",
    version: int = 1,
) -> FundingCaseArtifactResponse:
    now = datetime(2026, 9, 14, 10, 0, tzinfo=UTC)
    return FundingCaseArtifactResponse(
        id=uuid4(),
        case_id=uuid4(),
        source_app=source_app,
        artifact_type=artifact_type,
        external_artifact_id=external_id,
        version=version,
        status=status,
        title=external_id,
        summary=None,
        content_url=None,
        content_text=None,
        mime_type="text/plain",
        checksum=None,
        metadata={},
        created_at=now,
        updated_at=now,
        approved_at=now if status == "APPROVED" else None,
    )


def _ids(artifacts: list[FundingCaseArtifactResponse]) -> set[UUID]:
    return {artifact.id for artifact in artifacts}


def test_automatic_process_and_reporting_drafts_are_default_fallbacks() -> None:
    process = _artifact(
        source_app="VAKEVAHTI_AUTOMATION",
        artifact_type="PROCESS_DESCRIPTION",
        external_id="automatic-process-description",
    )
    reporting = _artifact(
        source_app="VAKEVAHTI_AUTOMATION",
        artifact_type="REPORTING",
        external_id="automatic-reporting-plan",
    )

    selected = _preferred_artifacts([process, reporting])

    assert _ids(selected) == {process.id, reporting.id}


def test_real_artifact_replaces_automatic_fallback_of_same_type() -> None:
    automatic_process = _artifact(
        source_app="VAKEVAHTI_AUTOMATION",
        artifact_type="PROCESS_DESCRIPTION",
        external_id="automatic-process-description",
    )
    automatic_reporting = _artifact(
        source_app="VAKEVAHTI_AUTOMATION",
        artifact_type="REPORTING",
        external_id="automatic-reporting-plan",
    )
    approved_process = _artifact(
        source_app="PROSESSIKUVAUS",
        artifact_type="PROCESS_DESCRIPTION",
        external_id="process-42",
        status="APPROVED",
        version=2,
    )

    selected = _preferred_artifacts(
        [automatic_process, automatic_reporting, approved_process]
    )

    assert _ids(selected) == {approved_process.id, automatic_reporting.id}


def test_explicit_artifact_selection_is_not_rewritten_by_fallback_policy() -> None:
    automatic_process = _artifact(
        source_app="VAKEVAHTI_AUTOMATION",
        artifact_type="PROCESS_DESCRIPTION",
        external_id="automatic-process-description",
    )
    approved_process = _artifact(
        source_app="PROSESSIKUVAUS",
        artifact_type="PROCESS_DESCRIPTION",
        external_id="process-42",
        status="APPROVED",
    )

    selected = _preferred_artifacts(
        [automatic_process, approved_process],
        [automatic_process.id, approved_process.id],
    )

    assert _ids(selected) == {automatic_process.id, approved_process.id}
