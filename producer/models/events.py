from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator

from typing import Literal

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
