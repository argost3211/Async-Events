from typing import AsyncGenerator, List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from producer.core.metrics import EVENTS_DB_WRITTEN, EVENTS_RECEIVED
from producer.db.engine import AsyncSessionLocal
from producer.models.events import EventCreate, EventRead
from producer.services.event_service import EventService
from producer.services.publish_after_response import publish_event_after_response

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


@router.post("/events", response_model=EventRead, status_code=201)
async def create_event(
    event: EventCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    service: EventService = Depends(get_event_service),
) -> EventRead:
    EVENTS_RECEIVED.inc()
    domain_event = await service.create_event(
        order_id=event.order_id,
        user_id=event.user_id,
        event_type=event.event_type,
        event_occurred_at=event.event_occurred_at,
    )
    EVENTS_DB_WRITTEN.inc()
    kafka_client = getattr(request.app.state, "kafka_client", None)
    if kafka_client is not None:
        background_tasks.add_task(
            publish_event_after_response, domain_event, kafka_client
        )
    return EventRead.from_domain(domain_event)


@router.get("/events", response_model=List[EventRead])
async def get_events(
    service: EventService = Depends(get_event_service),
) -> List[EventRead]:
    events = await service.get_all_events()
    return [EventRead.from_domain(e) for e in events]


@router.get("/events/{event_id}", response_model=EventRead)
async def get_event(
    event_id: str, service: EventService = Depends(get_event_service)
) -> EventRead:
    event = await service.get_event(event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    return EventRead.from_domain(event)
