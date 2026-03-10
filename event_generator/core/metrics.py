from prometheus_client import Counter, Gauge, Histogram, generate_latest

EVENTS_SENT = Counter(
    "generator_events_sent_total",
    "Total events sent to producer",
)
PRODUCER_RESPONSE_DURATION = Histogram(
    "generator_producer_response_duration_seconds",
    "Time waiting for producer HTTP response",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)
EVENTS_PER_SECOND_TARGET = Gauge(
    "generator_events_per_second_target",
    "Target events per second from config",
)


def metrics_content() -> bytes:
    return generate_latest()
