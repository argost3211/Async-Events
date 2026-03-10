import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import Response

from consumer.core.config import config
from consumer.core.logging import setup_logging
from consumer.core import metrics as consumer_metrics
from consumer.core.templates import render_message
from consumer.db.engine import AsyncSessionLocal
from consumer.models.events import EventMessage
from consumer.services.kafka_consumer import KafkaConsumerClient
from consumer.services.notification_service import NotificationService
from consumer.use_cases.process_order_event import ProcessOrderEventUseCase

setup_logging()


async def _message_handler(msg: EventMessage) -> None:
    async with AsyncSessionLocal() as session:
        notification_service = NotificationService(session)
        use_case = ProcessOrderEventUseCase(
            notification_repo=notification_service,
            message_renderer=render_message,
        )
        result = await use_case.execute(
            event_id=msg.event_id,
            order_id=msg.order_id,
            user_id=msg.user_id,
            event_type=msg.event_type,
            event_occurred_at=msg.event_occurred_at,
        )
        if not result.skipped:
            consumer_metrics.NOTIFICATIONS_CREATED.inc()


@asynccontextmanager
async def lifespan(app: FastAPI):
    kafka_client = KafkaConsumerClient()
    try:
        await kafka_client.connect()
    except Exception:
        yield
        return
    consumer_task = asyncio.create_task(kafka_client.consume_loop(_message_handler))
    try:
        yield
    finally:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
        await kafka_client.disconnect()


app = FastAPI(lifespan=lifespan)


@app.get("/metrics")
async def metrics() -> Response:
    return Response(
        content=consumer_metrics.metrics_content(),
        media_type="text/plain; charset=utf-8",
    )


def run() -> None:
    import uvicorn

    uvicorn.run(
        "consumer.main:app",
        host="0.0.0.0",
        port=config.consumer_metrics_port,
        log_level="info",
    )


if __name__ == "__main__":
    run()
