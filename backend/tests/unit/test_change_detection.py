from pydantic import HttpUrl

from app.domain.funding_call import FundingCallCandidate, RelevanceStatus
from app.services.change_detection import candidate_content_hash


def make_candidate(
    *,
    external_key: str = "stable-key",
    title: str = "Test funding call",
    description_text: str | None = None,
) -> FundingCallCandidate:
    return FundingCallCandidate(
        external_key=external_key,
        source_code="STM",
        title=title,
        source_url=HttpUrl("https://example.test/call"),
        description_text=description_text,
        relevance_status=RelevanceStatus.RELEVANT,
        relevance_reason="STM business rule",
    )


def test_content_hash_is_deterministic() -> None:
    candidate = make_candidate(description_text="Same material content")

    assert candidate_content_hash(candidate) == candidate_content_hash(candidate)


def test_content_hash_changes_when_material_content_changes() -> None:
    before = make_candidate(description_text="Original")
    after = make_candidate(description_text="Changed")

    assert candidate_content_hash(before) != candidate_content_hash(after)


def test_external_identity_is_not_part_of_content_hash() -> None:
    first = make_candidate(external_key="source-id-1")
    second = make_candidate(external_key="source-id-2")

    assert candidate_content_hash(first) == candidate_content_hash(second)
