from __future__ import annotations

import random
from datetime import datetime, timezone
from uuid import uuid4

from event_generator.domain.event_payload import EventPayload
from event_generator.domain.order_chain import OrderChain


class OrderEventPool:
    """Генерирует следующее событие из пула заказов с учётом дубликатов и отмен."""

    def __init__(
        self,
        pool_size: int,
        duplicate_probability: float,
        cancel_probability: float,
    ) -> None:
        self._pool: list[OrderChain] = [
            OrderChain(order_id=str(uuid4()), user_id=f"user-{i}")
            for i in range(pool_size)
        ]
        self._last_sent: dict[int, tuple[str, datetime]] = {}
        self._duplicate_probability = duplicate_probability
        self._cancel_probability = cancel_probability

    def generate_next(self) -> EventPayload | None:
        if not self._pool:
            return None
        idx = random.randint(0, len(self._pool) - 1)
        chain = self._pool[idx]
        event_type = chain.next_event_type()
        if event_type is None:
            self._replace_chain(idx)
            return None

        if random.random() < self._duplicate_probability and idx in self._last_sent:
            event_type, occurred = self._last_sent[idx]
            return EventPayload(
                order_id=chain.order_id,
                user_id=chain.user_id,
                event_type=event_type,
                event_occurred_at=occurred,
            )

        occurred = datetime.now(timezone.utc)
        if (
            not chain.cancelled
            and event_type != "order_delivered"
            and random.random() < self._cancel_probability
        ):
            chain.cancel()
            event_type = "order_cancelled"
        payload = EventPayload(
            order_id=chain.order_id,
            user_id=chain.user_id,
            event_type=event_type,
            event_occurred_at=occurred,
        )
        self._last_sent[idx] = (event_type, occurred)
        if event_type == "order_cancelled":
            self._replace_chain(idx)
        else:
            chain.advance()
            if chain.completed:
                self._replace_chain(idx)
                self._last_sent.pop(idx, None)
        return payload

    def _replace_chain(self, idx: int) -> None:
        self._pool[idx] = OrderChain(
            order_id=str(uuid4()),
            user_id=f"user-{idx}",
        )
