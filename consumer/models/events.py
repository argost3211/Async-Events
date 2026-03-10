from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, field_validator


def _to_utc(dt: datetime) -> datetime:
    """Приводит datetime к timezone-aware UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class EventMessage(BaseModel):
    """Pydantic-модель десериализации Kafka-сообщения (совпадает с EventKafkaPayload Producer)."""

    event_id: str
    order_id: str
    user_id: str
    event_type: str
    event_occurred_at: datetime

    @field_validator("event_occurred_at", mode="after")
    @classmethod
    def event_occurred_at_utc(cls, v: datetime) -> datetime:
        return _to_utc(v)
