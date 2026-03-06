"""Фабрики тестовых данных (общий модуль для всех тестов)."""

from datetime import datetime, timezone
from uuid import uuid4, UUID

from producer.db.schema.events import Event


def make_event(
    event_id: UUID | None = None,
    order_id: str = "order-1",
    user_id: str = "user-1",
    event_type: str = "order_created",
    event_occurred_at: datetime | None = None,
    published_to_kafka: bool = False,
) -> Event:
    """Создаёт тестовый Event (событие заказа) с заданными полями."""
    e = Event(
        order_id=order_id,
        user_id=user_id,
        event_type=event_type,
        event_occurred_at=event_occurred_at or datetime.now(timezone.utc),
        published_to_kafka=published_to_kafka,
    )
    e.id = event_id or uuid4()
    e.created_at = datetime.now(timezone.utc)
    return e
