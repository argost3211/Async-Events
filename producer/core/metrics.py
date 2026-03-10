from prometheus_client import Counter, generate_latest

EVENTS_RECEIVED = Counter(
    "producer_events_received_total",
    "Total events received (POST /api/v1/events)",
)
EVENTS_DB_WRITTEN = Counter(
    "producer_events_db_written_total",
    "Total events written to DB",
)
EVENTS_KAFKA_PUBLISHED = Counter(
    "producer_events_kafka_published_total",
    "Total events successfully published to Kafka",
)


def metrics_content() -> bytes:
    return generate_latest()
