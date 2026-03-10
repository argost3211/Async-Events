import logging
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)


class ProducerClient:
    def __init__(
        self,
        base_url: str,
        *,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = http_client

    async def send_event(
        self,
        order_id: str,
        user_id: str,
        event_type: str,
        event_occurred_at: datetime,
    ) -> bool:
        url = f"{self._base_url}/api/v1/events"
        payload = {
            "order_id": order_id,
            "user_id": user_id,
            "event_type": event_type,
            "event_occurred_at": event_occurred_at.isoformat(),
        }
        client = self._client
        own_client = False
        if client is None:
            client = httpx.AsyncClient()
            own_client = True
        try:
            response = await client.post(url, json=payload)
            if response.status_code == 201:
                return True
            logger.warning(
                "Producer API returned %s for order_id=%s event_type=%s",
                response.status_code,
                order_id,
                event_type,
            )
            return False
        except Exception as e:
            logger.exception(
                "Failed to send event order_id=%s event_type=%s: %s",
                order_id,
                event_type,
                e,
            )
            return False
        finally:
            if own_client:
                await client.aclose()
