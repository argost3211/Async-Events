import asyncio
import logging

from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from aiokafka.errors import TopicAlreadyExistsError
from faststream.kafka import KafkaBroker

from producer.core.config import config
from producer.domain.events import Event
from producer.models.events import EventKafkaPayload

logger = logging.getLogger(__name__)


class KafkaClient:
    def __init__(self) -> None:
        self._broker = KafkaBroker(config.kafka_bootstrap_servers)
        self._admin: AIOKafkaAdminClient | None = None

    async def connect(self) -> None:
        """Подключение к Kafka с retry и создание топиков при отсутствии."""
        for attempt in range(1, config.kafka_connect_retry_attempts + 1):
            try:
                await self._broker.connect()
                logger.info("Kafka broker connected")
                break
            except Exception as e:
                logger.warning(
                    "Kafka connect attempt %s/%s failed: %s",
                    attempt,
                    config.kafka_connect_retry_attempts,
                    e,
                )
                if attempt == config.kafka_connect_retry_attempts:
                    raise
                await asyncio.sleep(config.kafka_connect_retry_seconds)
        await self._ensure_topics()

    async def _ensure_topics(self) -> None:
        """Создание топиков при отсутствии (игнорируем TopicAlreadyExistsError)."""
        self._admin = AIOKafkaAdminClient(
            bootstrap_servers=config.kafka_bootstrap_servers
        )
        await self._admin.start()
        try:
            for new_topic in [
                NewTopic(
                    name=config.kafka_order_events_topic,
                    num_partitions=config.kafka_order_events_partitions,
                    replication_factor=config.kafka_replication_factor,
                ),
                NewTopic(
                    name=config.kafka_order_events_dlq_topic,
                    num_partitions=config.kafka_order_events_dlq_partitions,
                    replication_factor=config.kafka_replication_factor,
                ),
            ]:
                try:
                    await self._admin.create_topics([new_topic])
                    logger.info("Created Kafka topic: %s", new_topic.name)
                except TopicAlreadyExistsError:
                    pass
        finally:
            await self._admin.close()
            self._admin = None

    async def disconnect(self) -> None:
        """Отключение брокера."""
        await self._broker.stop()

    async def publish_order_event(self, event: Event) -> None:
        """Сериализует доменное событие и отправляет в топик order-events."""
        payload = EventKafkaPayload(
            event_id=str(event.id),
            order_id=event.order_id,
            user_id=event.user_id,
            event_type=event.event_type,
            event_occurred_at=event.event_occurred_at,
        )
        key = f"{event.user_id}:{event.order_id}".encode("utf-8")
        value = payload.model_dump(mode="json")
        await self._broker.publish(
            value,
            topic=config.kafka_order_events_topic,
            key=key,
        )
