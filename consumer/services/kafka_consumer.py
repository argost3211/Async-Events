import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Awaitable, Callable

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.structs import ConsumerRecord

from consumer.core.config import config
from consumer.core import metrics as consumer_metrics
from consumer.models.events import EventMessage

logger = logging.getLogger(__name__)


@dataclass
class DLQErrorInfo:
    error_reason: str
    attempt_count: int
    timestamp: datetime


class KafkaConsumerClient:
    """Обертка над AIOKafkaConsumer и AIOKafkaProducer (для DLQ)."""

    def __init__(self) -> None:
        self._consumer: AIOKafkaConsumer | None = None
        self._producer: AIOKafkaProducer | None = None

    async def connect(self) -> None:
        """Подключение к Kafka с retry. Consumer не создаёт топики."""
        for attempt in range(1, config.kafka_connect_retry_attempts + 1):
            try:
                self._consumer = AIOKafkaConsumer(
                    config.kafka_order_events_topic,
                    bootstrap_servers=config.kafka_bootstrap_servers,
                    group_id=config.consumer_group_id,
                    enable_auto_commit=False,
                    auto_offset_reset="earliest",
                )
                await self._consumer.start()
                self._producer = AIOKafkaProducer(
                    bootstrap_servers=config.kafka_bootstrap_servers,
                )
                await self._producer.start()
                logger.info("Kafka consumer and producer connected")
                return
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

    async def disconnect(self) -> None:
        """Корректное закрытие consumer и producer."""
        if self._consumer:
            await self._consumer.stop()
            self._consumer = None
        if self._producer:
            await self._producer.stop()
            self._producer = None

    def _parse_message(self, raw_value: bytes | None) -> EventMessage | None:
        if raw_value is None:
            return None
        try:
            data = json.loads(raw_value.decode("utf-8"))
            return EventMessage.model_validate(data)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Failed to parse message: %s", e)
            return None

    async def publish_to_dlq(
        self,
        original_value: bytes,
        original_key: bytes | None,
        error_info: DLQErrorInfo,
    ) -> None:
        """Отправка в order-events-dlq: тело + метаданные."""
        if not self._producer:
            return
        payload = {
            "original_value": original_value.decode("utf-8", errors="replace"),
            "original_key": (
                original_key.decode("utf-8", errors="replace") if original_key else None
            ),
            "error_reason": error_info.error_reason,
            "attempt_count": error_info.attempt_count,
            "timestamp": error_info.timestamp.isoformat(),
        }
        value = json.dumps(payload).encode("utf-8")
        await self._producer.send_and_wait(
            config.kafka_order_events_dlq_topic,
            value=value,
            key=original_key,
        )

    async def consume_loop(
        self,
        handler: Callable[[EventMessage], Awaitable[None]],
    ) -> None:
        """
        Основной цикл потребления. Handler — async (message: EventMessage) -> None.
        При успехе — commit. При ошибке — retry с exponential backoff;
        после исчерпания попыток — DLQ и commit.
        """
        if not self._consumer:
            raise RuntimeError("Consumer not connected")
        while True:
            try:
                msg: ConsumerRecord = await self._consumer.getone()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Error fetching message: %s", e)
                continue
            parsed = self._parse_message(msg.value)
            if parsed is None:
                await self._consumer.commit()
                continue
            consumer_metrics.MESSAGES_CONSUMED.inc()
            last_error: Exception | None = None
            for attempt in range(1, config.consumer_max_retries + 1):
                try:
                    await handler(parsed)
                    last_error = None
                    break
                except Exception as e:
                    last_error = e
                    if attempt < config.consumer_max_retries:
                        consumer_metrics.RETRIES.inc()
                        delay = min(
                            config.consumer_retry_base_delay * (2 ** (attempt - 1)),
                            config.consumer_retry_max_delay,
                        )
                        logger.warning(
                            "Handler attempt %s/%s failed, retrying in %.1fs: %s",
                            attempt,
                            config.consumer_max_retries,
                            delay,
                            e,
                        )
                        await asyncio.sleep(delay)
            if last_error is not None:
                consumer_metrics.DLQ_MESSAGES.inc()
                error_info = DLQErrorInfo(
                    error_reason=str(last_error),
                    attempt_count=config.consumer_max_retries,
                    timestamp=datetime.now(timezone.utc),
                )
                await self.publish_to_dlq(msg.value or b"", msg.key, error_info)
            await self._consumer.commit()
