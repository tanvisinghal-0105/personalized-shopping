"""
Retry decorators with exponential backoff for external API calls.

Provides resilient wrappers for Vertex AI, Imagen, GCS, and Firestore
operations. Inspired by the brandcanvas retry patterns.
"""

import logging
import functools
import time
from typing import Callable, TypeVar, Any

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Retryable error status codes
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _is_retryable(error: Exception) -> bool:
    """Check if an error is retryable."""
    error_str = str(error).lower()
    retryable_patterns = [
        "429",
        "503",
        "504",
        "rate limit",
        "quota",
        "resource exhausted",
        "service unavailable",
        "deadline exceeded",
        "internal server error",
        "temporarily unavailable",
    ]
    return any(pattern in error_str for pattern in retryable_patterns)


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    multiplier: float = 2.0,
    retryable_check: Callable = _is_retryable,
):
    """Decorator for retrying functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        multiplier: Backoff multiplier
        retryable_check: Function to check if error is retryable
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = initial_delay
            last_error = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt == max_retries or not retryable_check(e):
                        logger.error(
                            f"[RETRY] {func.__name__} failed after {attempt + 1} attempts: {e}"
                        )
                        raise
                    logger.warning(
                        f"[RETRY] {func.__name__} attempt {attempt + 1}/{max_retries} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    delay = min(delay * multiplier, max_delay)

            raise last_error  # Should not reach here

        return wrapper

    return decorator


# Pre-configured decorators for common use cases
vertex_ai_retry = retry_with_backoff(max_retries=3, initial_delay=2.0, max_delay=30.0)
imagen_retry = retry_with_backoff(max_retries=2, initial_delay=3.0, max_delay=60.0)
firestore_retry = retry_with_backoff(max_retries=3, initial_delay=0.5, max_delay=10.0)
gcs_retry = retry_with_backoff(max_retries=3, initial_delay=1.0, max_delay=15.0)


def classify_error(error: Exception) -> str:
    """Classify an error for structured logging and monitoring.

    Returns a category string for dashboards and alerting.
    """
    error_str = str(error).lower()

    if "429" in error_str or "rate limit" in error_str or "quota" in error_str:
        return "rate_limited"
    elif "401" in error_str or "403" in error_str or "unauthorized" in error_str:
        return "auth_error"
    elif "404" in error_str or "not found" in error_str:
        return "not_found"
    elif "timeout" in error_str or "deadline" in error_str:
        return "timeout"
    elif "503" in error_str or "unavailable" in error_str:
        return "service_unavailable"
    elif "connection" in error_str:
        return "connection_error"
    elif "reauthentication" in error_str or "refresh" in error_str:
        return "credentials_expired"
    else:
        return "internal_error"
