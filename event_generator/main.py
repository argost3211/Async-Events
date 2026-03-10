import asyncio

import httpx

from event_generator.core.config import config
from event_generator.core.logging import setup_logging
from event_generator.services.health_checker import HealthChecker
from event_generator.services.producer_client import ProducerClient
from event_generator.use_cases.generate_events import GenerateEventsUseCase

setup_logging()


async def run() -> None:
    async with httpx.AsyncClient() as http_client:
        producer_client = ProducerClient(
            base_url=config.producer_base_url,
            http_client=http_client,
        )
        health_checker = HealthChecker(
            base_url=config.producer_base_url,
            http_client=http_client,
            retry_seconds=config.health_retry_seconds,
            retry_attempts=config.health_retry_attempts,
        )
        use_case = GenerateEventsUseCase(
            event_sender=producer_client,
            health_waiter=health_checker,
            active_orders=config.active_orders,
            events_per_second=config.events_per_second,
            duplicate_probability=config.duplicate_probability,
            cancel_probability=config.cancel_probability,
            min_delay_ms=config.min_delay_ms,
            max_delay_ms=config.max_delay_ms,
        )
        await use_case.execute()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
