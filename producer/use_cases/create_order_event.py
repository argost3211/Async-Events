"""Use case: создание события заказа и попытка публикации в Kafka."""

import logging
from dataclasses import dataclass, replace
from datetime import datetime

from producer.domain.events import Event
from producer.use_cases.protocols import EventRepository, EventPublisher

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CreateEventResult:
    event: Event
    published: bool
    kafka_error: bool = False


class CreateOrderEventUseCase:
    """
    Создание события заказа: запись в БД и при возможности — публикация.
    Возвращает CreateEventResult.
    """

    def __init__(
        self,
        event_repo: EventRepository,
        kafka_publisher: EventPublisher | None = None,
    ) -> None:
        self._event_repo = event_repo
        self._kafka_publisher = kafka_publisher

    async def execute(
        self,
        order_id: str,
        user_id: str,
        event_type: str,
        event_occurred_at: datetime,
    ) -> CreateEventResult:
        event = await self._event_repo.create_event(
            order_id=order_id,
            user_id=user_id,
            event_type=event_type,
            event_occurred_at=event_occurred_at,
        )

        if not self._kafka_publisher:
            return CreateEventResult(event=event, published=False)

        try:
            await self._kafka_publisher.publish_order_event(event)
            await self._event_repo.mark_published(event.id)
            event = replace(event, published_to_kafka=True)
            return CreateEventResult(event=event, published=True)
        except Exception as e:
            logger.warning(
                "Kafka publish failed, event will be republished by job: %s", e
            )
            return CreateEventResult(event=event, published=False, kafka_error=True)
