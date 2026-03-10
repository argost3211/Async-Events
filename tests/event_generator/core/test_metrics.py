from event_generator.core.metrics import EVENTS_PER_SECOND_TARGET, metrics_content


def test_metrics_content_returns_bytes():
    content = metrics_content()
    assert isinstance(content, bytes)


def test_metrics_content_includes_generator_metrics():
    content = metrics_content().decode("utf-8")
    assert "generator_events_sent_total" in content
    assert "generator_producer_response_duration_seconds" in content
    assert "generator_events_per_second_target" in content


def test_events_per_second_target_can_be_set():
    EVENTS_PER_SECOND_TARGET.set(42.0)
    content = metrics_content().decode("utf-8")
    assert "generator_events_per_second_target" in content
    assert "42.0" in content
