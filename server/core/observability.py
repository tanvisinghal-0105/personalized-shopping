"""
Observability: metrics, health checks, monitoring, and distributed tracing.

Provides:
- Application health status
- Request/response metrics
- Latency tracking
- Error rate monitoring
- Resource usage reporting
- Distributed tracing via OpenTelemetry + Cloud Trace
"""

import time
import logging
import threading
from typing import Dict
from collections import defaultdict

logger = logging.getLogger(__name__)

# OpenTelemetry tracing (lazy-loaded, optional dependency)
_tracer = None


def init_tracing(service_name: str = "shopping-backend") -> None:
    """Initialize OpenTelemetry tracing with Cloud Trace exporter.

    Uses lazy initialization so the server still works if the
    opentelemetry packages are not installed.
    """
    global _tracer
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter

        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(BatchSpanProcessor(CloudTraceSpanExporter()))
        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer(service_name)
        logger.info("OpenTelemetry tracing initialized with Cloud Trace exporter")
    except ImportError:
        logger.warning(
            "OpenTelemetry packages not installed -- tracing disabled. "
            "Install opentelemetry-sdk and opentelemetry-exporter-gcp-trace to enable."
        )
    except Exception as exc:
        logger.warning("Failed to initialize tracing: %s", exc)


def get_tracer():
    """Return the global tracer, or None if tracing is not available."""
    return _tracer


class HealthStatus:
    """Application health checker."""

    def __init__(self):
        self._components = {}
        self._lock = threading.Lock()

    def register(self, name: str, check_fn=None):
        """Register a health check component."""
        with self._lock:
            self._components[name] = {
                "status": "unknown",
                "last_check": None,
                "check_fn": check_fn,
            }

    def update(self, name: str, healthy: bool, detail: str = ""):
        """Update health status of a component."""
        with self._lock:
            self._components[name] = {
                "status": "healthy" if healthy else "unhealthy",
                "detail": detail,
                "last_check": time.time(),
            }

    def get_status(self) -> Dict:
        """Get overall health status."""
        with self._lock:
            components = {}
            all_healthy = True
            for name, comp in self._components.items():
                status = comp.get("status", "unknown")
                if status != "healthy":
                    all_healthy = False
                components[name] = {
                    "status": status,
                    "detail": comp.get("detail", ""),
                }
            return {
                "status": "healthy" if all_healthy else "degraded",
                "components": components,
            }


class MetricsCollector:
    """Collect application metrics for monitoring."""

    def __init__(self):
        self._lock = threading.Lock()
        self._counters = defaultdict(int)
        self._latencies = defaultdict(list)
        self._errors = defaultdict(int)
        self._start_time = time.time()

    def increment(self, metric: str, value: int = 1):
        with self._lock:
            self._counters[metric] += value

    def record_latency(self, operation: str, duration_ms: float):
        with self._lock:
            self._latencies[operation].append(duration_ms)
            # Keep last 1000 samples
            if len(self._latencies[operation]) > 1000:
                self._latencies[operation] = self._latencies[operation][-500:]

    def record_error(self, error_type: str):
        with self._lock:
            self._errors[error_type] += 1
            self._counters["total_errors"] += 1

    def get_metrics(self) -> Dict:
        with self._lock:
            latency_stats = {}
            for op, values in self._latencies.items():
                if values:
                    sorted_vals = sorted(values)
                    latency_stats[op] = {
                        "count": len(values),
                        "avg_ms": round(sum(values) / len(values), 1),
                        "p50_ms": round(sorted_vals[len(sorted_vals) // 2], 1),
                        "p95_ms": round(sorted_vals[int(len(sorted_vals) * 0.95)], 1),
                        "p99_ms": round(sorted_vals[int(len(sorted_vals) * 0.99)], 1),
                    }

            total_requests = self._counters.get("total_requests", 0)
            total_errors = self._counters.get("total_errors", 0)
            error_rate = (
                (total_errors / total_requests * 100) if total_requests > 0 else 0
            )

            return {
                "uptime_seconds": round(time.time() - self._start_time, 1),
                "counters": dict(self._counters),
                "latencies": latency_stats,
                "errors": dict(self._errors),
                "error_rate_pct": round(error_rate, 2),
            }


# Global singletons
_health = HealthStatus()
_metrics = MetricsCollector()


def get_health() -> HealthStatus:
    return _health


def get_metrics() -> MetricsCollector:
    return _metrics
