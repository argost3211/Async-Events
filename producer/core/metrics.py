from prometheus_client import Counter, Histogram, generate_latest

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
ERRORS_DB = Counter(
    "producer_errors_db_total",
    "Total DB write errors",
)
ERRORS_KAFKA = Counter(
    "producer_errors_kafka_total",
    "Total Kafka publish errors",
)
POST_REQUEST_DURATION = Histogram(
    "producer_post_events_duration_seconds",
    "POST /api/v1/events request duration",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0),
)
REPUBLISH_PUBLISHED = Counter(
    "producer_republish_kafka_published_total",
    "Total events republished to Kafka by background job",
)
REPUBLISH_ERRORS = Counter(
    "producer_republish_errors_total",
    "Total republish errors in background job",
)


def metrics_content() -> bytes:
    return generate_latest()
