from datetime import datetime, timezone
from unittest.mock import AsyncMock

from producer.use_cases.create_order_event import CreateOrderEventUseCase
from tests.producer.factories import make_event


async def test_creates_event_without_publisher():
    event = make_event()
    repo = AsyncMock()
    repo.create_event = AsyncMock(return_value=event)

    use_case = CreateOrderEventUseCase(event_repo=repo)
    result = await use_case.execute(
        order_id="ord-1",
        user_id="user-1",
        event_type="order_created",
        event_occurred_at=datetime.now(timezone.utc),
    )

    assert result.event is event
    assert result.published is False
    assert result.kafka_error is False
    repo.create_event.assert_called_once()


async def test_creates_event_and_publishes():
    event = make_event()
    repo = AsyncMock()
    repo.create_event = AsyncMock(return_value=event)
    publisher = AsyncMock()

    use_case = CreateOrderEventUseCase(event_repo=repo, kafka_publisher=publisher)
    result = await use_case.execute(
        order_id="ord-1",
        user_id="user-1",
        event_type="order_created",
        event_occurred_at=datetime.now(timezone.utc),
    )

    assert result.event.published_to_kafka is True
    assert result.published is True
    assert result.kafka_error is False
    publisher.publish_order_event.assert_called_once_with(event)
    repo.mark_published.assert_called_once_with(event.id)


async def test_creates_event_kafka_failure():
    event = make_event()
    repo = AsyncMock()
    repo.create_event = AsyncMock(return_value=event)
    publisher = AsyncMock()
    publisher.publish_order_event = AsyncMock(side_effect=RuntimeError("kafka down"))

    use_case = CreateOrderEventUseCase(event_repo=repo, kafka_publisher=publisher)
    result = await use_case.execute(
        order_id="ord-1",
        user_id="user-1",
        event_type="order_created",
        event_occurred_at=datetime.now(timezone.utc),
    )

    assert result.event is event
    assert result.published is False
    assert result.kafka_error is True
    repo.mark_published.assert_not_called()
