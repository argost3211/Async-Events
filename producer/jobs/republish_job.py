"""Фоновый job: периодический вызов use case повторной публикации."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from producer.core.config import config
from producer.core.metrics import REPUBLISH_ERRORS, REPUBLISH_PUBLISHED
from producer.db.engine import AsyncSessionLocal
from producer.services.event_service import EventService
from producer.use_cases.republish_unpublished_events import (
    RepublishUnpublishedEventsUseCase,
)

logger = logging.getLogger(__name__)


async def run_republish_loop(kafka_client) -> None:
    """Цикл с интервалом: выборка непропубликованных и отправка в Kafka через use case."""
    interval = config.republish_interval_seconds
    window_hours = config.republish_window_hours
    limit = config.republish_batch_limit
    while True:
        try:
            await asyncio.sleep(interval)
            created_after = datetime.now(timezone.utc) - timedelta(hours=window_hours)
            async with AsyncSessionLocal() as session:
                event_service = EventService(session)
                use_case = RepublishUnpublishedEventsUseCase(
                    event_service, kafka_client
                )
                result = await use_case.execute(
                    created_after=created_after, limit=limit
                )
                if result.published_count:
                    REPUBLISH_PUBLISHED.inc(result.published_count)
                if result.error_count:
                    REPUBLISH_ERRORS.inc(result.error_count)
        except asyncio.CancelledError:
            logger.info("Republish job cancelled")
            break
        except Exception as e:
            logger.exception("Republish job error: %s", e)
