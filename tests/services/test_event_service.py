from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession

from producer.services.event_service import EventService
from tests.factories import make_event


async def test_create_event(event_service: EventService, mocked_session: AsyncSession):
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=None)
    cm.__aexit__ = AsyncMock(return_value=None)
    mocked_session.begin = MagicMock(return_value=cm)
    mocked_session.refresh = AsyncMock()

    event = await event_service.create_event(
        order_id="ord-1",
        user_id="user-1",
        event_type="order_created",
        event_occurred_at=datetime.now(timezone.utc),
    )

    assert event.order_id == "ord-1"
    assert event.user_id == "user-1"
    assert event.event_type == "order_created"
    assert event.published_to_kafka is False
    mocked_session.add.assert_called_once()
    mocked_session.refresh.assert_called_once()
    assert mocked_session.add.call_args[0][0] is event


async def test_get_event_returns_event(
    event_service: EventService, mocked_session: AsyncSession
):
    event_id = uuid4()
    expected = make_event(
        event_id=event_id,
        order_id="ord-1",
        user_id="user-1",
        event_type="order_paid",
    )
    result_mock = MagicMock()
    result_mock.scalars.return_value.first.return_value = expected
    mocked_session.execute = AsyncMock(return_value=result_mock)

    result = await event_service.get_event(str(event_id))

    assert result is expected
    mocked_session.execute.assert_called_once()


async def test_get_event_returns_none(
    event_service: EventService, mocked_session: AsyncSession
):
    result_mock = MagicMock()
    result_mock.scalars.return_value.first.return_value = None
    mocked_session.execute = AsyncMock(return_value=result_mock)

    result = await event_service.get_event(str(uuid4()))

    assert result is None
    mocked_session.execute.assert_called_once()


async def test_get_all_events(
    event_service: EventService, mocked_session: AsyncSession
):
    events = [
        make_event(order_id="ord-a", user_id="u1", event_type="order_created"),
        make_event(order_id="ord-b", user_id="u2", event_type="order_paid"),
    ]
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = events
    mocked_session.execute = AsyncMock(return_value=result_mock)

    result = await event_service.get_all_events()

    assert result == events
    assert len(result) == 2
    mocked_session.execute.assert_called_once()
