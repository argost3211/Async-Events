import uuid

import pytest


def _event_payload(
    order_id: str = "ord-1", user_id: str = "user-1", event_type: str = "order_created"
):
    from datetime import datetime, timezone

    return {
        "order_id": order_id,
        "user_id": user_id,
        "event_type": event_type,
        "event_occurred_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.mark.integration
async def test_post_events_returns_created_event(client):
    response = await client.post(
        "/api/v1/events",
        json=_event_payload(order_id="ord-1", user_id="u1", event_type="order_created"),
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert uuid.UUID(data["id"])
    assert data["order_id"] == "ord-1"
    assert data["user_id"] == "u1"
    assert data["event_type"] == "order_created"
    assert data["published_to_kafka"] is False
    assert "created_at" in data
    assert "event_occurred_at" in data


@pytest.mark.integration
async def test_get_events_empty_then_with_item(client):
    response = await client.get("/api/v1/events")
    assert response.status_code == 200
    assert response.json() == []

    await client.post(
        "/api/v1/events",
        json=_event_payload(order_id="ord-2", user_id="u2", event_type="order_paid"),
    )
    response = await client.get("/api/v1/events")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["order_id"] == "ord-2"
    assert items[0]["user_id"] == "u2"
    assert items[0]["event_type"] == "order_paid"
    assert "id" in items[0]
    assert "created_at" in items[0]
    assert "event_occurred_at" in items[0]
    assert items[0]["published_to_kafka"] is False


@pytest.mark.integration
async def test_get_event_by_id_returns_event(client):
    create_resp = await client.post(
        "/api/v1/events",
        json=_event_payload(order_id="ord-3", user_id="u3", event_type="order_shipped"),
    )
    assert create_resp.status_code == 201
    event_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/events/{event_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == event_id
    assert data["order_id"] == "ord-3"
    assert data["user_id"] == "u3"
    assert data["event_type"] == "order_shipped"
    assert "created_at" in data
    assert "event_occurred_at" in data


@pytest.mark.integration
async def test_get_event_by_id_returns_404_when_not_found(client):
    unknown_id = str(uuid.uuid4())
    response = await client.get(f"/api/v1/events/{unknown_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"


@pytest.mark.integration
async def test_health_returns_200(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.integration
async def test_metrics_returns_prometheus_text(client):
    response = await client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")
    body = response.text
    assert "producer_events_received_total" in body or "producer_" in body
