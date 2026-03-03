from typing import AsyncGenerator, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from producer.models.events import EventCreate, EventRead
from producer.services.event_service import EventService
from producer.db.engine import AsyncSessionLocal

router = APIRouter(prefix="/api/v1")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_event_service(
    session: AsyncSession = Depends(get_session),
) -> EventService:
    return EventService(session=session)


@router.post("/events", response_model=EventRead)
async def create_event(
    event: EventCreate, service: EventService = Depends(get_event_service)
) -> EventRead:
    event_model = await service.create_event(event.type, event.message)
    return EventRead(
        id=str(event_model.id),
        type=event_model.type,
        message=event_model.message,
        created_at=event_model.created_at,
    )


@router.get("/events", response_model=List[EventRead])
async def get_events(
    service: EventService = Depends(get_event_service),
) -> List[EventRead]:
    events = await service.get_all_events()
    return [
        EventRead(
            id=str(em.id), type=em.type, message=em.message, created_at=em.created_at
        )
        for em in events
    ]


@router.get("/events/{event_id}", response_model=EventRead)
async def get_event(
    event_id: str, service: EventService = Depends(get_event_service)
) -> EventRead:
    event_model = await service.get_event(event_id)
    if event_model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    return EventRead(
        id=str(event_model.id),
        type=event_model.type,
        message=event_model.message,
        created_at=event_model.created_at,
    )
