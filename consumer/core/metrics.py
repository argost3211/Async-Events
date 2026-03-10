from prometheus_client import Counter, Histogram, generate_latest

MESSAGES_CONSUMED = Counter(
    "consumer_messages_consumed_total",
    "Total messages consumed from Kafka",
)
NOTIFICATIONS_CREATED = Counter(
    "consumer_notifications_created_total",
    "Total notifications created",
)
MESSAGES_SKIPPED = Counter(
    "consumer_messages_skipped_total",
    "Total messages skipped (idempotency)",
)
MESSAGE_PROCESSING_DURATION = Histogram(
    "consumer_message_processing_duration_seconds",
    "Time to process one message",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)
RETRIES = Counter(
    "consumer_retries_total",
    "Total retry attempts",
)
DLQ_MESSAGES = Counter(
    "consumer_dlq_messages_total",
    "Total messages sent to DLQ",
)
ERRORS_DB = Counter(
    "consumer_errors_db_total",
    "Total DB errors",
)
ERRORS_KAFKA = Counter(
    "consumer_errors_kafka_total",
    "Total Kafka errors",
)


def metrics_content() -> bytes:
    return generate_latest()
