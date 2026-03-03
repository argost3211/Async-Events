from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from producer.db.schema.events import Event


class EventService:
    def __init__(self, session: AsyncSession):
        self._db = session

    async def create_event(self, type: str, message: str | None) -> Event:
        event = Event(type=type, message=message)
        async with self._db.begin():
            self._db.add(event)
        await self._db.refresh(event)
        return event

    async def get_event(self, event_id: str) -> Event | None:
        result = await self._db.execute(select(Event).where(Event.id == event_id))
        return result.scalars().first()

    async def get_all_events(self) -> list[Event]:
        result = await self._db.execute(select(Event))
        return list(result.scalars().all())
