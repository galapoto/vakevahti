from app.domain.funding_call import RelevanceStatus
from app.services.notification_outbox import FundingNotificationEvent, notification_event_type


def test_notification_policy_suppresses_baseline_and_excluded_calls() -> None:
    assert (
        notification_event_type(
            baseline=True,
            change_status="NEW",
            relevance_status=RelevanceStatus.RELEVANT,
        )
        is None
    )
    assert (
        notification_event_type(
            baseline=False,
            change_status="NEW",
            relevance_status=RelevanceStatus.NOT_RELEVANT,
        )
        is None
    )


def test_notification_policy_maps_visible_funding_events() -> None:
    assert notification_event_type(
        baseline=False,
        change_status="NEW",
        relevance_status=RelevanceStatus.RELEVANT,
    ) is FundingNotificationEvent.DISCOVERED
    assert notification_event_type(
        baseline=False,
        change_status="NEW",
        relevance_status=RelevanceStatus.NEEDS_REVIEW,
    ) is FundingNotificationEvent.REVIEW_REQUIRED
    assert notification_event_type(
        baseline=False,
        change_status="CHANGED",
        relevance_status=RelevanceStatus.RELEVANT,
    ) is FundingNotificationEvent.CHANGED
    assert notification_event_type(
        baseline=False,
        change_status="CHANGED",
        relevance_status=RelevanceStatus.NEEDS_REVIEW,
    ) is FundingNotificationEvent.REVIEW_REQUIRED
    assert (
        notification_event_type(
            baseline=False,
            change_status="UNCHANGED",
            relevance_status=RelevanceStatus.RELEVANT,
        )
        is None
    )
