from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field

load_dotenv()


class Config(BaseSettings):
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
    kafka_order_events_partitions: int = Field(
        default=3, alias="KAFKA_ORDER_EVENTS_PARTITIONS"
    )
    kafka_order_events_dlq_partitions: int = Field(
        default=1, alias="KAFKA_ORDER_EVENTS_DLQ_PARTITIONS"
    )
    kafka_replication_factor: int = Field(default=1, alias="KAFKA_REPLICATION_FACTOR")
    kafka_connect_retry_seconds: int = Field(
        default=2, alias="KAFKA_CONNECT_RETRY_SECONDS"
    )
    kafka_connect_retry_attempts: int = Field(
        default=30, alias="KAFKA_CONNECT_RETRY_ATTEMPTS"
    )

    republish_interval_seconds: int = Field(
        default=15, alias="REPUBLISH_INTERVAL_SECONDS"
    )
    republish_window_hours: int = Field(default=24, alias="REPUBLISH_WINDOW_HOURS")
    republish_batch_limit: int = Field(default=100, alias="REPUBLISH_BATCH_LIMIT")

    def pg_url(self) -> str:
        return f"postgresql+asyncpg://{self.pg_user}:{self.pg_password}@{self.pg_host}:{self.pg_port}/{self.pg_db}"


config = Config()
