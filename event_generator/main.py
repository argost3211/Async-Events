import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import Response

from event_generator.core.config import config
from event_generator.core.logging import setup_logging
from event_generator.core.metrics import metrics_content
from event_generator.jobs.generator_job import run_generator

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(run_generator())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(lifespan=lifespan)


@app.get("/metrics")
async def metrics() -> Response:
    return Response(
        content=metrics_content(),
        media_type="text/plain; charset=utf-8",
    )


def main() -> None:
    import uvicorn

    uvicorn.run(
        "event_generator.main:app",
        host="0.0.0.0",
        port=config.metrics_port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
