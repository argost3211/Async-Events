from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field

load_dotenv()


class ConsumerConfig(BaseSettings):
    debug: bool = False
    pg_host: str = Field(alias="POSTGRES_HOST")
    pg_port: int = Field(alias="POSTGRES_PORT")
    pg_user: str = Field(alias="POSTGRES_USER")
    pg_password: str = Field(alias="POSTGRES_PASSWORD")
    pg_db: str = Field(alias="POSTGRES_DB")

    kafka_bootstrap_servers: str = Field(
        default="localhost:9092", alias="KAFKA_BOOTSTRAP_SERVERS"
    )
    kafka_order_events_topic: str = Field(
        default="order-events", alias="KAFKA_ORDER_EVENTS_TOPIC"
    )
    kafka_order_events_dlq_topic: str = Field(
        default="order-events-dlq", alias="KAFKA_ORDER_EVENTS_DLQ_TOPIC"
    )
    kafka_connect_retry_seconds: int = Field(
        default=2, alias="KAFKA_CONNECT_RETRY_SECONDS"
    )
    kafka_connect_retry_attempts: int = Field(
        default=30, alias="KAFKA_CONNECT_RETRY_ATTEMPTS"
    )

    consumer_group_id: str = Field(
        default="order-events-consumer", alias="CONSUMER_GROUP_ID"
    )
    consumer_max_retries: int = Field(default=3, alias="CONSUMER_MAX_RETRIES")
    consumer_retry_base_delay: float = Field(
        default=1.0, alias="CONSUMER_RETRY_BASE_DELAY"
    )
    consumer_retry_max_delay: float = Field(
        default=30.0, alias="CONSUMER_RETRY_MAX_DELAY"
    )
    consumer_metrics_port: int = Field(default=8001, alias="CONSUMER_METRICS_PORT")

    def pg_url(self) -> str:
        return f"postgresql+asyncpg://{self.pg_user}:{self.pg_password}@{self.pg_host}:{self.pg_port}/{self.pg_db}"


config = ConsumerConfig()
