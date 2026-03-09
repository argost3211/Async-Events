"""Use case: выборка непропубликованных событий и отправка через publisher."""

import logging
from dataclasses import dataclass
from datetime import datetime

from producer.use_cases.protocols import EventRepository, EventPublisher

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RepublishResult:
    published_count: int = 0
    error_count: int = 0


class RepublishUnpublishedEventsUseCase:
    """
    Выборка событий с published_to_kafka=False за окно created_after
    и их публикация через EventPublisher.
    """

    def __init__(
        self,
        event_repo: EventRepository,
        kafka_publisher: EventPublisher,
    ) -> None:
        self._event_repo = event_repo
        self._kafka_publisher = kafka_publisher

    async def execute(
        self,
        created_after: datetime,
        limit: int,
    ) -> RepublishResult:
        events = await self._event_repo.get_unpublished(
            created_after=created_after, limit=limit
        )
        published_count = 0
        error_count = 0
        for event in events:
            try:
                await self._kafka_publisher.publish_order_event(event)
                await self._event_repo.mark_published(event.id)
                published_count += 1
            except Exception as e:
                error_count += 1
                logger.warning("Republish failed for event %s: %s", event.id, e)
        return RepublishResult(published_count=published_count, error_count=error_count)
