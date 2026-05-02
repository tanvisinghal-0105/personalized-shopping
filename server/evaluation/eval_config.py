"""
Evaluation configuration for the OTTO Home Decor voice shopping assistant.

Defines the expected conversation trajectory, tool calls, and quality
criteria based on DEMO_STORYLINE.md.
"""

try:
    from core.models import ConsultationStage
except ImportError:
    # Fallback when imported from outside the server package (e.g., CRM)
    from enum import Enum

    class ConsultationStage(str, Enum):
        ROOM_IDENTIFICATION = "stage_1_room_identification"
        ROOM_PURPOSE = "stage_1a_room_purpose"
        AGE_CONTEXT = "stage_1b_age_context"
        CONSTRAINTS = "stage_1c_constraints"
        PHOTO_REQUEST = "stage_1d_photo_request"
        STYLE_DISCOVERY = "stage_2_style_discovery"
        COLOR_PREFERENCES = "stage_3_color_preferences"
        ROOM_DIMENSIONS = "stage_4_room_dimensions"
        MOODBOARD_PRESENTED = "moodboard_presented"


# -- Expected tool call trajectory for the full demo flow --
# The evaluator checks that these tools are called in order.
# Args use "*" for any value, or a specific value for exact match.
EXPECTED_TRAJECTORY = [
    {
        "tool_name": "start_home_decor_consultation",
        "phase": "Phase 1 - Initial Request",
        "required_args": {"customer_id": "*"},
    },
    {
        "tool_name": "continue_home_decor_consultation",
        "phase": "Phase 2 - Room Selection",
        "required_args": {"room_type": "*"},
        "expected_stage": ConsultationStage.ROOM_PURPOSE.value,
    },
    {
        "tool_name": "continue_home_decor_consultation",
        "phase": "Phase 2 - Room Purpose",
        "required_args": {"room_purpose": "*"},
        "expected_stage": ConsultationStage.AGE_CONTEXT.value,
    },
    {
        "tool_name": "continue_home_decor_consultation",
        "phase": "Phase 2 - Age Context",
        "required_args": {"age_context": "*"},
        "expected_stage": ConsultationStage.CONSTRAINTS.value,
    },
    {
        "tool_name": "continue_home_decor_consultation",
        "phase": "Phase 2 - Constraints",
        "required_args": {"constraints": "*"},
        "expected_stage": ConsultationStage.PHOTO_REQUEST.value,
    },
    {
        "tool_name": "continue_home_decor_consultation",
        "phase": "Phase 4 - Style Finder",
        "expected_stage": ConsultationStage.STYLE_DISCOVERY.value,
    },
    {
        "tool_name": "continue_home_decor_consultation",
        "phase": "Phase 4 - Color Preferences",
        "expected_stage": ConsultationStage.COLOR_PREFERENCES.value,
    },
    {
        "tool_name": "continue_home_decor_consultation",
        "phase": "Phase 5 - Room Dimensions",
        "expected_stage": ConsultationStage.ROOM_DIMENSIONS.value,
    },
    {
        "tool_name": "continue_home_decor_consultation",
        "phase": "Phase 6 - Moodboard",
        "expected_stage": ConsultationStage.MOODBOARD_PRESENTED.value,
    },
]

# -- Test utterances mapped to expected intent detection --
INTENT_TEST_CASES = [
    {
        "utterance": "I need help redesigning Mila's bedroom. She's starting school soon and we need a desk, a bigger bed, and more storage.",
        "expected_intent": "home_decor",
        "expected_tool": "start_home_decor_consultation",
    },
    {
        "utterance": "Can you help me decorate my living room?",
        "expected_intent": "home_decor",
        "expected_tool": "start_home_decor_consultation",
    },
    {
        "utterance": "What's the weather like today?",
        "expected_intent": None,
        "expected_tool": None,
    },
    {
        "utterance": "Hello!",
        "expected_intent": None,
        "expected_tool": None,
    },
    {
        "utterance": "I want to style my office in a modern way",
        "expected_intent": "home_decor",
        "expected_tool": "start_home_decor_consultation",
    },
]

# -- Audio quality thresholds --
AUDIO_QUALITY_THRESHOLDS = {
    "max_wer": 0.15,  # Word Error Rate: < 15%
    "max_latency_first_byte_ms": 2000,  # Time to first audio byte: < 2s
    "max_latency_turn_ms": 5000,  # Full turn latency: < 5s
    "min_naturalness_score": 3.5,  # MOS-style 1-5 scale
    "min_relevance_score": 4.0,  # Response relevance 1-5 scale
}

# -- Moodboard quality criteria --
MOODBOARD_CRITERIA = {
    "min_products": 6,
    "max_products": 12,
    "min_furniture_ratio": 0.3,  # At least 30% furniture for redesigns
    "max_furniture_ratio": 0.5,  # At most 50% furniture
    "min_style_match_ratio": 0.6,  # 60% of products should match selected styles
    "min_color_match_ratio": 0.4,  # 40% of products should match selected colours
}

# -- Vertex AI evaluation judge model --
JUDGE_MODEL = "gemini-2.5-flash"
