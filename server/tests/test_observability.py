"""Tests for observability module."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.observability import HealthStatus, MetricsCollector


class TestHealthStatus:
    def test_register_and_update(self):
        health = HealthStatus()
        health.register("firestore")
        health.update("firestore", True, "connected")
        status = health.get_status()
        assert status["status"] == "healthy"
        assert status["components"]["firestore"]["status"] == "healthy"

    def test_unhealthy_component(self):
        health = HealthStatus()
        health.register("firestore")
        health.update("firestore", False, "connection timeout")
        status = health.get_status()
        assert status["status"] == "degraded"

    def test_mixed_health(self):
        health = HealthStatus()
        health.update("firestore", True)
        health.update("vertex_ai", False, "quota exceeded")
        status = health.get_status()
        assert status["status"] == "degraded"
        assert status["components"]["firestore"]["status"] == "healthy"
        assert status["components"]["vertex_ai"]["status"] == "unhealthy"


class TestMetricsCollector:
    def test_increment_counter(self):
        metrics = MetricsCollector()
        metrics.increment("total_requests")
        metrics.increment("total_requests")
        result = metrics.get_metrics()
        assert result["counters"]["total_requests"] == 2

    def test_record_latency(self):
        metrics = MetricsCollector()
        metrics.record_latency("tool_call", 100.0)
        metrics.record_latency("tool_call", 200.0)
        metrics.record_latency("tool_call", 300.0)
        result = metrics.get_metrics()
        assert result["latencies"]["tool_call"]["avg_ms"] == 200.0
        assert result["latencies"]["tool_call"]["count"] == 3

    def test_record_error(self):
        metrics = MetricsCollector()
        metrics.increment("total_requests", 100)
        metrics.record_error("timeout")
        metrics.record_error("timeout")
        metrics.record_error("auth_error")
        result = metrics.get_metrics()
        assert result["errors"]["timeout"] == 2
        assert result["errors"]["auth_error"] == 1
        assert result["error_rate_pct"] == 3.0

    def test_uptime(self):
        metrics = MetricsCollector()
        result = metrics.get_metrics()
        assert result["uptime_seconds"] >= 0

    def test_empty_metrics(self):
        metrics = MetricsCollector()
        result = metrics.get_metrics()
        assert result["error_rate_pct"] == 0
        assert len(result["latencies"]) == 0
