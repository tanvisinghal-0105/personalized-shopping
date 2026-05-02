"""Tests for authentication module."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.auth import authenticate_websocket, ALLOWED_DOMAINS


class TestAuthDisabled:
    """When AUTH_ENABLED=false, all requests should pass."""

    def test_returns_dev_user_when_disabled(self):
        result = authenticate_websocket({})
        assert result is not None
        assert result["auth"] == "disabled"

    def test_returns_email_when_disabled(self):
        result = authenticate_websocket({})
        assert "email" in result

    def test_empty_headers_pass_when_disabled(self):
        result = authenticate_websocket({})
        assert result is not None


class TestAllowedDomains:
    def test_google_is_allowed(self):
        assert "google.com" in ALLOWED_DOMAINS

    def test_random_domain_not_allowed(self):
        assert "random.com" not in ALLOWED_DOMAINS
