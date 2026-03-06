import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from producer.db.schema.events import Event


class EventService:
    def __init__(self, session: AsyncSession):
        self._db = session

    async def create_event(
        self,
        order_id: str,
        user_id: str,
        event_type: str,
        event_occurred_at: datetime,
    ) -> Event:
        event = Event(
            order_id=order_id,
            user_id=user_id,
            event_type=event_type,
            event_occurred_at=event_occurred_at,
            published_to_kafka=False,
        )
        async with self._db.begin():
            self._db.add(event)
        await self._db.refresh(event)
        return event

    async def get_event(self, event_id: str) -> Event | None:
        try:
            uid = uuid.UUID(event_id)
        except ValueError:
            return None
        result = await self._db.execute(select(Event).where(Event.id == uid))
        return result.scalars().first()

    async def get_all_events(self) -> list[Event]:
        result = await self._db.execute(select(Event))
        return list(result.scalars().all())
