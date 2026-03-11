"""Сервис: публикация события в Kafka и обновление published_to_kafka в фоне (новая сессия БД)."""

import logging

from producer.core.metrics import EVENTS_KAFKA_PUBLISHED
from producer.db.engine import AsyncSessionLocal
from producer.domain.events import Event
from producer.services.event_service import EventService
from producer.use_cases.protocols import EventPublisher

logger = logging.getLogger(__name__)


async def publish_event_after_response(
    event: Event, kafka_client: EventPublisher
) -> None:
    """Публикует событие в Kafka и помечает запись в БД (published_to_kafka). Использует новую сессию БД."""
    try:
        await kafka_client.publish_order_event(event)
        async with AsyncSessionLocal() as session:
            event_service = EventService(session=session)
            await event_service.mark_published(event.id)
        EVENTS_KAFKA_PUBLISHED.inc()
    except Exception as e:
        logger.warning(
            "Kafka publish failed in background, event will be republished by job: %s",
            e,
        )
