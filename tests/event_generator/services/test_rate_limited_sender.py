from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from event_generator.services.rate_limited_sender import RateLimitedSender


@pytest.fixture
def inner_sender():
    sender = AsyncMock()
    sender.send_event = AsyncMock(return_value=True)
    return sender


@pytest.fixture
def rate_limited_sender(inner_sender):
    return RateLimitedSender(
        sender=inner_sender,
        sender_max_concurrent=2,
        timeout_seconds=1.0,
        max_retries=3,
        backoff_factor=2.0,
    )


async def test_successful_send_returns_true(rate_limited_sender, inner_sender):
    occurred = datetime.now(timezone.utc)
    result = await rate_limited_sender.send_event(
        order_id="ord-1",
        user_id="user-1",
        event_type="order_created",
        event_occurred_at=occurred,
    )
    assert result is True
    inner_sender.send_event.assert_called_once_with(
        order_id="ord-1",
        user_id="user-1",
        event_type="order_created",
        event_occurred_at=occurred,
    )


async def test_returns_false_after_all_retries_exhausted(inner_sender):
    inner_sender.send_event = AsyncMock(
        side_effect=ConnectionError("unreachable"),
    )
    sender = RateLimitedSender(
        sender=inner_sender,
        sender_max_concurrent=1,
        timeout_seconds=0.1,
        max_retries=3,
        backoff_factor=0.01,
    )
    occurred = datetime.now(timezone.utc)
    result = await sender.send_event(
        order_id="ord-1",
        user_id="user-1",
        event_type="order_created",
        event_occurred_at=occurred,
    )
    assert result is False
    assert inner_sender.send_event.await_count == 3


async def test_retry_on_exception_then_succeed(inner_sender):
    inner_sender.send_event = AsyncMock(side_effect=[ConnectionError("fail"), True])
    sender = RateLimitedSender(
        sender=inner_sender,
        sender_max_concurrent=1,
        timeout_seconds=1.0,
        max_retries=3,
        backoff_factor=0.01,
    )
    occurred = datetime.now(timezone.utc)
    result = await sender.send_event(
        order_id="ord-1",
        user_id="user-1",
        event_type="order_created",
        event_occurred_at=occurred,
    )
    assert result is True
    assert inner_sender.send_event.await_count == 2


async def test_timeout_triggers_retry(inner_sender):
    async def slow_send(*args, **kwargs):
        await __import__("asyncio").sleep(10.0)
        return True

    inner_sender.send_event = AsyncMock(side_effect=slow_send)
    sender = RateLimitedSender(
        sender=inner_sender,
        sender_max_concurrent=1,
        timeout_seconds=0.05,
        max_retries=2,
        backoff_factor=0.01,
    )
    occurred = datetime.now(timezone.utc)
    result = await sender.send_event(
        order_id="ord-1",
        user_id="user-1",
        event_type="order_created",
        event_occurred_at=occurred,
    )
    assert result is False
    assert inner_sender.send_event.await_count == 2


async def test_concurrency_limited_by_semaphore(inner_sender):
    in_flight = 0
    max_seen = 0

    async def track_concurrent(*args, **kwargs):
        nonlocal in_flight, max_seen
        in_flight += 1
        if in_flight > max_seen:
            max_seen = in_flight
        await __import__("asyncio").sleep(0.05)
        in_flight -= 1
        return True

    inner_sender.send_event = AsyncMock(side_effect=track_concurrent)
    sender = RateLimitedSender(
        sender=inner_sender,
        sender_max_concurrent=2,
        timeout_seconds=5.0,
        max_retries=1,
        backoff_factor=1.0,
    )
    occurred = datetime.now(timezone.utc)
    tasks = [
        sender.send_event(
            order_id=f"ord-{i}",
            user_id=f"user-{i}",
            event_type="order_created",
            event_occurred_at=occurred,
        )
        for i in range(5)
    ]
    results = await __import__("asyncio").gather(*tasks)
    assert all(results)
    assert max_seen <= 2


async def test_semaphore_acquire_timeout(inner_sender):
    """When all semaphore slots are held by slow tasks, new task returns False on acquire timeout."""
    asyncio = __import__("asyncio")

    async def slow_send(*args, **kwargs):
        await asyncio.sleep(2.0)
        return True

    inner_sender.send_event = AsyncMock(side_effect=slow_send)
    sender = RateLimitedSender(
        sender=inner_sender,
        sender_max_concurrent=1,
        timeout_seconds=5.0,
        max_retries=1,
        backoff_factor=0.01,
        semaphore_acquire_timeout_seconds=0.1,
    )
    occurred = datetime.now(timezone.utc)

    hold_task = asyncio.create_task(
        sender.send_event(
            order_id="ord-hold",
            user_id="user-1",
            event_type="order_created",
            event_occurred_at=occurred,
        )
    )
    await asyncio.sleep(0.02)

    result = await sender.send_event(
        order_id="ord-wait",
        user_id="user-2",
        event_type="order_created",
        event_occurred_at=occurred,
    )
    assert result is False
    assert inner_sender.send_event.await_count == 1

    await hold_task
