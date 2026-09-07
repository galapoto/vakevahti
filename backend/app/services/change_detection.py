import hashlib
import json
from typing import Any

from app.domain.funding_call import FundingCallCandidate

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


def candidate_snapshot(candidate: FundingCallCandidate) -> dict[str, Any]:
    """Return the canonical material state used for history and change detection.

    Exact timestamps carry their source-local calendar date implicitly. Store that date
    explicitly in new snapshots too so API/storage semantics remain consistent even when
    a scanner only supplied ``*_at`` for older all-relevant source adapters.
    """

    payload = candidate.model_dump(mode="json")
    if payload["application_opens_on"] is None and candidate.application_opens_at:
        payload["application_opens_on"] = candidate.application_opens_at.date().isoformat()
    if payload["application_deadline_on"] is None and candidate.application_deadline_at:
        payload["application_deadline_on"] = (
            candidate.application_deadline_at.date().isoformat()
        )
    return {field: payload[field] for field in _MATERIAL_FIELDS}


def candidate_content_hash(candidate: FundingCallCandidate) -> str:
    """Hash material fields deterministically so unchanged input stays unchanged."""

    canonical_json = json.dumps(
        candidate_snapshot(candidate),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
