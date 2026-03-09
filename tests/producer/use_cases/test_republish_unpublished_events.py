from datetime import datetime, timezone
from unittest.mock import AsyncMock

from producer.use_cases.republish_unpublished_events import (
    RepublishUnpublishedEventsUseCase,
)
from tests.producer.factories import make_event


async def test_republish_all_ok():
    events = [make_event(order_id="ord-1"), make_event(order_id="ord-2")]
    repo = AsyncMock()
    repo.get_unpublished = AsyncMock(return_value=events)
    publisher = AsyncMock()

    use_case = RepublishUnpublishedEventsUseCase(
        event_repo=repo, kafka_publisher=publisher
    )
    result = await use_case.execute(
        created_after=datetime(2025, 1, 1, tzinfo=timezone.utc),
        limit=10,
    )

    assert result.published_count == 2
    assert result.error_count == 0
    assert publisher.publish_order_event.call_count == 2
    assert repo.mark_published.call_count == 2


async def test_republish_partial_failure():
    events = [make_event(order_id="ord-1"), make_event(order_id="ord-2")]
    repo = AsyncMock()
    repo.get_unpublished = AsyncMock(return_value=events)
    publisher = AsyncMock()
    publisher.publish_order_event = AsyncMock(
        side_effect=[None, RuntimeError("kafka down")]
    )

    use_case = RepublishUnpublishedEventsUseCase(
        event_repo=repo, kafka_publisher=publisher
    )
    result = await use_case.execute(
        created_after=datetime(2025, 1, 1, tzinfo=timezone.utc),
        limit=10,
    )

    assert result.published_count == 1
    assert result.error_count == 1
    repo.mark_published.assert_called_once_with(events[0].id)


async def test_republish_no_events():
    repo = AsyncMock()
    repo.get_unpublished = AsyncMock(return_value=[])
    publisher = AsyncMock()

    use_case = RepublishUnpublishedEventsUseCase(
        event_repo=repo, kafka_publisher=publisher
    )
    result = await use_case.execute(
        created_after=datetime(2025, 1, 1, tzinfo=timezone.utc),
        limit=10,
    )

    assert result.published_count == 0
    assert result.error_count == 0
    publisher.publish_order_event.assert_not_called()
