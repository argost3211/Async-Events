from __future__ import annotations

from datetime import datetime
from typing import Protocol


class EventSender(Protocol):
    async def send_event(
        self,
        order_id: str,
        user_id: str,
        event_type: str,
        event_occurred_at: datetime,
    ) -> bool: ...


class HealthWaiter(Protocol):
    async def wait_for_ready(self) -> None: ...
