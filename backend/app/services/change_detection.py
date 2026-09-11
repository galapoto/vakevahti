import hashlib
import json
from typing import Any

from app.domain.funding_call import FundingCallCandidate

_LEGACY_MATERIAL_FIELDS = (
    "title",
    "source_url",
    "application_opens_at",
    "application_deadline_at",
    "description_text",
    "relevance_status",
    "relevance_reason",
    "evidence",
)

_MATERIAL_FIELDS = (
    "title",
    "source_url",
    "application_opens_on",
    "application_opens_at",
    "application_deadline_on",
    "application_deadline_at",
    "description_text",
    "relevance_status",
    "relevance_reason",
    "evidence",
)


def _snapshot_payload(candidate: FundingCallCandidate) -> dict[str, Any]:
    payload = candidate.model_dump(mode="json")
    if payload["application_opens_on"] is None and candidate.application_opens_at:
        payload["application_opens_on"] = candidate.application_opens_at.date().isoformat()
    if payload["application_deadline_on"] is None and candidate.application_deadline_at:
        payload["application_deadline_on"] = (
            candidate.application_deadline_at.date().isoformat()
        )
    return payload


def candidate_snapshot(candidate: FundingCallCandidate) -> dict[str, Any]:
    """Return the current canonical material state used for new history versions."""

    payload = _snapshot_payload(candidate)
    return {field: payload[field] for field in _MATERIAL_FIELDS}


def _legacy_candidate_snapshot(candidate: FundingCallCandidate) -> dict[str, Any]:
    """Reproduce the pre-date-precision hash contract for migration-safe comparison."""

    payload = _snapshot_payload(candidate)
    return {field: payload[field] for field in _LEGACY_MATERIAL_FIELDS}


def _hash_snapshot(snapshot: dict[str, Any]) -> str:
    canonical_json = json.dumps(
        snapshot,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def candidate_content_hash(candidate: FundingCallCandidate) -> str:
    """Hash the current material contract deterministically."""

    return _hash_snapshot(candidate_snapshot(candidate))


def legacy_candidate_content_hash(candidate: FundingCallCandidate) -> str:
    """Hash using the pre-2026-09-07 material contract for compatibility only."""

    return _hash_snapshot(_legacy_candidate_snapshot(candidate))
