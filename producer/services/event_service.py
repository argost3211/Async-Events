import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.schema.events import Event as EventORM
from producer.domain.events import Event


class EventService:
    def __init__(self, session: AsyncSession):
        self._db = session

    @staticmethod
    def _to_domain(orm: EventORM) -> Event:
        return Event(
            id=orm.id,
            order_id=orm.order_id,
            user_id=orm.user_id,
            event_type=orm.event_type,
            created_at=orm.created_at,
            event_occurred_at=orm.event_occurred_at,
            published_to_kafka=orm.published_to_kafka,
        )

    async def create_event(
        self,
        order_id: str,
        user_id: str,
        event_type: str,
        event_occurred_at: datetime,
    ) -> Event:
        orm_event = EventORM(
            order_id=order_id,
            user_id=user_id,
            event_type=event_type,
            event_occurred_at=event_occurred_at,
            published_to_kafka=False,
        )
        async with self._db.begin():
            self._db.add(orm_event)
        await self._db.refresh(orm_event)
        return self._to_domain(orm_event)

    async def get_event(self, event_id: str) -> Event | None:
        try:
            uid = uuid.UUID(event_id)
        except ValueError:
            return None
        result = await self._db.execute(select(EventORM).where(EventORM.id == uid))
        orm_event = result.scalars().first()
        return self._to_domain(orm_event) if orm_event else None

    async def get_all_events(self) -> list[Event]:
        result = await self._db.execute(select(EventORM))
        return [self._to_domain(orm) for orm in result.scalars().all()]

    async def mark_published(self, event_id: uuid.UUID) -> None:
        await self._db.execute(
            update(EventORM)
            .where(EventORM.id == event_id)
            .values(published_to_kafka=True)
        )
        await self._db.commit()

    async def get_unpublished(self, created_after: datetime, limit: int) -> list[Event]:
        result = await self._db.execute(
            select(EventORM)
            .where(EventORM.published_to_kafka.is_(False))
            .where(EventORM.created_at >= created_after)
            .order_by(EventORM.created_at)
            .limit(limit)
        )
        return [self._to_domain(orm) for orm in result.scalars().all()]
