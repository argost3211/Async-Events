from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv()


class Config(BaseSettings):
    producer_base_url: str = Field(
        default="http://producer:8000", alias="GENERATOR_PRODUCER_BASE_URL"
    )
    events_per_second: float = Field(default=10.0, alias="GENERATOR_EVENTS_PER_SECOND")
    active_orders: int = Field(default=100, alias="GENERATOR_ACTIVE_ORDERS")
    duplicate_probability: float = Field(
        default=0.1, alias="GENERATOR_DUPLICATE_PROBABILITY"
    )
    min_delay_ms: int = Field(default=100, alias="GENERATOR_MIN_DELAY_MS")
    max_delay_ms: int = Field(default=1000, alias="GENERATOR_MAX_DELAY_MS")
    health_retry_seconds: int = Field(default=2, alias="GENERATOR_HEALTH_RETRY_SECONDS")
    health_retry_attempts: int = Field(
        default=30, alias="GENERATOR_HEALTH_RETRY_ATTEMPTS"
    )
    cancel_probability: float = Field(default=0.1, alias="GENERATOR_CANCEL_PROBABILITY")
    metrics_port: int = Field(default=8002, alias="GENERATOR_METRICS_PORT")


config = Config()
