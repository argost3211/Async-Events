from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from event_generator.services.health_checker import HealthChecker


@pytest.fixture
def mock_httpx_client():
    client = MagicMock(spec=httpx.AsyncClient)
    client.get = AsyncMock()
    return client


@pytest.fixture
def health_checker(mock_httpx_client):
    return HealthChecker(
        base_url="http://producer:8000",
        http_client=mock_httpx_client,
        retry_seconds=1,
        retry_attempts=3,
    )


async def test_wait_for_ready_returns_on_first_200(health_checker, mock_httpx_client):
    mock_httpx_client.get.return_value = httpx.Response(200)
    await health_checker.wait_for_ready()
    mock_httpx_client.get.assert_called_once_with("http://producer:8000/health")


async def test_wait_for_ready_retries_until_200(health_checker, mock_httpx_client):
    mock_httpx_client.get.side_effect = [
        httpx.Response(503),
        httpx.Response(503),
        httpx.Response(200),
    ]
    await health_checker.wait_for_ready()
    assert mock_httpx_client.get.call_count == 3


async def test_wait_for_ready_raises_after_exhausted_attempts(
    health_checker, mock_httpx_client
):
    mock_httpx_client.get.return_value = httpx.Response(503)
    with pytest.raises(RuntimeError, match="Producer health check failed"):
        await health_checker.wait_for_ready()
    assert mock_httpx_client.get.call_count == 3


async def test_wait_for_ready_raises_on_connection_error(
    health_checker, mock_httpx_client
):
    mock_httpx_client.get.side_effect = httpx.ConnectError("unreachable")
    with pytest.raises(RuntimeError, match="Producer health check failed"):
        await health_checker.wait_for_ready()
