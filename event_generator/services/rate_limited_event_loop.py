"""Rate-limited event loop: semaphore-based rate, pool lock, send tasks; used by GenerateEventsUseCase."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from event_generator.domain.event_payload import EventPayload
from event_generator.domain.order_pool import OrderEventPool

if TYPE_CHECKING:
    from event_generator.use_cases.protocols import EventSender


class RateLimitedEventLoop:
    """Runs the send loop: rate semaphore refill task, pool lock, create_task(send_one)."""

    def __init__(self, *, event_sender: EventSender, events_per_second: float) -> None:
        self._event_sender = event_sender
        self._events_per_second = events_per_second

    async def run(
        self, pool: OrderEventPool, max_iterations: int | None = None
    ) -> None:
        interval = 1.0 / self._events_per_second if self._events_per_second > 0 else 0.0
        rate_semaphore: asyncio.Semaphore = asyncio.Semaphore(0)
        pool_lock = asyncio.Lock()
        pending_tasks: set[asyncio.Task[None]] = set()

        async def refill_rate() -> None:
            rate_semaphore.release()
            while True:
                if interval > 0:
                    await asyncio.sleep(interval)
                rate_semaphore.release()

        async def send_one(payload: EventPayload) -> None:
            await self._event_sender.send_event(
                order_id=payload.order_id,
                user_id=payload.user_id,
                event_type=payload.event_type,
                event_occurred_at=payload.event_occurred_at,
            )

        refill_task = asyncio.create_task(refill_rate())

        try:
            sent_count = 0
            while True:
                if max_iterations is not None and sent_count >= max_iterations:
                    break
                async with pool_lock:
                    payload = pool.generate_next()
                    if payload is None:
                        continue
                await rate_semaphore.acquire()
                sent_count += 1
                task = asyncio.create_task(send_one(payload))
                pending_tasks.add(task)
                task.add_done_callback(pending_tasks.discard)

            if pending_tasks:
                await asyncio.gather(*pending_tasks)
        except asyncio.CancelledError:
            refill_task.cancel()
            try:
                await refill_task
            except asyncio.CancelledError:
                pass
            if pending_tasks:
                await asyncio.gather(*pending_tasks, return_exceptions=True)
            raise
        finally:
            refill_task.cancel()
            try:
                await refill_task
            except asyncio.CancelledError:
                pass
