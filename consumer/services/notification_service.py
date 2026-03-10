from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.schema.notifications import Notification as NotificationORM
from consumer.domain.notifications import Notification


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    @staticmethod
    def _to_domain(orm: NotificationORM) -> Notification:
        return Notification(
            id=orm.id,
            user_id=orm.user_id,
            order_id=orm.order_id,
            event_type=orm.event_type,
            message=orm.message,
            created_at=orm.created_at,
        )

    async def exists(self, order_id: str, event_type: str) -> bool:
        result = await self._db.execute(
            select(NotificationORM.id)
            .where(
                NotificationORM.order_id == order_id,
                NotificationORM.event_type == event_type,
            )
            .limit(1)
        )
        return result.scalar() is not None

    async def create_notification(
        self,
        user_id: str,
        order_id: str,
        event_type: str,
        message: str,
    ) -> Notification:
        orm_notification = NotificationORM(
            user_id=user_id,
            order_id=order_id,
            event_type=event_type,
            message=message,
        )
        self._db.add(orm_notification)
        await self._db.flush()
        await self._db.refresh(orm_notification)
        await self._db.commit()
        return self._to_domain(orm_notification)
