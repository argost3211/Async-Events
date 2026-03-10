import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)


class HealthChecker:
    def __init__(
        self,
        base_url: str,
        *,
        http_client: httpx.AsyncClient | None = None,
        retry_seconds: int = 2,
        retry_attempts: int = 30,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = http_client
        self._retry_seconds = retry_seconds
        self._retry_attempts = retry_attempts

    async def wait_for_ready(self) -> None:
        url = f"{self._base_url}/health"
        client = self._client
        own_client = False
        if client is None:
            client = httpx.AsyncClient()
            own_client = True
        try:
            for attempt in range(1, self._retry_attempts + 1):
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        return
                except Exception as e:
                    logger.warning(
                        "Health check attempt %s/%s failed: %s",
                        attempt,
                        self._retry_attempts,
                        e,
                    )
                if attempt < self._retry_attempts:
                    await asyncio.sleep(self._retry_seconds)
            raise RuntimeError("Producer health check failed")
        finally:
            if own_client:
                await client.aclose()
