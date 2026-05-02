"""
Image Quality Evaluation using Gemini as judge.

Evaluates generated room visualization images against criteria:
- Product placement accuracy (are all selected products visible?)
- Style adherence (does the image match the selected style?)
- Room layout preservation (does it look like the original room?)
- Constraint compliance (are kept items still present?)
- Overall aesthetic quality

Uses a rubric-based approach inspired by Davidsonian Scene Graph (DSG)
methodology from the brandcanvas evaluation system.
"""

import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def evaluate_generated_image(
    image_base64: str,
    products_shown: List[Dict],
    style_preferences: List[str],
    room_type: str,
    constraints: Optional[Dict] = None,
    has_reference_photo: bool = False,
) -> Dict:
    """Evaluate a generated room visualization image against criteria.

    Args:
        image_base64: Base64-encoded generated image
        products_shown: List of products that should be in the image
        style_preferences: Selected style themes
        room_type: Type of room (bedroom, living room, etc.)
        constraints: Items to keep/remove
        has_reference_photo: Whether a reference room photo was provided

    Returns:
        Dictionary with scores and verdicts per criterion
    """
    from google import genai
    from google.genai import types as genai_types
    import base64

    # Build evaluation rubric
    rubric = _build_rubric(products_shown, style_preferences, room_type, constraints)

    # Build the evaluation prompt
    questions = []
    for i, criterion in enumerate(rubric):
        questions.append(
            f"{i+1}. {criterion['question']} "
            f"(Severity: {criterion['severity']}, Category: {criterion['category']})"
        )

    eval_prompt = (
        "You are an expert interior design evaluator. "
        "Examine this room visualization image and answer each question with "
        "YES, NO, or N/A (if the criterion cannot be assessed from the image).\n\n"
        "For each question, provide:\n"
        "- verdict: YES / NO / N/A\n"
        "- confidence: HIGH / MEDIUM / LOW\n"
        "- brief explanation (1 sentence)\n\n"
        "Questions:\n" + "\n".join(questions) + "\n\n"
        "Respond in JSON format:\n"
        '{"verdicts": [{"question_id": 1, "verdict": "YES", "confidence": "HIGH", "explanation": "..."}, ...]}'
    )

    try:
        client = genai.Client()
        image_bytes = base64.b64decode(image_base64)

        from PIL import Image as PILImage
        from io import BytesIO

        pil_image = PILImage.open(BytesIO(image_bytes))

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[pil_image, eval_prompt],
            config=genai_types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )

        if response and response.text:
            result = _parse_verdicts(response.text, rubric)
            return result

    except Exception as e:
        logger.error(f"[IMAGE EVAL] Evaluation failed: {e}")

    return {
        "image_eval_score": 0.0,
        "error": "evaluation_failed",
        "verdicts": [],
    }


def _build_rubric(
    products: List[Dict],
    styles: List[str],
    room_type: str,
    constraints: Optional[Dict],
) -> List[Dict]:
    """Build evaluation rubric from criteria."""
    rubric = []

    # Product placement criteria (BLOCKER severity)
    for product in products[:6]:
        name = product.get("name", "unknown product")
        rubric.append(
            {
                "question": f"Is a '{name}' clearly visible in the room?",
                "category": "product_placement",
                "severity": "BLOCKER",
                "gt_answer": "yes",
            }
        )

    # Style adherence criteria
    style_text = ", ".join(styles) if styles else "modern"
    rubric.append(
        {
            "question": f"Does the room design match a '{style_text}' interior design style?",
            "category": "style_adherence",
            "severity": "WARNING",
            "gt_answer": "yes",
        }
    )

    # Room type criteria
    rubric.append(
        {
            "question": f"Does this look like a {room_type}?",
            "category": "room_type",
            "severity": "BLOCKER",
            "gt_answer": "yes",
        }
    )

    # Constraint compliance
    if constraints:
        keep_items = []
        if isinstance(constraints, dict):
            keep_items = constraints.get("keep", [])
        elif isinstance(constraints, str) and "shelf" in constraints.lower():
            keep_items = ["cube shelf"]

        for item in keep_items:
            rubric.append(
                {
                    "question": f"Is the existing '{item}' still present and visible in the room?",
                    "category": "constraint_compliance",
                    "severity": "BLOCKER",
                    "gt_answer": "yes",
                }
            )

    # General quality criteria
    rubric.extend(
        [
            {
                "question": "Is the image photorealistic and free from obvious AI artifacts?",
                "category": "quality",
                "severity": "WARNING",
                "gt_answer": "yes",
            },
            {
                "question": "Are all furniture items placed on appropriate surfaces (not floating, not on windows)?",
                "category": "quality",
                "severity": "WARNING",
                "gt_answer": "yes",
            },
            {
                "question": "Does the room look warm, inviting, and aspirational?",
                "category": "aesthetic",
                "severity": "WARNING",
                "gt_answer": "yes",
            },
        ]
    )

    return rubric


def _parse_verdicts(response_text: str, rubric: List[Dict]) -> Dict:
    """Parse Gemini's verdict response and compute scores."""
    try:
        # Try to parse JSON
        data = json.loads(response_text)
        verdicts_raw = data.get("verdicts", [])
    except json.JSONDecodeError:
        logger.warning("[IMAGE EVAL] Failed to parse JSON response, attempting regex")
        verdicts_raw = []

    verdicts = []
    blocker_failed = False
    scores_by_category = {}

    for i, criterion in enumerate(rubric):
        verdict_data = verdicts_raw[i] if i < len(verdicts_raw) else {}
        verdict = verdict_data.get("verdict", "N/A").upper().strip()
        confidence = verdict_data.get("confidence", "LOW")
        explanation = verdict_data.get("explanation", "")

        # Score: YES=1.0, NO=0.0, N/A=excluded
        if verdict == "YES":
            score = 1.0
        elif verdict == "NO":
            score = 0.0
            if criterion["severity"] == "BLOCKER":
                blocker_failed = True
        else:
            score = None  # Excluded from average

        category = criterion["category"]
        if category not in scores_by_category:
            scores_by_category[category] = []
        if score is not None:
            scores_by_category[category].append(score)

        verdicts.append(
            {
                "question": criterion["question"],
                "category": category,
                "severity": criterion["severity"],
                "verdict": verdict,
                "confidence": confidence,
                "explanation": explanation,
                "score": score,
            }
        )

    # Compute category scores
    category_scores = {}
    for cat, cat_scores in scores_by_category.items():
        if cat_scores:
            category_scores[cat] = round(sum(cat_scores) / len(cat_scores), 3)
        else:
            category_scores[cat] = -1.0  # All N/A

    # Overall score
    all_scores = [s for scores in scores_by_category.values() for s in scores]
    overall = round(sum(all_scores) / len(all_scores), 3) if all_scores else 0.0

    # If any BLOCKER failed, cap overall at 0.5
    if blocker_failed:
        overall = min(overall, 0.5)

    return {
        "image_eval_score": overall,
        "blocker_failed": blocker_failed,
        "category_scores": category_scores,
        "verdicts": verdicts,
        "criteria_count": len(rubric),
        "verdicts_count": len([v for v in verdicts if v["score"] is not None]),
    }
