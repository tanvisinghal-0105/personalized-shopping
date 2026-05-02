"""Tests for HomeDecorSessionState."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.agents.retail.session_state import HomeDecorSessionState


@pytest.fixture
def state_manager():
    return HomeDecorSessionState()


class TestCreateSession:
    def test_creates_session(self, state_manager):
        state_manager.create_session("CY-1234", "DECOR-001")
        session = state_manager.get_session("DECOR-001")
        assert session is not None
        assert session["session_id"] == "DECOR-001"

    def test_session_has_empty_collected_data(self, state_manager):
        state_manager.create_session("CY-1234", "DECOR-001")
        session = state_manager.get_session("DECOR-001")
        collected = session["collected_data"]
        assert collected["room_type"] is None
        assert collected["style_preferences"] is None
        assert collected["color_preferences"] is None
        assert collected["room_photos_analyzed"] is False


class TestUpdateSession:
    def test_updates_room_type(self, state_manager):
        state_manager.create_session("CY-1234", "DECOR-001")
        state_manager.update_session("DECOR-001", room_type="bedroom")
        session = state_manager.get_session("DECOR-001")
        assert session["collected_data"]["room_type"] == "bedroom"

    def test_none_does_not_overwrite(self, state_manager):
        state_manager.create_session("CY-1234", "DECOR-001")
        state_manager.update_session("DECOR-001", room_type="bedroom")
        state_manager.update_session("DECOR-001", room_type=None)
        session = state_manager.get_session("DECOR-001")
        assert session["collected_data"]["room_type"] == "bedroom"

    def test_updates_multiple_fields(self, state_manager):
        state_manager.create_session("CY-1234", "DECOR-001")
        state_manager.update_session(
            "DECOR-001",
            room_type="bedroom",
            room_purpose="redesign",
            age_context="school-age",
        )
        session = state_manager.get_session("DECOR-001")
        assert session["collected_data"]["room_type"] == "bedroom"
        assert session["collected_data"]["room_purpose"] == "redesign"
        assert session["collected_data"]["age_context"] == "school-age"

    def test_returns_none_for_missing_session(self, state_manager):
        result = state_manager.update_session("NONEXISTENT", room_type="bedroom")
        assert result is None


class TestGetCustomerSession:
    def test_returns_session_by_customer(self, state_manager):
        state_manager.create_session("CY-1234", "DECOR-001")
        session = state_manager.get_customer_session("CY-1234")
        assert session is not None
        assert session["session_id"] == "DECOR-001"

    def test_returns_none_for_unknown_customer(self, state_manager):
        assert state_manager.get_customer_session("CY-UNKNOWN") is None


class TestMarkMoodboardGenerated:
    def test_marks_moodboard(self, state_manager):
        state_manager.create_session("CY-1234", "DECOR-001")
        state_manager.mark_moodboard_generated("DECOR-001")
        session = state_manager.get_session("DECOR-001")
        assert session["moodboard_generated"] is True
