"""
Evaluation configuration for the OTTO Home Decor voice shopping assistant.

Defines the expected conversation trajectory, tool calls, and quality
criteria based on DEMO_STORYLINE.md.
"""

# -- Expected tool call trajectory for the full demo flow --
# Each entry: (tool_name, critical_args_subset)
# The evaluator checks that these tools are called in order with matching args.
EXPECTED_TRAJECTORY = [
    {
        "tool_name": "start_home_decor_consultation",
        "phase": "Phase 1 - Initial Request",
        "required_args": {"customer_id": "*"},
        "expected_output_keys": ["ui_data"],
        "expected_ui_type": "room_selector",
    },
    {
        "tool_name": "continue_home_decor_consultation",
        "phase": "Phase 2 - Room Purpose",
        "required_args": {"room_type": "bedroom"},
        "expected_stage": "stage_1a_room_purpose",
    },
    {
        "tool_name": "continue_home_decor_consultation",
        "phase": "Phase 2 - Age Context",
        "required_args": {"room_purpose": "redesign"},
        "expected_stage": "stage_1b_age_context",
    },
    {
        "tool_name": "continue_home_decor_consultation",
        "phase": "Phase 2 - Constraints",
        "required_args": {"age_context": "school-age"},
        "expected_stage": "stage_1c_constraints",
    },
    {
        "tool_name": "continue_home_decor_consultation",
        "phase": "Phase 3 - Photo Request",
        "expected_stage": "stage_1d_photo_request",
        "expected_ui_type": "photo_upload",
    },
    {
        "tool_name": "analyze_room_with_history",
        "phase": "Phase 3 - Photo Analysis",
        "required_args": {"room_type": "bedroom"},
    },
    {
        "tool_name": "continue_home_decor_consultation",
        "phase": "Phase 4 - Style Finder",
        "expected_stage": "stage_2_style_discovery",
        "expected_ui_type": "style_selector",
    },
    {
        "tool_name": "continue_home_decor_consultation",
        "phase": "Phase 4 - Color Preferences",
        "expected_stage": "stage_3_color_preferences",
        "expected_ui_type": "color_selector",
    },
    {
        "tool_name": "continue_home_decor_consultation",
        "phase": "Phase 5 - Room Dimensions",
        "expected_stage": "stage_4_room_dimensions",
        "expected_ui_type": "room_dimensions",
    },
    {
        "tool_name": "continue_home_decor_consultation",
        "phase": "Phase 6 - Moodboard Generation",
        "expected_stage": "moodboard_presented",
        "expected_ui_type": "moodboard",
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
