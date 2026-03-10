from prometheus_client import Counter, generate_latest

MESSAGES_CONSUMED = Counter(
    "consumer_messages_consumed_total",
    "Total messages consumed from Kafka",
)
NOTIFICATIONS_CREATED = Counter(
    "consumer_notifications_created_total",
    "Total notifications created",
)


def metrics_content() -> bytes:
    return generate_latest()
