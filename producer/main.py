import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import Response

from producer.api.v1.events import router as event_router
from producer.services.kafka_client import KafkaClient
from producer.core.logging import setup_logging
from producer.core.metrics import metrics_content
from producer.jobs.republish_job import run_republish_loop

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.kafka_client = None
    kafka_client = KafkaClient()
    try:
        await kafka_client.connect()
    except Exception:
        yield
        return
    app.state.kafka_client = kafka_client
    task = asyncio.create_task(run_republish_loop(kafka_client))
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        await kafka_client.disconnect()


app = FastAPI(lifespan=lifespan)

app.include_router(event_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics")
async def metrics() -> Response:
    return Response(
        content=metrics_content(),
        media_type="text/plain; charset=utf-8",
    )
