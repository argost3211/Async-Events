"""Протоколы (порты) для инверсии зависимостей use cases."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from producer.domain.events import Event


class EventRepository(Protocol):
    async def create_event(
        self,
        order_id: str,
        user_id: str,
        event_type: str,
        event_occurred_at: datetime,
    ) -> Event: ...

    async def get_event(self, event_id: str) -> Event | None: ...

    async def get_all_events(self) -> list[Event]: ...

    async def mark_published(self, event_id: UUID) -> None: ...

    async def get_unpublished(
        self, created_after: datetime, limit: int
    ) -> list[Event]: ...


class EventPublisher(Protocol):
    """Абстракция публикации события."""

    async def publish_order_event(self, event: Event) -> None: ...
