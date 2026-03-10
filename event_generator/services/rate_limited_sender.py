"""Rate-limited wrapper for EventSender: concurrency cap, timeout, retry with backoff."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from event_generator.use_cases.protocols import EventSender

logger = logging.getLogger(__name__)


class RateLimitedSender:
    """Wraps an EventSender with semaphore-based concurrency limit, timeout and retry."""

    def __init__(
        self,
        sender: EventSender,
        *,
        sender_max_concurrent: int,
        timeout_seconds: float,
        max_retries: int,
        backoff_factor: float,
    ) -> None:
        self._sender = sender
        self._semaphore = asyncio.Semaphore(max(1, sender_max_concurrent))
        self._timeout_seconds = timeout_seconds
        self._max_retries = max(1, max_retries)
        self._backoff_factor = backoff_factor

    async def send_event(
        self,
        order_id: str,
        user_id: str,
        event_type: str,
        event_occurred_at: datetime,
    ) -> bool:
        async with self._semaphore:
            return await self._send_with_retry(
                order_id=order_id,
                user_id=user_id,
                event_type=event_type,
                event_occurred_at=event_occurred_at,
            )

    async def _send_with_retry(
        self,
        order_id: str,
        user_id: str,
        event_type: str,
        event_occurred_at: datetime,
    ) -> bool:
        last_error: BaseException | None = None
        for attempt in range(self._max_retries):
            try:
                async with asyncio.timeout(self._timeout_seconds):
                    result = await self._sender.send_event(
                        order_id=order_id,
                        user_id=user_id,
                        event_type=event_type,
                        event_occurred_at=event_occurred_at,
                    )
                    if attempt > 0:
                        logger.info(
                            "Send succeeded on attempt %s: order_id=%s",
                            attempt + 1,
                            order_id,
                        )
                    return result
            except (TimeoutError, OSError, ConnectionError) as e:
                last_error = e
                logger.warning(
                    "Send attempt %s failed for order_id=%s: %s",
                    attempt + 1,
                    order_id,
                    e,
                )
                if attempt < self._max_retries - 1:
                    pause = self._backoff_factor**attempt
                    await asyncio.sleep(pause)
        logger.error(
            "All %s send attempts failed for order_id=%s: %s",
            self._max_retries,
            order_id,
            last_error,
        )
        return False
