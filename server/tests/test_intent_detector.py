"""Tests for IntentDetector."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.agents.retail.intent_detector import IntentDetector


class TestDetectHomeDecorIntent:
    def test_detects_redesign_bedroom(self):
        msg = "I need help redesigning Mila's bedroom. She's starting school soon."
        assert IntentDetector.detect_home_decor_intent(msg) is True

    def test_detects_decorate_living_room(self):
        msg = "Can you help me decorate my living room?"
        assert IntentDetector.detect_home_decor_intent(msg) is True

    def test_detects_style_office(self):
        msg = "I want to style my office in a modern way"
        assert IntentDetector.detect_home_decor_intent(msg) is True

    def test_rejects_greeting(self):
        msg = "Hello!"
        assert IntentDetector.detect_home_decor_intent(msg) is False

    def test_rejects_weather(self):
        msg = "What's the weather like today?"
        assert IntentDetector.detect_home_decor_intent(msg) is False

    def test_rejects_empty(self):
        assert IntentDetector.detect_home_decor_intent("") is False

    def test_rejects_none(self):
        assert IntentDetector.detect_home_decor_intent(None) is False

    def test_rejects_introduction(self):
        msg = "My name is Tanvi and I'm looking around"
        assert IntentDetector.detect_home_decor_intent(msg) is False

    def test_detects_transform_space(self):
        msg = "I would like to transform this space into something modern"
        assert IntentDetector.detect_home_decor_intent(msg) is True


class TestExtractRoomType:
    def test_extracts_bedroom(self):
        msg = "I need help redesigning Mila's bedroom"
        assert IntentDetector.extract_room_type(msg) == "bedroom"

    def test_extracts_living_room(self):
        msg = "Can you decorate my living room?"
        assert IntentDetector.extract_room_type(msg) == "living room"

    def test_extracts_office(self):
        msg = "I want to style my home office"
        assert IntentDetector.extract_room_type(msg) == "office"

    def test_extracts_kitchen(self):
        msg = "Help me redesign the kitchen"
        assert IntentDetector.extract_room_type(msg) == "kitchen"

    def test_returns_none_for_no_room(self):
        msg = "I want to redecorate something"
        assert IntentDetector.extract_room_type(msg) is None

    def test_returns_none_for_empty(self):
        assert IntentDetector.extract_room_type("") is None
