from __future__ import annotations

from typing import Literal, TYPE_CHECKING
from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator

if TYPE_CHECKING:
    from producer.domain.events import Event as DomainEvent

OrderEventType = Literal[
    "order_created",
    "order_paid",
    "order_shipped",
    "order_delivered",
    "order_cancelled",
]


def _to_utc(dt: datetime) -> datetime:
    """Приводит datetime к timezone-aware UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class EventCreate(BaseModel):
    order_id: str = Field(max_length=64)
    user_id: str = Field(max_length=64)
    event_type: OrderEventType
    event_occurred_at: datetime

    @field_validator("event_occurred_at", mode="after")
    @classmethod
    def event_occurred_at_utc(cls, v: datetime) -> datetime:
        return _to_utc(v)


class EventRead(BaseModel):
    id: str
    order_id: str
    user_id: str
    event_type: str
    created_at: datetime
    event_occurred_at: datetime
    published_to_kafka: bool

    @classmethod
    def from_domain(cls, event: DomainEvent) -> EventRead:
        return cls(
            id=str(event.id),
            order_id=event.order_id,
            user_id=event.user_id,
            event_type=event.event_type,
            created_at=event.created_at,
            event_occurred_at=event.event_occurred_at,
            published_to_kafka=event.published_to_kafka,
        )


class EventKafkaPayload(BaseModel):
    event_id: str
    order_id: str
    user_id: str
    event_type: str
    event_occurred_at: datetime

    @field_validator("event_occurred_at", mode="after")
    @classmethod
    def event_occurred_at_utc(cls, v: datetime) -> datetime:
        return _to_utc(v)
