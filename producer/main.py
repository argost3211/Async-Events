from fastapi import FastAPI

from producer.api.v1.events import router as event_router
from producer.core.logging import setup_logging

setup_logging()

app = FastAPI()

app.include_router(event_router)
