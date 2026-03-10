import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from consumer.models.events import EventMessage
from consumer.services.kafka_consumer import (
    DLQErrorInfo,
    KafkaConsumerClient,
)


@pytest.fixture
def order_event_bytes():
    return json.dumps(
        {
            "event_id": "e1",
            "order_id": "order-1",
            "user_id": "user-1",
            "event_type": "order_created",
            "event_occurred_at": datetime.now(timezone.utc).isoformat(),
        }
    ).encode("utf-8")


@pytest.fixture
def mock_consumer(order_event_bytes):
    consumer = AsyncMock()
    msg = MagicMock()
    msg.value = order_event_bytes
    msg.key = b"user-1:order-1"
    consumer.getone = AsyncMock(side_effect=[msg, KeyboardInterrupt])
    consumer.commit = AsyncMock()
    consumer.start = AsyncMock()
    consumer.stop = AsyncMock()
    return consumer


@pytest.fixture
def mock_producer():
    producer = AsyncMock()
    producer.send_and_wait = AsyncMock()
    producer.start = AsyncMock()
    producer.stop = AsyncMock()
    return producer


async def test_consume_loop_success_calls_handler_and_commit(
    mock_consumer, mock_producer, order_event_bytes
):
    handler = AsyncMock()
    with (
        patch(
            "consumer.services.kafka_consumer.AIOKafkaConsumer",
            return_value=mock_consumer,
        ),
        patch(
            "consumer.services.kafka_consumer.AIOKafkaProducer",
            return_value=mock_producer,
        ),
    ):
        client = KafkaConsumerClient()
        await client.connect()
        try:
            with pytest.raises(KeyboardInterrupt):
                await client.consume_loop(handler)
        finally:
            await client.disconnect()
    handler.assert_called_once()
    call_arg = handler.call_args[0][0]
    assert isinstance(call_arg, EventMessage)
    assert call_arg.order_id == "order-1"
    assert call_arg.event_type == "order_created"
    mock_consumer.commit.assert_called()


async def test_consume_loop_handler_error_retries_then_dlq(
    mock_consumer, mock_producer, order_event_bytes
):
    handler = AsyncMock(side_effect=RuntimeError("db error"))
    with (
        patch(
            "consumer.services.kafka_consumer.AIOKafkaConsumer",
            return_value=mock_consumer,
        ),
        patch(
            "consumer.services.kafka_consumer.AIOKafkaProducer",
            return_value=mock_producer,
        ),
        patch("consumer.services.kafka_consumer.config") as mock_config,
    ):
        mock_config.kafka_connect_retry_attempts = 1
        mock_config.kafka_bootstrap_servers = "localhost:9092"
        mock_config.kafka_order_events_topic = "order-events"
        mock_config.consumer_group_id = "test-group"
        mock_config.kafka_order_events_dlq_topic = "order-events-dlq"
        mock_config.consumer_max_retries = 2
        mock_config.consumer_retry_base_delay = 0.01
        mock_config.consumer_retry_max_delay = 0.1
        client = KafkaConsumerClient()
        await client.connect()
        try:
            with pytest.raises(KeyboardInterrupt):
                await client.consume_loop(handler)
        finally:
            await client.disconnect()
    assert handler.call_count == 2
    mock_producer.send_and_wait.assert_called_once()
    call_kw = mock_producer.send_and_wait.call_args[1]
    assert call_kw["value"] is not None
    payload = json.loads(call_kw["value"].decode("utf-8"))
    assert "error_reason" in payload
    assert "attempt_count" in payload
    assert payload["attempt_count"] == 2
    mock_consumer.commit.assert_called()


async def test_publish_to_dlq_sends_payload(mock_producer):
    with (
        patch(
            "consumer.services.kafka_consumer.AIOKafkaConsumer",
            return_value=AsyncMock(),
        ),
        patch(
            "consumer.services.kafka_consumer.AIOKafkaProducer",
            return_value=mock_producer,
        ),
    ):
        client = KafkaConsumerClient()
        await client.connect()
        try:
            await client.publish_to_dlq(
                original_value=b'{"event_id":"e1"}',
                original_key=b"key",
                error_info=DLQErrorInfo(
                    error_reason="test error",
                    attempt_count=3,
                    timestamp=datetime.now(timezone.utc),
                ),
            )
        finally:
            await client.disconnect()
    mock_producer.send_and_wait.assert_called_once()
    call_args = mock_producer.send_and_wait.call_args
    assert call_args[0][0] == "order-events-dlq"
    payload = json.loads(call_args[1]["value"].decode("utf-8"))
    assert payload["error_reason"] == "test error"
    assert payload["attempt_count"] == 3
