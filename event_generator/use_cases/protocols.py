from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from event_generator.domain.order_pool import OrderEventPool


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


class EventLoopRunner(Protocol):
    async def run(self, pool: OrderEventPool) -> None: ...
