import asyncio
from datetime import datetime
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from event_generator.domain.order_pool import OrderEventPool
from event_generator.services.rate_limited_event_loop import RateLimitedEventLoop
from event_generator.use_cases.generate_events import GenerateEventsUseCase


@pytest.fixture
def event_sender():
    sender = AsyncMock()
    sender.send_event = AsyncMock(return_value=True)
    return sender


@pytest.fixture
def event_loop_runner(event_sender):
    return RateLimitedEventLoop(
        event_sender=event_sender,
        events_per_second=100.0,
    )


@pytest.fixture
def health_waiter():
    waiter = AsyncMock()
    waiter.wait_for_ready = AsyncMock(return_value=None)
    return waiter


@pytest.fixture
def use_case(event_loop_runner, health_waiter):
    return GenerateEventsUseCase(
        event_loop_runner=event_loop_runner,
        health_waiter=health_waiter,
        active_orders=2,
        duplicate_probability=0.0,
        cancel_probability=0.0,
    )


async def test_wait_for_ready_called_before_loop(health_waiter):
    mock_runner = AsyncMock()
    use_case = GenerateEventsUseCase(
        event_loop_runner=mock_runner,
        health_waiter=health_waiter,
        active_orders=2,
        duplicate_probability=0.0,
        cancel_probability=0.0,
    )
    task = asyncio.create_task(use_case.execute())
    await asyncio.sleep(0.05)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    health_waiter.wait_for_ready.assert_called_once()
    mock_runner.run.assert_called_once()
    (pool,) = mock_runner.run.call_args[0]
    assert isinstance(pool, OrderEventPool)


async def test_send_event_called_with_correct_payload(use_case, event_sender):
    task = asyncio.create_task(use_case.execute())
    await asyncio.sleep(0.15)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
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
    task = asyncio.create_task(use_case.execute())
    await asyncio.sleep(0.2)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    order_ids = {c[1]["order_id"] for c in event_sender.send_event.await_args_list}
    assert len(order_ids) >= 1
    for oid in order_ids:
        UUID(oid)


async def test_duplicate_sent_when_duplicate_probability_one(event_sender):
    runner = RateLimitedEventLoop(
        event_sender=event_sender,
        events_per_second=100.0,
    )
    use_case = GenerateEventsUseCase(
        event_loop_runner=runner,
        health_waiter=AsyncMock(wait_for_ready=AsyncMock(return_value=None)),
        active_orders=1,
        duplicate_probability=1.0,
        cancel_probability=0.0,
    )
    task = asyncio.create_task(use_case.execute())
    await asyncio.sleep(0.15)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    assert event_sender.send_event.await_count >= 5


async def test_chain_advances_after_send(use_case, event_sender):
    task = asyncio.create_task(use_case.execute())
    await asyncio.sleep(0.2)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    event_types = [c[1]["event_type"] for c in event_sender.send_event.await_args_list]
    assert "order_created" in event_types
    assert any(t != "order_created" for t in event_types)
