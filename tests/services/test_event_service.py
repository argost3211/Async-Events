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

    event = await event_service.create_event("some_type", "some message")

    assert event.type == "some_type"
    assert event.message == "some message"
    mocked_session.add.assert_called_once()
    mocked_session.refresh.assert_called_once()
    assert mocked_session.add.call_args[0][0] is event


async def test_get_event_returns_event(
    event_service: EventService, mocked_session: AsyncSession
):
    event_id = uuid4()
    expected = make_event(event_id=event_id, type="found", message="found msg")
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

    result = await event_service.get_event("any-id")

    assert result is None
    mocked_session.execute.assert_called_once()


async def test_get_all_events(
    event_service: EventService, mocked_session: AsyncSession
):
    events = [
        make_event(type="a", message="msg a"),
        make_event(type="b", message="msg b"),
    ]
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = events
    mocked_session.execute = AsyncMock(return_value=result_mock)

    result = await event_service.get_all_events()

    assert result == events
    assert len(result) == 2
    mocked_session.execute.assert_called_once()
