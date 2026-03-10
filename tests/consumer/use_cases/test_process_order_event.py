from datetime import datetime, timezone
from unittest.mock import AsyncMock

from consumer.use_cases.process_order_event import ProcessOrderEventUseCase
from tests.consumer.factories import make_notification


def _render_message(event_type: str, order_id: str) -> str:
    return f"Заказ {order_id}: {event_type}"


async def test_process_new_event_creates_notification():
    notification = make_notification()
    repo = AsyncMock()
    repo.exists = AsyncMock(return_value=False)
    repo.create_notification = AsyncMock(return_value=notification)

    use_case = ProcessOrderEventUseCase(
        notification_repo=repo,
        message_renderer=_render_message,
    )
    result = await use_case.execute(
        event_id="e1",
        order_id="order-1",
        user_id="user-1",
        event_type="order_created",
        event_occurred_at=datetime.now(timezone.utc),
    )

    assert result.skipped is False
    assert result.notification is notification
    repo.exists.assert_called_once_with(order_id="order-1", event_type="order_created")
    repo.create_notification.assert_called_once()
    call_kw = repo.create_notification.call_args[1]
    assert call_kw["user_id"] == "user-1"
    assert call_kw["order_id"] == "order-1"
    assert call_kw["event_type"] == "order_created"
    assert call_kw["message"] == "Заказ order-1: order_created"


async def test_process_duplicate_event_skipped():
    repo = AsyncMock()
    repo.exists = AsyncMock(return_value=True)
    repo.create_notification = AsyncMock()

    use_case = ProcessOrderEventUseCase(
        notification_repo=repo,
        message_renderer=_render_message,
    )
    result = await use_case.execute(
        event_id="e1",
        order_id="order-1",
        user_id="user-1",
        event_type="order_paid",
        event_occurred_at=datetime.now(timezone.utc),
    )

    assert result.skipped is True
    assert result.notification is None
    repo.exists.assert_called_once_with(order_id="order-1", event_type="order_paid")
    repo.create_notification.assert_not_called()
