"""Tests for cost tracker module."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.cost_tracker import CostTracker


class TestCostTracker:
    def test_record_llm_call(self):
        tracker = CostTracker()
        tracker.record_llm_call(
            "sess-1", "gemini-2.5-flash", input_tokens=1000, output_tokens=500
        )
        cost = tracker.get_session_cost("sess-1")
        assert cost["total_cost_usd"] > 0

    def test_record_image_generation(self):
        tracker = CostTracker()
        tracker.record_image_generation(
            "sess-1", "imagen-4.0-ultra-generate-001", count=2
        )
        cost = tracker.get_session_cost("sess-1")
        assert cost["total_cost_usd"] == 0.12  # 2 * 0.06

    def test_multiple_calls_accumulate(self):
        tracker = CostTracker()
        tracker.record_llm_call(
            "sess-1", "gemini-2.5-flash", input_tokens=100, output_tokens=50
        )
        tracker.record_llm_call(
            "sess-1", "gemini-2.5-flash", input_tokens=200, output_tokens=100
        )
        cost = tracker.get_session_cost("sess-1")
        assert cost["models"]["gemini-2.5-flash"]["count"] == 2

    def test_separate_sessions(self):
        tracker = CostTracker()
        tracker.record_llm_call(
            "sess-1", "gemini-2.5-flash", input_tokens=1000, output_tokens=500
        )
        tracker.record_llm_call(
            "sess-2", "gemini-2.5-flash", input_tokens=2000, output_tokens=1000
        )
        cost1 = tracker.get_session_cost("sess-1")
        cost2 = tracker.get_session_cost("sess-2")
        assert cost2["total_cost_usd"] > cost1["total_cost_usd"]

    def test_unknown_session(self):
        tracker = CostTracker()
        cost = tracker.get_session_cost("nonexistent")
        assert cost["total_cost_usd"] == 0.0

    def test_global_stats(self):
        tracker = CostTracker()
        tracker.record_llm_call(
            "s1", "gemini-2.5-flash", input_tokens=100, output_tokens=50
        )
        tracker.record_image_generation("s2", "imagen-4.0-ultra-generate-001")
        stats = tracker.get_global_stats()
        assert stats["total_cost_usd"] > 0
        assert stats["active_sessions"] == 2

    def test_cleanup_session(self):
        tracker = CostTracker()
        tracker.record_llm_call(
            "sess-1", "gemini-2.5-flash", input_tokens=100, output_tokens=50
        )
        report = tracker.cleanup_session("sess-1")
        assert report is not None
        assert report["total_cost_usd"] > 0
        assert tracker.get_session_cost("sess-1")["total_cost_usd"] == 0.0
