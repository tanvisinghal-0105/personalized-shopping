"""Tests for evaluation metrics in run_eval.py."""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from evaluation.run_eval import (
    trajectory_order_metric,
    trajectory_args_metric,
    step_skip_metric,
    session_completion_metric,
    moodboard_quality_metric,
    speech_wer_metric,
    speech_latency_metric,
    _word_error_rate,
)


class TestWordErrorRate:
    def test_identical_strings(self):
        assert _word_error_rate("hello world", "hello world") == 0.0

    def test_completely_different(self):
        assert _word_error_rate("hello", "goodbye") == 1.0

    def test_empty_reference(self):
        assert _word_error_rate("", "") == 0.0

    def test_partial_match(self):
        wer = _word_error_rate("the cat sat", "the dog sat")
        assert 0.0 < wer < 1.0


class TestTrajectoryOrderMetric:
    def test_perfect_match(self):
        instance = {
            "predicted_trajectory": [
                {"tool_name": "start_home_decor_consultation"},
                {"tool_name": "continue_home_decor_consultation"},
                {"tool_name": "continue_home_decor_consultation"},
            ]
        }
        result = trajectory_order_metric(instance)
        assert result["trajectory_order_score"] > 0

    def test_empty_trajectory(self):
        result = trajectory_order_metric({"predicted_trajectory": []})
        assert result["trajectory_order_score"] == 0.0

    def test_missing_trajectory(self):
        result = trajectory_order_metric({})
        assert result["trajectory_order_score"] == 0.0


class TestStepSkipMetric:
    def test_all_stages_present(self):
        instance = {
            "tool_calls": [
                {"stage": "stage_1_room_identification"},
                {"stage": "stage_1a_room_purpose"},
                {"stage": "stage_1b_age_context"},
                {"stage": "stage_1c_constraints"},
                {"stage": "stage_1d_photo_request"},
                {"stage": "stage_2_style_discovery"},
                {"stage": "stage_3_color_preferences"},
                {"stage": "stage_4_room_dimensions"},
                {"stage": "moodboard_presented"},
            ]
        }
        result = step_skip_metric(instance)
        assert result["step_skip_score"] == 1.0
        assert result["skipped_stages"] == []

    def test_missing_stages(self):
        instance = {
            "tool_calls": [
                {"stage": "stage_1_room_identification"},
                {"stage": "moodboard_presented"},
            ]
        }
        result = step_skip_metric(instance)
        assert result["step_skip_score"] < 1.0
        assert len(result["skipped_stages"]) > 0

    def test_empty_tool_calls(self):
        result = step_skip_metric({"tool_calls": []})
        assert result["step_skip_score"] == 0.0


class TestSessionCompletionMetric:
    def test_completed_session(self):
        instance = {
            "tool_calls": [{"stage": "moodboard_presented"}],
            "turn_count": 9,
        }
        result = session_completion_metric(instance)
        assert result["session_completion_score"] == 1.0
        assert result["reached_moodboard"] is True

    def test_incomplete_session(self):
        instance = {
            "tool_calls": [{"stage": "stage_2_style_discovery"}],
            "turn_count": 3,
        }
        result = session_completion_metric(instance)
        assert result["session_completion_score"] == 0.0
        assert result["reached_moodboard"] is False


class TestMoodboardQualityMetric:
    def test_no_moodboard(self):
        result = moodboard_quality_metric({"events": [], "tool_calls": []})
        assert result["moodboard_quality_score"] == 0.0

    def test_moodboard_from_tool_call(self):
        instance = {
            "events": [],
            "tool_calls": [
                {
                    "stage": "moodboard_presented",
                    "ui_type": "moodboard",
                    "args": {
                        "style_preferences": ["modern"],
                        "color_preferences": ["blue"],
                    },
                }
            ],
        }
        result = moodboard_quality_metric(instance)
        assert "moodboard_quality_score" in result


class TestSpeechLatencyMetric:
    def test_good_latency(self):
        instance = {
            "events": [
                {"type": "agent_response", "latency_first_byte_ms": 500},
                {"type": "agent_response", "latency_first_byte_ms": 600},
            ]
        }
        result = speech_latency_metric(instance)
        assert result["speech_latency_score"] > 0.5

    def test_no_latency_data(self):
        result = speech_latency_metric({"events": []})
        assert result["speech_latency_score"] == 0.0
