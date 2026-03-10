from __future__ import annotations

from typing import TYPE_CHECKING

from event_generator.domain.order_pool import OrderEventPool

if TYPE_CHECKING:
    from event_generator.use_cases.protocols import EventLoopRunner, HealthWaiter


class GenerateEventsUseCase:
    """Координатор: ожидание готовности producer, создание пула, запуск цикла отправки."""

    def __init__(
        self,
        *,
        event_loop_runner: EventLoopRunner,
        health_waiter: HealthWaiter,
        active_orders: int,
        duplicate_probability: float,
        cancel_probability: float,
    ) -> None:
        self._event_loop_runner = event_loop_runner
        self._health_waiter = health_waiter
        self._active_orders = active_orders
        self._duplicate_probability = duplicate_probability
        self._cancel_probability = cancel_probability

    async def execute(self) -> None:
        await self._health_waiter.wait_for_ready()

        pool = OrderEventPool(
            pool_size=self._active_orders,
            duplicate_probability=self._duplicate_probability,
            cancel_probability=self._cancel_probability,
        )

        await self._event_loop_runner.run(pool)
