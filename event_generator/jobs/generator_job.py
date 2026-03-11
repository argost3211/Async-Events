"""Фоновая задача: запуск генератора событий после сборки зависимостей."""

import httpx

from event_generator.core.config import config
from event_generator.core.metrics import EVENTS_PER_SECOND_TARGET
from event_generator.services.health_checker import HealthChecker
from event_generator.services.producer_client import ProducerClient
from event_generator.services.rate_limited_event_loop import RateLimitedEventLoop
from event_generator.services.rate_limited_sender import RateLimitedSender
from event_generator.use_cases.generate_events import GenerateEventsUseCase


async def run_generator() -> None:
    EVENTS_PER_SECOND_TARGET.set(config.events_per_second)
    async with httpx.AsyncClient(timeout=config.sender_timeout_seconds) as http_client:
        producer_client = ProducerClient(
            base_url=config.producer_base_url,
            http_client=http_client,
        )
        rate_limited_sender = RateLimitedSender(
            sender=producer_client,
            sender_max_concurrent=config.sender_max_concurrent,
            timeout_seconds=config.sender_timeout_seconds,
            max_retries=config.sender_max_retries,
            backoff_factor=config.sender_backoff_factor,
        )
        health_checker = HealthChecker(
            base_url=config.producer_base_url,
            http_client=http_client,
            retry_seconds=config.health_retry_seconds,
            retry_attempts=config.health_retry_attempts,
        )
        event_loop_runner = RateLimitedEventLoop(
            event_sender=rate_limited_sender,
            events_per_second=config.events_per_second,
        )
        use_case = GenerateEventsUseCase(
            event_loop_runner=event_loop_runner,
            health_waiter=health_checker,
            active_orders=config.active_orders,
            duplicate_probability=config.duplicate_probability,
            cancel_probability=config.cancel_probability,
        )
        await use_case.execute()
