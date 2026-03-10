from datetime import datetime, timezone
from uuid import UUID, uuid4

from consumer.domain.notifications import Notification
from consumer.models.events import EventMessage


def make_orm_notification(
    *,
    id: UUID | None = None,
    user_id: str = "user-1",
    order_id: str = "order-1",
    event_type: str = "order_created",
    message: str = "Заказ order-1 создан",
    created_at: datetime | None = None,
):
    """Создаёт ORM Notification для тестов уровня репозитория."""
    from shared.db.schema.notifications import Notification as NotificationORM

    n = NotificationORM(
        user_id=user_id,
        order_id=order_id,
        event_type=event_type,
        message=message,
    )
    n.id = id or uuid4()
    n.created_at = created_at or datetime.now(timezone.utc)
    return n


def make_notification(
    *,
    id: str | None = None,
    user_id: str = "user-1",
    order_id: str = "order-1",
    event_type: str = "order_created",
    message: str = "Заказ order-1 создан",
    created_at: datetime | None = None,
) -> Notification:
    return Notification(
        id=uuid4() if id is None else UUID(id),
        user_id=user_id,
        order_id=order_id,
        event_type=event_type,
        message=message,
        created_at=created_at or datetime.now(timezone.utc),
    )


def make_order_event_message(
    *,
    event_id: str = "e1",
    order_id: str = "order-1",
    user_id: str = "user-1",
    event_type: str = "order_created",
    event_occurred_at: datetime | None = None,
) -> EventMessage:
    return EventMessage(
        event_id=event_id,
        order_id=order_id,
        user_id=user_id,
        event_type=event_type,
        event_occurred_at=event_occurred_at or datetime.now(timezone.utc),
    )
