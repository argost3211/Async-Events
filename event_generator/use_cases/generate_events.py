from __future__ import annotations

import asyncio
import random
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from event_generator.core.metrics import EVENTS_SENT
from event_generator.domain.order_chain import OrderChain

if TYPE_CHECKING:
    from event_generator.use_cases.protocols import EventSender, HealthWaiter


class GenerateEventsUseCase:
    def __init__(
        self,
        *,
        event_sender: EventSender,
        health_waiter: HealthWaiter,
        active_orders: int,
        events_per_second: float,
        duplicate_probability: float,
        cancel_probability: float,
        min_delay_ms: int,
        max_delay_ms: int,
    ) -> None:
        self._event_sender = event_sender
        self._health_waiter = health_waiter
        self._active_orders = active_orders
        self._events_per_second = events_per_second
        self._duplicate_probability = duplicate_probability
        self._cancel_probability = cancel_probability
        self._min_delay_ms = min_delay_ms
        self._max_delay_ms = max_delay_ms

    async def execute(self, max_iterations: int | None = None) -> None:
        await self._health_waiter.wait_for_ready()
        pool: list[OrderChain] = [
            OrderChain(order_id=f"order-{i}", user_id=f"user-{i}")
            for i in range(self._active_orders)
        ]
        last_sent: dict[int, tuple[str, datetime]] = {}
        sent_count = 0

        while True:
            if max_iterations is not None and sent_count >= max_iterations:
                break
            idx = random.randint(0, len(pool) - 1)
            chain = pool[idx]
            event_type = chain.next_event_type()
            if event_type is None:
                pool[idx] = OrderChain(order_id=f"order-{idx}", user_id=f"user-{idx}")
                continue

            if random.random() < self._duplicate_probability and idx in last_sent:
                event_type, occurred = last_sent[idx]
                ok = await self._event_sender.send_event(
                    order_id=chain.order_id,
                    user_id=chain.user_id,
                    event_type=event_type,
                    event_occurred_at=occurred,
                )
                if ok:
                    EVENTS_SENT.inc()
                sent_count += 1
            else:
                occurred = datetime.now(timezone.utc)
                if (
                    not chain.cancelled
                    and event_type != "order_delivered"
                    and random.random() < self._cancel_probability
                ):
                    chain.cancel()
                    event_type = "order_cancelled"
                ok = await self._event_sender.send_event(
                    order_id=chain.order_id,
                    user_id=chain.user_id,
                    event_type=event_type,
                    event_occurred_at=occurred,
                )
                if ok:
                    EVENTS_SENT.inc()
                sent_count += 1
                last_sent[idx] = (event_type, occurred)
                if event_type == "order_cancelled":
                    pool[idx] = OrderChain(
                        order_id=f"order-{idx}", user_id=f"user-{idx}"
                    )
                else:
                    chain.advance()
                    if chain.completed:
                        pool[idx] = OrderChain(
                            order_id=f"order-{idx}", user_id=f"user-{idx}"
                        )
                        last_sent.pop(idx, None)

            delay_ms = random.randint(
                self._min_delay_ms,
                max(self._min_delay_ms, self._max_delay_ms),
            )
            if delay_ms > 0:
                await asyncio.sleep(delay_ms / 1000.0)

            if self._events_per_second > 0:
                await asyncio.sleep(1.0 / self._events_per_second)
