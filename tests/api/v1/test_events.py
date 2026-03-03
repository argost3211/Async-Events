import uuid

import pytest


@pytest.mark.integration
async def test_post_events_returns_created_event(client):
    response = await client.post(
        "/api/v1/events",
        json={"type": "user_registered", "message": "test"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert uuid.UUID(data["id"])
    assert data["type"] == "user_registered"
    assert data["message"] == "test"
    assert "created_at" in data


@pytest.mark.integration
async def test_get_events_empty_then_with_item(client):
    # Список пустой: изоляция транзакции, данные предыдущих тестов откатаны
    response = await client.get("/api/v1/events")
    assert response.status_code == 200
    assert response.json() == []

    await client.post(
        "/api/v1/events",
        json={"type": "password_changed", "message": "list test"},
    )
    response = await client.get("/api/v1/events")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["type"] == "password_changed"
    assert items[0]["message"] == "list test"
    assert "id" in items[0]
    assert "created_at" in items[0]


@pytest.mark.integration
async def test_get_event_by_id_returns_event(client):
    create_resp = await client.post(
        "/api/v1/events",
        json={"type": "email_changed", "message": "get by id"},
    )
    assert create_resp.status_code == 200
    event_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/events/{event_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == event_id
    assert data["type"] == "email_changed"
    assert data["message"] == "get by id"
    assert "created_at" in data


@pytest.mark.integration
async def test_get_event_by_id_returns_404_when_not_found(client):
    unknown_id = str(uuid.uuid4())
    response = await client.get(f"/api/v1/events/{unknown_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"
