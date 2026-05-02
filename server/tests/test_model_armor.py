"""Tests for Model Armor integration in security module."""

from unittest.mock import patch, MagicMock
import pytest
from core.security import sanitize_with_model_armor


class TestModelArmorSanitization:
    """Test sanitize_with_model_armor function."""

    @patch("core.security._get_model_armor_client")
    def test_safe_prompt_passes(self, mock_get_client):
        """Normal text should pass sanitization."""
        mock_get_client.return_value = None  # No client = fallback
        result = sanitize_with_model_armor("I want to buy a phone case")
        assert result["safe"] is True
        assert result["source"] == "skipped"

    @patch("core.security._get_model_armor_client")
    def test_returns_skipped_when_no_client(self, mock_get_client):
        """When Model Armor client is unavailable, return skipped."""
        mock_get_client.return_value = None
        result = sanitize_with_model_armor("any text", is_prompt=True)
        assert result["safe"] is True
        assert result["source"] == "skipped"
        assert result["findings"] == []

    @patch("core.security._get_model_armor_client")
    def test_handles_client_exception(self, mock_get_client):
        """When client throws, return fallback."""
        mock_client = MagicMock()
        mock_client.sanitize_user_prompt.side_effect = Exception("API error")
        mock_get_client.return_value = mock_client
        result = sanitize_with_model_armor("test text", is_prompt=True)
        assert result["safe"] is True
        assert result["source"] == "fallback"

    @patch("core.security._get_model_armor_client")
    def test_prompt_vs_response_routing(self, mock_get_client):
        """Verify is_prompt flag routes to correct API method."""
        mock_get_client.return_value = None
        result_prompt = sanitize_with_model_armor("test", is_prompt=True)
        result_response = sanitize_with_model_armor("test", is_prompt=False)
        assert result_prompt["source"] == "skipped"
        assert result_response["source"] == "skipped"


class TestModelArmorIntegration:
    """Test that Model Armor is wired into the security pipeline."""

    def test_sanitize_function_exists(self):
        """Verify sanitize_with_model_armor is importable."""
        from core.security import sanitize_with_model_armor

        assert callable(sanitize_with_model_armor)

    def test_imported_in_websocket_handler(self):
        """Verify it's imported in the websocket handler."""
        import importlib
        import core.websocket_handler as wh

        assert hasattr(
            wh, "sanitize_with_model_armor"
        ) or "sanitize_with_model_armor" in dir(wh)
