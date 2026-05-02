"""Tests for retry module."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.retry import retry_with_backoff, classify_error, _is_retryable


class TestIsRetryable:
    def test_rate_limit_is_retryable(self):
        assert _is_retryable(Exception("429 Too Many Requests")) is True

    def test_quota_is_retryable(self):
        assert _is_retryable(Exception("Resource exhausted")) is True

    def test_service_unavailable_is_retryable(self):
        assert _is_retryable(Exception("503 Service Unavailable")) is True

    def test_not_found_is_not_retryable(self):
        assert _is_retryable(Exception("404 Not Found")) is False

    def test_auth_error_is_not_retryable(self):
        assert _is_retryable(Exception("401 Unauthorized")) is False


class TestClassifyError:
    def test_rate_limited(self):
        assert classify_error(Exception("429 rate limit")) == "rate_limited"

    def test_auth_error(self):
        assert classify_error(Exception("403 forbidden")) == "auth_error"

    def test_timeout(self):
        assert classify_error(Exception("deadline exceeded")) == "timeout"

    def test_credentials_expired(self):
        assert (
            classify_error(Exception("Reauthentication is needed"))
            == "credentials_expired"
        )

    def test_not_found(self):
        assert classify_error(Exception("404 not found")) == "not_found"

    def test_internal_error(self):
        assert classify_error(Exception("something broke")) == "internal_error"


class TestRetryDecorator:
    def test_succeeds_on_first_try(self):
        call_count = 0

        @retry_with_backoff(max_retries=3, initial_delay=0.01)
        def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = succeed()
        assert result == "ok"
        assert call_count == 1

    def test_retries_on_retryable_error(self):
        call_count = 0

        @retry_with_backoff(max_retries=3, initial_delay=0.01)
        def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("503 Service Unavailable")
            return "ok"

        result = fail_then_succeed()
        assert result == "ok"
        assert call_count == 3

    def test_raises_after_max_retries(self):
        @retry_with_backoff(max_retries=2, initial_delay=0.01)
        def always_fail():
            raise Exception("503 Service Unavailable")

        with pytest.raises(Exception, match="503"):
            always_fail()

    def test_no_retry_on_non_retryable(self):
        call_count = 0

        @retry_with_backoff(max_retries=3, initial_delay=0.01)
        def fail_auth():
            nonlocal call_count
            call_count += 1
            raise Exception("401 Unauthorized")

        with pytest.raises(Exception, match="401"):
            fail_auth()
        assert call_count == 1
