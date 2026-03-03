
from fastapi import FastAPI

from producer.core.logging import setup_logging


setup_logging()

app = FastAPI()



