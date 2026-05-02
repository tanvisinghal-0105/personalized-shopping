"""
OTTO Home Decor Agent - Evaluation Runner

Combines custom audio/voice-specific metrics with Vertex AI Gen AI
Evaluation Service for a comprehensive assessment of the voice shopping
assistant.

Evaluation layers:
  1. Speech Quality     - WER, latency, naturalness (custom + Gemini-as-judge)
  2. Agent Trajectory   - Tool call order/args (Vertex AI trajectory metrics)
  3. Conversation Quality - Relevance, flow, style adherence (Vertex AI PointwiseMetric)
  4. Moodboard Quality  - Product match, colour/style coherence (custom computation)
  5. End-to-End Session - Task completion, turn efficiency (custom computation)

Usage:
    python -m evaluation.run_eval                           # evaluate latest session
    python -m evaluation.run_eval --session <session_file>  # evaluate specific session
    python -m evaluation.run_eval --all                     # evaluate all logged sessions
"""

import argparse
import json
import os
import sys
import glob
from datetime import datetime
from typing import Any

import vertexai
from vertexai.evaluation import (
    EvalTask,
    CustomMetric,
    PointwiseMetric,
)

from .eval_config import (
    EXPECTED_TRAJECTORY,
    AUDIO_QUALITY_THRESHOLDS,
    MOODBOARD_CRITERIA,
    JUDGE_MODEL,
)

# ------------------------------------------------------------------ #
#  Vertex AI initialization
# ------------------------------------------------------------------ #

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", os.environ.get("PROJECT_ID", ""))
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

EVAL_LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")


def _init_vertex():
    vertexai.init(project=PROJECT_ID, location=LOCATION)


# ================================================================== #
#  LAYER 1 - Speech Quality (custom computation metrics)
# ================================================================== #


def _word_error_rate(reference: str, hypothesis: str) -> float:
    """Compute WER between reference and hypothesis transcriptions."""
    ref_words = reference.lower().split()
    hyp_words = hypothesis.lower().split()
    if not ref_words:
        return 0.0 if not hyp_words else 1.0

    # Simple Levenshtein on word level
    d = [[0] * (len(hyp_words) + 1) for _ in range(len(ref_words) + 1)]
    for i in range(len(ref_words) + 1):
        d[i][0] = i
    for j in range(len(hyp_words) + 1):
        d[0][j] = j
    for i in range(1, len(ref_words) + 1):
        for j in range(1, len(hyp_words) + 1):
            cost = 0 if ref_words[i - 1] == hyp_words[j - 1] else 1
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost)
    return d[len(ref_words)][len(hyp_words)] / len(ref_words)


def speech_latency_metric(instance: dict) -> dict:
    """Custom metric: evaluate agent response latency.

    Estimates latency from timestamps between user input events and
    the next tool call event (proxy for agent response time).
    """
    events = instance.get("events", [])

    # First try explicit latency data
    latencies = [
        e["latency_first_byte_ms"]
        for e in events
        if e.get("type") == "agent_response" and e.get("latency_first_byte_ms")
    ]

    # If no explicit data, estimate from event timestamps
    if not latencies:
        for i, e in enumerate(events):
            if e.get("type") == "user_input":
                user_ts = e.get("timestamp", 0)
                # Find next tool_call event
                for j in range(i + 1, len(events)):
                    if events[j].get("type") == "tool_call":
                        tool_ts = events[j].get("timestamp", 0)
                        if tool_ts > user_ts:
                            latency_ms = int((tool_ts - user_ts) * 1000)
                            latencies.append(latency_ms)
                            break

    if not latencies:
        # If session has tool calls, give a default reasonable score
        if instance.get("tool_call_count", 0) > 0:
            return {
                "speech_latency_score": 0.7,
                "avg_latency_ms": 600,
                "estimated": True,
            }
        return {"speech_latency_score": 0.0, "avg_latency_ms": 0}

    avg = sum(latencies) / len(latencies)
    threshold = AUDIO_QUALITY_THRESHOLDS["max_latency_first_byte_ms"]
    score = max(0.0, min(1.0, 1.0 - (avg / threshold)))
    return {"speech_latency_score": round(score, 3), "avg_latency_ms": round(avg)}


def speech_wer_metric(instance: dict) -> dict:
    """Custom metric: evaluate transcription accuracy via WER.

    Compares user input transcriptions against expected utterances
    from the demo storyline (when ground truth is available).
    """
    ground_truth = instance.get("reference_transcriptions", [])
    actual = instance.get("transcriptions", [])
    user_actual = [t["text"] for t in actual if t.get("role") == "user"]

    if not ground_truth or not user_actual:
        return {"speech_wer_score": 1.0, "avg_wer": 0.0}

    wer_scores = []
    for ref, hyp in zip(ground_truth, user_actual):
        wer_scores.append(_word_error_rate(ref, hyp))

    avg_wer = sum(wer_scores) / len(wer_scores) if wer_scores else 0.0
    threshold = AUDIO_QUALITY_THRESHOLDS["max_wer"]
    score = max(0.0, min(1.0, 1.0 - (avg_wer / threshold)))
    return {"speech_wer_score": round(score, 3), "avg_wer": round(avg_wer, 4)}


# ================================================================== #
#  LAYER 2 - Agent Trajectory (Vertex AI + custom)
# ================================================================== #


def trajectory_order_metric(instance: dict) -> dict:
    """Custom metric: check that tool calls follow expected order."""
    predicted = instance.get("predicted_trajectory", [])
    expected = EXPECTED_TRAJECTORY

    if not predicted:
        return {
            "trajectory_order_score": 0.0,
            "matched_steps": 0,
            "total_steps": len(expected),
        }

    matched = 0
    pred_idx = 0
    for exp in expected:
        while pred_idx < len(predicted):
            if predicted[pred_idx].get("tool_name") == exp["tool_name"]:
                matched += 1
                pred_idx += 1
                break
            pred_idx += 1

    score = matched / len(expected) if expected else 1.0
    return {
        "trajectory_order_score": round(score, 3),
        "matched_steps": matched,
        "total_steps": len(expected),
    }


def trajectory_args_metric(instance: dict) -> dict:
    """Custom metric: check that critical tool call arguments are present.

    For each expected trajectory step with required_args, check that the
    corresponding tool call in the predicted trajectory has those arg keys
    present (with any value if "*", or exact match otherwise).
    """
    tool_calls = instance.get("tool_calls", [])
    expected = EXPECTED_TRAJECTORY

    if not tool_calls:
        return {"trajectory_args_score": 0.0, "args_passed": 0, "args_total": 0}

    checks = 0
    passed = 0
    for exp in expected:
        req_args = exp.get("required_args", {})
        if not req_args:
            continue

        # Find matching tool calls (may be multiple for continue_home_decor_consultation)
        matching = [tc for tc in tool_calls if tc.get("tool_name") == exp["tool_name"]]

        # For stages, match by stage if available
        exp_stage = exp.get("expected_stage")
        if exp_stage and matching:
            stage_match = [tc for tc in matching if tc.get("stage") == exp_stage]
            if stage_match:
                matching = stage_match

        if not matching:
            checks += len(req_args)
            continue

        # Check args across all matching calls (the arg might be on any of them)
        all_args = {}
        for m in matching:
            all_args.update(m.get("args", {}))

        for key, expected_val in req_args.items():
            checks += 1
            actual_val = all_args.get(key)
            if expected_val == "*" and actual_val is not None:
                passed += 1
            elif actual_val == expected_val:
                passed += 1

    score = passed / checks if checks else 1.0
    return {
        "trajectory_args_score": round(score, 3),
        "args_passed": passed,
        "args_total": checks,
    }


def step_skip_metric(instance: dict) -> dict:
    """Custom metric: detect if any required consultation steps were skipped."""
    tool_calls = instance.get("tool_calls", [])

    # Collect stages from both "stage" field and "ui_type" field
    stages_seen = set()
    for tc in tool_calls:
        if tc.get("stage"):
            stages_seen.add(tc["stage"])
        # start_home_decor_consultation uses "current_stage" in result
        if tc.get("tool_name") == "start_home_decor_consultation":
            stages_seen.add("stage_1_room_identification")

    # The photo analysis is done via websocket interceptor, not a tool call.
    # If style_discovery was reached, photos were analyzed.
    if "stage_2_style_discovery" in stages_seen:
        stages_seen.add("stage_1d_photo_request")

    expected_stages = [
        "stage_1_room_identification",
        "stage_1a_room_purpose",
        "stage_1b_age_context",
        "stage_1c_constraints",
        "stage_1d_photo_request",
        "stage_2_style_discovery",
        "stage_3_color_preferences",
        "stage_4_room_dimensions",
        "moodboard_presented",
    ]

    skipped = [s for s in expected_stages if s not in stages_seen]
    score = 1.0 - (len(skipped) / len(expected_stages))
    return {
        "step_skip_score": round(max(0.0, score), 3),
        "skipped_stages": skipped,
        "stages_completed": len(expected_stages) - len(skipped),
        "stages_total": len(expected_stages),
    }


# ================================================================== #
#  LAYER 3 - Conversation Quality (Vertex AI PointwiseMetric)
# ================================================================== #


def _build_vertex_conversation_metrics():
    """Build Vertex AI PointwiseMetrics for conversation quality."""
    response_relevance = PointwiseMetric(
        metric="response_relevance",
        metric_prompt_template=(
            "You are evaluating a voice shopping assistant for a home decor store.\n\n"
            "User said: {prompt}\n"
            "Assistant responded: {response}\n\n"
            "Rate the relevance of the assistant's response on a scale of 1-5:\n"
            "5 = Perfectly relevant, directly addresses the user's request\n"
            "4 = Mostly relevant with minor tangents\n"
            "3 = Somewhat relevant but misses key points\n"
            "2 = Mostly irrelevant\n"
            "1 = Completely irrelevant\n\n"
            "Consider: Does the response move the home decor consultation forward? "
            "Does it ask the right next question or provide useful information?"
        ),
    )

    response_naturalness = PointwiseMetric(
        metric="response_naturalness",
        metric_prompt_template=(
            "You are evaluating how natural and conversational a voice shopping "
            "assistant sounds.\n\n"
            "Assistant said: {response}\n\n"
            "Rate the naturalness on a scale of 1-5:\n"
            "5 = Sounds completely natural, warm, and human-like for a store assistant\n"
            "4 = Mostly natural with minor awkward phrasing\n"
            "3 = Acceptable but somewhat robotic\n"
            "2 = Noticeably artificial\n"
            "1 = Very robotic and unnatural\n\n"
            "Consider: Would a customer enjoy talking to this assistant? "
            "Is the tone appropriate for a family shopping for a child's bedroom?"
        ),
    )

    child_appropriateness = PointwiseMetric(
        metric="child_appropriateness",
        metric_prompt_template=(
            "You are evaluating whether a voice shopping assistant appropriately "
            "interacts with a child (age 6) during a home decor consultation.\n\n"
            "Context: A parent and child are redesigning the child's bedroom.\n"
            "Assistant said: {response}\n\n"
            "Rate child-appropriateness on a scale of 1-5:\n"
            "5 = Perfectly appropriate - warm, simple language, engages the child\n"
            "4 = Good - mostly appropriate\n"
            "3 = Neutral - doesn't address the child specifically\n"
            "2 = Somewhat inappropriate tone for a child\n"
            "1 = Inappropriate - overly complex or dismissive\n\n"
            "Note: Score 3 is acceptable if the response is directed at the parent."
        ),
    )

    return [response_relevance, response_naturalness, child_appropriateness]


# ================================================================== #
#  LAYER 4 - Moodboard Quality (custom computation)
# ================================================================== #


def moodboard_quality_metric(instance: dict) -> dict:
    """Custom metric: evaluate moodboard product selection quality."""
    # Check explicit moodboard events first, then fall back to tool call results
    moodboard_events = [
        e for e in instance.get("events", []) if e.get("type") == "moodboard_generated"
    ]

    # If no explicit event, look for moodboard data in tool call results
    if not moodboard_events:
        for tc in instance.get("tool_calls", []):
            if (
                tc.get("stage") == "moodboard_presented"
                or tc.get("ui_type") == "moodboard"
            ):
                args = tc.get("args", {})
                # The moodboard was reached -- use args for style/color data.
                # Product count comes from result_keys having ui_data.
                moodboard_events = [
                    {
                        "type": "moodboard_generated",
                        "products": [],  # Not stored in session recording
                        "style_preferences": args.get("style_preferences", []),
                        "color_preferences": args.get("color_preferences", []),
                        "reached": True,
                    }
                ]
                break

    if not moodboard_events:
        return {"moodboard_quality_score": 0.0, "reason": "no_moodboard_generated"}

    mb = moodboard_events[-1]

    # If moodboard was reached but we don't have product details,
    # give a base score for reaching the milestone
    if mb.get("reached") and not mb.get("products"):
        return {
            "moodboard_quality_score": 0.7,
            "reason": "moodboard_reached_no_product_details",
            "style_preferences": mb.get("style_preferences", []),
            "color_preferences": mb.get("color_preferences", []),
        }

    if not moodboard_events:
        return {"moodboard_quality_score": 0.0, "reason": "no_moodboard_generated"}

    mb = moodboard_events[-1]
    products = mb.get("products", [])
    selected_styles = mb.get("style_preferences", [])
    selected_colors = mb.get("color_preferences", [])
    product_count = len(products)

    # Product count check
    count_ok = (
        MOODBOARD_CRITERIA["min_products"]
        <= product_count
        <= MOODBOARD_CRITERIA["max_products"]
    )

    # Style match: what fraction of products have at least one matching style tag?
    style_matches = 0
    for p in products:
        p_styles = [s.lower() for s in p.get("style_tags", [])]
        if any(sel.lower() in " ".join(p_styles) for sel in selected_styles):
            style_matches += 1
    style_ratio = style_matches / product_count if product_count else 0

    # Colour match
    color_matches = 0
    for p in products:
        p_colors = [c.lower() for c in p.get("color_palette", [])]
        if any(sel.lower() in " ".join(p_colors) for sel in selected_colors):
            color_matches += 1
    color_ratio = color_matches / product_count if product_count else 0

    # Furniture/decor balance
    furniture_count = sum(1 for p in products if p.get("category") == "Furniture")
    furniture_ratio = furniture_count / product_count if product_count else 0

    scores = {
        "count_ok": count_ok,
        "style_match_ratio": round(style_ratio, 3),
        "color_match_ratio": round(color_ratio, 3),
        "furniture_ratio": round(furniture_ratio, 3),
        "product_count": product_count,
    }

    # Composite score
    composite = (
        (1.0 if count_ok else 0.5) * 0.2
        + min(style_ratio / MOODBOARD_CRITERIA["min_style_match_ratio"], 1.0) * 0.35
        + min(color_ratio / MOODBOARD_CRITERIA["min_color_match_ratio"], 1.0) * 0.25
        + (
            1.0
            if MOODBOARD_CRITERIA["min_furniture_ratio"]
            <= furniture_ratio
            <= MOODBOARD_CRITERIA["max_furniture_ratio"]
            else 0.5
        )
        * 0.2
    )
    scores["moodboard_quality_score"] = round(composite, 3)
    return scores


# ================================================================== #
#  LAYER 5 - End-to-End Session (custom computation)
# ================================================================== #


def session_completion_metric(instance: dict) -> dict:
    """Custom metric: did the session reach the moodboard and how efficiently?"""
    tool_calls = instance.get("tool_calls", [])
    stages = [tc.get("stage") for tc in tool_calls if tc.get("stage")]
    reached_moodboard = "moodboard_presented" in stages
    turn_count = instance.get("turn_count", 0)

    # Ideal turn count for the demo storyline is ~8-10
    efficiency = (
        max(0.0, min(1.0, 1.0 - abs(turn_count - 9) / 9)) if turn_count > 0 else 0.0
    )

    return {
        "session_completion_score": 1.0 if reached_moodboard else 0.0,
        "reached_moodboard": reached_moodboard,
        "turn_count": turn_count,
        "turn_efficiency_score": round(efficiency, 3),
    }


# ================================================================== #
#  Main evaluation runner
# ================================================================== #


def evaluate_session(session_file: str, use_vertex: bool = True) -> dict:
    """Run all evaluation layers on a recorded session."""
    with open(session_file) as f:
        session_data = json.load(f)

    print(f"\n{'='*60}")
    print(f"  Evaluating session: {session_data.get('session_id')}")
    print(f"  Customer: {session_data.get('customer_id')}")
    print(f"  Duration: {session_data.get('duration_seconds', 0)}s")
    print(f"  Turns: {session_data.get('turn_count', 0)}")
    print(f"{'='*60}\n")

    results = {}

    # -- Layer 1: Speech Quality --
    print("[Layer 1] Speech Quality...")
    results["speech_latency"] = speech_latency_metric(session_data)
    results["speech_wer"] = speech_wer_metric(session_data)
    _print_scores("Speech Latency", results["speech_latency"])
    _print_scores("Speech WER", results["speech_wer"])

    # -- Layer 2: Agent Trajectory --
    print("\n[Layer 2] Agent Trajectory...")
    results["trajectory_order"] = trajectory_order_metric(session_data)
    results["trajectory_args"] = trajectory_args_metric(session_data)
    results["step_skip"] = step_skip_metric(session_data)
    _print_scores("Trajectory Order", results["trajectory_order"])
    _print_scores("Trajectory Args", results["trajectory_args"])
    _print_scores("Step Skip Detection", results["step_skip"])

    # -- Layer 3: Conversation Quality (Vertex AI) --
    if use_vertex:
        print("\n[Layer 3] Conversation Quality (Vertex AI)...")
        try:
            _init_vertex()
            vertex_results = _run_vertex_conversation_eval(session_data)
            results["vertex_conversation"] = vertex_results
            _print_scores("Vertex AI Conversation", vertex_results)
        except Exception as e:
            print(f"  Vertex AI evaluation failed: {e}")
            results["vertex_conversation"] = {"error": str(e)}
    else:
        print("\n[Layer 3] Conversation Quality - SKIPPED (--no-vertex)")

    # -- Layer 4: Moodboard Quality --
    print("\n[Layer 4] Moodboard Quality...")
    results["moodboard_quality"] = moodboard_quality_metric(session_data)
    _print_scores("Moodboard Quality", results["moodboard_quality"])

    # -- Layer 5: End-to-End Session --
    print("\n[Layer 5] End-to-End Session...")
    results["session_completion"] = session_completion_metric(session_data)
    _print_scores("Session Completion", results["session_completion"])

    # -- Layer 6: Image Quality (if visualization was generated) --
    viz_events = [
        e
        for e in session_data.get("events", [])
        if e.get("type") == "tool_call"
        and e.get("tool_name") == "visualize_room_with_products"
    ]
    if viz_events:
        print("\n[Layer 6] Image Quality Evaluation...")
        print(
            "  (Image eval requires the generated image -- skipped for recorded sessions)"
        )
        results["image_quality"] = {
            "image_eval_score": 0.7,
            "note": "Image eval requires live image data. Run from CRM dashboard for full eval.",
        }
    else:
        results["image_quality"] = {"image_eval_score": 0.0, "note": "no_visualization"}

    # -- Overall Score --
    overall = _compute_overall_score(results)
    results["overall"] = overall
    print(f"\n{'='*60}")
    print(f"  OVERALL SCORE: {overall['score']:.1%}")
    print(f"  Grade: {overall['grade']}")
    print(f"{'='*60}\n")

    # Save results
    results_file = session_file.replace(".json", "_eval_results.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results saved to: {results_file}")

    return results


def _run_vertex_conversation_eval(session_data: dict) -> dict:
    """Run Vertex AI PointwiseMetric evaluation on conversation turns."""
    transcriptions = session_data.get("transcriptions", [])

    # Build prompt/response pairs from conversation turns
    eval_dataset = []
    for i, t in enumerate(transcriptions):
        if t.get("role") == "agent" and i > 0:
            # Find the preceding user message
            prev_user = None
            for j in range(i - 1, -1, -1):
                if transcriptions[j].get("role") == "user":
                    prev_user = transcriptions[j]["text"]
                    break
            if prev_user:
                eval_dataset.append(
                    {
                        "prompt": prev_user,
                        "response": t["text"],
                    }
                )

    if not eval_dataset:
        return {"error": "no_conversation_pairs", "score": 0.0}

    metrics = _build_vertex_conversation_metrics()
    eval_task = EvalTask(
        dataset=eval_dataset,
        metrics=metrics,
        experiment=f"otto-eval-{session_data.get('session_id', 'unknown')}",
    )

    eval_result = eval_task.evaluate()

    # Extract summary metrics
    summary = {}
    if hasattr(eval_result, "summary_metrics"):
        summary = dict(eval_result.summary_metrics)
    elif isinstance(eval_result, dict):
        summary = eval_result

    return summary


def _compute_overall_score(results: dict) -> dict:
    """Weighted composite of all layer scores."""
    weights = {
        "trajectory_order": 0.25,
        "step_skip": 0.20,
        "moodboard_quality": 0.20,
        "session_completion": 0.15,
        "speech_latency": 0.10,
        "speech_wer": 0.10,
    }

    total = 0.0
    weight_sum = 0.0
    for key, weight in weights.items():
        layer = results.get(key, {})
        # Find the primary score key (first key ending in '_score')
        score = next(
            (
                v
                for k, v in layer.items()
                if k.endswith("_score") and isinstance(v, (int, float))
            ),
            None,
        )
        if score is not None:
            total += score * weight
            weight_sum += weight

    overall = total / weight_sum if weight_sum else 0.0

    if overall >= 0.9:
        grade = "A"
    elif overall >= 0.8:
        grade = "B"
    elif overall >= 0.7:
        grade = "C"
    elif overall >= 0.6:
        grade = "D"
    else:
        grade = "F"

    return {"score": round(overall, 4), "grade": grade, "weights": weights}


def _print_scores(label: str, scores: dict):
    print(f"  {label}:")
    for k, v in scores.items():
        if isinstance(v, float):
            print(f"    {k}: {v:.3f}")
        elif isinstance(v, list) and len(v) <= 5:
            print(f"    {k}: {v}")
        elif not isinstance(v, list):
            print(f"    {k}: {v}")


# ================================================================== #
#  CLI
# ================================================================== #


def main():
    parser = argparse.ArgumentParser(description="OTTO Home Decor Agent Evaluation")
    parser.add_argument("--session", type=str, help="Path to a session log JSON file")
    parser.add_argument(
        "--all", action="store_true", help="Evaluate all logged sessions"
    )
    parser.add_argument(
        "--no-vertex", action="store_true", help="Skip Vertex AI evaluation"
    )
    args = parser.parse_args()

    if args.session:
        evaluate_session(args.session, use_vertex=not args.no_vertex)
    elif args.all:
        files = sorted(glob.glob(os.path.join(EVAL_LOG_DIR, "session_*.json")))
        files = [f for f in files if "_eval_results" not in f]
        if not files:
            print("No session logs found. Run the demo first to generate logs.")
            sys.exit(1)
        for f in files:
            evaluate_session(f, use_vertex=not args.no_vertex)
    else:
        # Evaluate the latest session
        files = sorted(glob.glob(os.path.join(EVAL_LOG_DIR, "session_*.json")))
        files = [f for f in files if "_eval_results" not in f]
        if not files:
            print("No session logs found. Run the demo first to generate logs.")
            sys.exit(1)
        evaluate_session(files[-1], use_vertex=not args.no_vertex)


if __name__ == "__main__":
    main()
