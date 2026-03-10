from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from event_generator.use_cases.generate_events import GenerateEventsUseCase


@pytest.fixture
def event_sender():
    sender = AsyncMock()
    sender.send_event = AsyncMock(return_value=True)
    return sender


@pytest.fixture
def health_waiter():
    waiter = AsyncMock()
    waiter.wait_for_ready = AsyncMock(return_value=None)
    return waiter


@pytest.fixture
def use_case(event_sender, health_waiter):
    return GenerateEventsUseCase(
        event_sender=event_sender,
        health_waiter=health_waiter,
        active_orders=2,
        events_per_second=100.0,
        duplicate_probability=0.0,
        cancel_probability=0.0,
        min_delay_ms=0,
        max_delay_ms=0,
    )


async def test_wait_for_ready_called_before_loop(use_case, health_waiter):
    await use_case.execute(max_iterations=0)
    health_waiter.wait_for_ready.assert_called_once()


async def test_send_event_called_with_correct_payload(use_case, event_sender):
    await use_case.execute(max_iterations=3)
    assert event_sender.send_event.await_count >= 3
    calls = event_sender.send_event.await_args_list
    first = calls[0][1]
    assert first["order_id"]
    assert first["user_id"]
    assert first["event_type"] in (
        "order_created",
        "order_paid",
        "order_shipped",
        "order_delivered",
        "order_cancelled",
    )
    assert isinstance(first["event_occurred_at"], datetime)


async def test_pool_size_respected(use_case, event_sender):
    await use_case.execute(max_iterations=20)
    order_ids = {c[1]["order_id"] for c in event_sender.send_event.await_args_list}
    assert len(order_ids) <= 2


async def test_duplicate_sent_when_duplicate_probability_one(event_sender):
    use_case = GenerateEventsUseCase(
        event_sender=event_sender,
        health_waiter=AsyncMock(wait_for_ready=AsyncMock(return_value=None)),
        active_orders=1,
        events_per_second=100.0,
        duplicate_probability=1.0,
        cancel_probability=0.0,
        min_delay_ms=0,
        max_delay_ms=0,
    )
    await use_case.execute(max_iterations=5)
    assert event_sender.send_event.await_count >= 5


async def test_chain_advances_after_send(use_case, event_sender):
    await use_case.execute(max_iterations=10)
    event_types = [c[1]["event_type"] for c in event_sender.send_event.await_args_list]
    assert "order_created" in event_types
    assert any(t != "order_created" for t in event_types)
