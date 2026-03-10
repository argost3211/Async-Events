from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from consumer.services.notification_service import NotificationService
from tests.consumer.factories import make_orm_notification


async def test_exists_returns_true(mocked_session):
    notification_id = uuid4()
    result_mock = MagicMock()
    result_mock.scalar.return_value = notification_id
    mocked_session.execute = AsyncMock(return_value=result_mock)

    service = NotificationService(mocked_session)
    result = await service.exists(order_id="order-1", event_type="order_created")

    assert result is True
    mocked_session.execute.assert_called_once()


async def test_exists_returns_false(mocked_session):
    result_mock = MagicMock()
    result_mock.scalar.return_value = None
    mocked_session.execute = AsyncMock(return_value=result_mock)

    service = NotificationService(mocked_session)
    result = await service.exists(order_id="order-1", event_type="order_created")

    assert result is False
    mocked_session.execute.assert_called_once()


async def test_create_notification_returns_domain_notification(mocked_session):
    orm_notification = make_orm_notification(
        user_id="user-1",
        order_id="order-1",
        event_type="order_created",
        message="Заказ order-1 создан",
    )
    mocked_session.add = MagicMock()
    mocked_session.flush = AsyncMock()
    mocked_session.refresh = AsyncMock()
    mocked_session.commit = AsyncMock()

    def refresh_side_effect(orm):
        orm.id = orm_notification.id
        orm.created_at = orm_notification.created_at

    mocked_session.refresh = AsyncMock(side_effect=refresh_side_effect)

    service = NotificationService(mocked_session)
    result = await service.create_notification(
        user_id="user-1",
        order_id="order-1",
        event_type="order_created",
        message="Заказ order-1 создан",
    )

    assert result.user_id == "user-1"
    assert result.order_id == "order-1"
    assert result.event_type == "order_created"
    assert result.message == "Заказ order-1 создан"
    mocked_session.add.assert_called_once()
    mocked_session.flush.assert_called_once()
    mocked_session.commit.assert_called_once()
