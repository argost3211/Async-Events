from datetime import datetime
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from event_generator.domain.order_pool import OrderEventPool
from event_generator.services.rate_limited_event_loop import RateLimitedEventLoop


@pytest.fixture
def event_sender():
    sender = AsyncMock()
    sender.send_event = AsyncMock(return_value=True)
    return sender


@pytest.fixture
def event_loop(event_sender):
    return RateLimitedEventLoop(
        event_sender=event_sender,
        events_per_second=100.0,
    )


@pytest.fixture
def pool():
    return OrderEventPool(
        pool_size=2,
        duplicate_probability=0.0,
        cancel_probability=0.0,
    )


async def test_run_with_max_iterations_zero_sends_nothing(
    event_loop, pool, event_sender
):
    await event_loop.run(pool, max_iterations=0)
    event_sender.send_event.assert_not_called()


async def test_run_respects_max_iterations(event_loop, pool, event_sender):
    await event_loop.run(pool, max_iterations=3)
    assert event_sender.send_event.await_count >= 3


async def test_run_calls_send_with_payload_fields(event_loop, pool, event_sender):
    await event_loop.run(pool, max_iterations=2)
    calls = event_sender.send_event.await_args_list
    for call in calls:
        kwargs = call[1]
        assert "order_id" in kwargs
        assert "user_id" in kwargs
        assert kwargs["event_type"] in (
            "order_created",
            "order_paid",
            "order_shipped",
            "order_delivered",
            "order_cancelled",
        )
        assert isinstance(kwargs["event_occurred_at"], datetime)


async def test_run_uses_pool_order_ids(event_loop, pool, event_sender):
    await event_loop.run(pool, max_iterations=10)
    order_ids = {c[1]["order_id"] for c in event_sender.send_event.await_args_list}
    assert len(order_ids) >= 1
    for oid in order_ids:
        UUID(oid)
