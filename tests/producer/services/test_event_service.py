from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession

from producer.services.event_service import EventService
from tests.producer.factories import make_orm_event


async def test_create_event(event_service: EventService, mocked_session: AsyncSession):
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=None)
    cm.__aexit__ = AsyncMock(return_value=None)
    mocked_session.begin = MagicMock(return_value=cm)
    mocked_session.flush = AsyncMock()

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
    mocked_session.flush.assert_called_once()


async def test_get_event_returns_event(
    event_service: EventService, mocked_session: AsyncSession
):
    event_id = uuid4()
    orm_event = make_orm_event(
        event_id=event_id,
        order_id="ord-1",
        user_id="user-1",
        event_type="order_paid",
    )
    result_mock = MagicMock()
    result_mock.scalars.return_value.first.return_value = orm_event
    mocked_session.execute = AsyncMock(return_value=result_mock)

    result = await event_service.get_event(str(event_id))

    assert result is not None
    assert result.id == event_id
    assert result.order_id == "ord-1"
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
    orm_events = [
        make_orm_event(order_id="ord-a", user_id="u1", event_type="order_created"),
        make_orm_event(order_id="ord-b", user_id="u2", event_type="order_paid"),
    ]
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = orm_events
    mocked_session.execute = AsyncMock(return_value=result_mock)

    result = await event_service.get_all_events()

    assert len(result) == 2
    assert result[0].order_id == "ord-a"
    assert result[1].order_id == "ord-b"
    mocked_session.execute.assert_called_once()


async def test_mark_published(
    event_service: EventService, mocked_session: AsyncSession
):
    event_id = uuid4()
    mocked_session.execute = AsyncMock()
    mocked_session.commit = AsyncMock()

    await event_service.mark_published(event_id)

    mocked_session.execute.assert_called_once()
    mocked_session.commit.assert_called_once()


async def test_get_unpublished(
    event_service: EventService, mocked_session: AsyncSession
):
    created_after = datetime(2025, 1, 1, tzinfo=timezone.utc)
    orm_events = [
        make_orm_event(order_id="ord-1", published_to_kafka=False),
    ]
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = orm_events
    mocked_session.execute = AsyncMock(return_value=result_mock)

    result = await event_service.get_unpublished(created_after=created_after, limit=10)

    assert len(result) == 1
    assert result[0].order_id == "ord-1"
    mocked_session.execute.assert_called_once()
