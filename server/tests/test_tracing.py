"""Tests for Cloud Trace / OpenTelemetry integration."""

import pytest


class TestTracingSetup:
    """Test tracing initialization."""

    def test_init_tracing_importable(self):
        """Verify init_tracing function exists."""
        from core.observability import init_tracing

        assert callable(init_tracing)

    def test_get_tracer_importable(self):
        """Verify get_tracer function exists."""
        from core.observability import get_tracer

        assert callable(get_tracer)

    def test_init_tracing_does_not_crash(self):
        """init_tracing should not raise even without Cloud Trace access."""
        from core.observability import init_tracing

        init_tracing("test-service")

    def test_get_tracer_returns_tracer(self):
        """get_tracer should return a tracer object after init."""
        from core.observability import init_tracing, get_tracer

        init_tracing("test-service")
        tracer = get_tracer()
        assert tracer is not None
