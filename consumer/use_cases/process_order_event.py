"""Use case: идемпотентная обработка события заказа и создание уведомления."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from consumer.domain.notifications import Notification
from consumer.use_cases.protocols import NotificationRepository


@dataclass(frozen=True)
class ProcessEventResult:
    notification: Notification | None
    skipped: bool


class ProcessOrderEventUseCase:
    """
    Обработка события заказа: проверка идемпотентности, создание уведомления.
    Возвращает ProcessEventResult. Не знает про Kafka, retry, метрики.
    """

    def __init__(
        self,
        notification_repo: NotificationRepository,
        message_renderer: Callable[[str, str], str],
    ) -> None:
        self._repo = notification_repo
        self._render_message = message_renderer

    async def execute(
        self,
        event_id: str,
        order_id: str,
        user_id: str,
        event_type: str,
        event_occurred_at: datetime,
    ) -> ProcessEventResult:
        if await self._repo.exists(order_id=order_id, event_type=event_type):
            return ProcessEventResult(notification=None, skipped=True)
        message = self._render_message(event_type=event_type, order_id=order_id)
        notification = await self._repo.create_notification(
            user_id=user_id,
            order_id=order_id,
            event_type=event_type,
            message=message,
        )
        return ProcessEventResult(notification=notification, skipped=False)
