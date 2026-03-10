"""Протоколы (порты) для инверсии зависимостей use cases."""

from __future__ import annotations

from typing import Protocol

from consumer.domain.notifications import Notification


class NotificationRepository(Protocol):
    async def exists(self, order_id: str, event_type: str) -> bool: ...

    async def create_notification(
        self,
        user_id: str,
        order_id: str,
        event_type: str,
        message: str,
    ) -> Notification: ...
