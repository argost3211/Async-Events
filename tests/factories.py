"""Фабрики тестовых данных (общий модуль для всех тестов)."""

from datetime import datetime, timezone
from uuid import uuid4, UUID

from producer.db.schema.events import Event


def make_event(
    event_id: UUID | None = None,
    type: str = "test",
    message: str | None = "msg",
) -> Event:
    """Создаёт тестовый Event с заданными полями."""
    e = Event(type=type, message=message)
    e.id = event_id or uuid4()
    e.created_at = datetime.now(timezone.utc)
    return e
