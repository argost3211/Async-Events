from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from event_generator.services.producer_client import ProducerClient


@pytest.fixture
def mock_httpx_client():
    client = MagicMock(spec=httpx.AsyncClient)
    client.post = AsyncMock()
    return client


@pytest.fixture
def producer_client(mock_httpx_client):
    return ProducerClient(
        base_url="http://producer:8000", http_client=mock_httpx_client
    )


async def test_send_event_returns_true_on_201(producer_client, mock_httpx_client):
    mock_httpx_client.post.return_value = httpx.Response(201)
    occurred = datetime.now(timezone.utc)
    result = await producer_client.send_event(
        order_id="ord-1",
        user_id="user-1",
        event_type="order_created",
        event_occurred_at=occurred,
    )
    assert result is True
    mock_httpx_client.post.assert_called_once()
    call_kwargs = mock_httpx_client.post.call_args
    assert call_kwargs[0][0] == "http://producer:8000/api/v1/events"
    assert call_kwargs[1]["json"]["order_id"] == "ord-1"
    assert call_kwargs[1]["json"]["user_id"] == "user-1"
    assert call_kwargs[1]["json"]["event_type"] == "order_created"
    assert "event_occurred_at" in call_kwargs[1]["json"]


async def test_send_event_returns_false_on_5xx(producer_client, mock_httpx_client):
    mock_httpx_client.post.return_value = httpx.Response(503)
    occurred = datetime.now(timezone.utc)
    result = await producer_client.send_event(
        order_id="ord-1",
        user_id="user-1",
        event_type="order_created",
        event_occurred_at=occurred,
    )
    assert result is False


async def test_send_event_returns_false_on_4xx(producer_client, mock_httpx_client):
    mock_httpx_client.post.return_value = httpx.Response(400)
    occurred = datetime.now(timezone.utc)
    result = await producer_client.send_event(
        order_id="ord-1",
        user_id="user-1",
        event_type="order_paid",
        event_occurred_at=occurred,
    )
    assert result is False


async def test_send_event_returns_false_on_connection_error(
    producer_client, mock_httpx_client
):
    mock_httpx_client.post.side_effect = httpx.ConnectError("unreachable")
    occurred = datetime.now(timezone.utc)
    result = await producer_client.send_event(
        order_id="ord-1",
        user_id="user-1",
        event_type="order_created",
        event_occurred_at=occurred,
    )
    assert result is False
