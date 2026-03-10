from typing import AsyncGenerator, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from producer.core.metrics import (
    EVENTS_DB_WRITTEN,
    EVENTS_KAFKA_PUBLISHED,
    EVENTS_RECEIVED,
)
from producer.models.events import EventCreate, EventRead
from producer.services.event_service import EventService
from producer.use_cases import CreateOrderEventUseCase
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


def get_create_event_use_case(
    request: Request,
    event_service: EventService = Depends(get_event_service),
) -> CreateOrderEventUseCase:
    kafka_client = getattr(request.app.state, "kafka_client", None)
    return CreateOrderEventUseCase(event_service, kafka_client)


@router.post("/events", response_model=EventRead, status_code=201)
async def create_event(
    event: EventCreate,
    use_case: CreateOrderEventUseCase = Depends(get_create_event_use_case),
) -> EventRead:
    EVENTS_RECEIVED.inc()
    result = await use_case.execute(
        order_id=event.order_id,
        user_id=event.user_id,
        event_type=event.event_type,
        event_occurred_at=event.event_occurred_at,
    )
    EVENTS_DB_WRITTEN.inc()
    if result.published:
        EVENTS_KAFKA_PUBLISHED.inc()

    return EventRead.from_domain(result.event)


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
