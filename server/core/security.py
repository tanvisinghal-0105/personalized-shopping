"""
Comprehensive security module covering:
1. Authentication & Authorization (Google IAP + OAuth2)
2. Data Protection & Privacy (PII handling, input sanitization)
3. AI-Specific Security (prompt injection detection, content safety)
4. Compliance & Governance (audit logging, data retention)
"""

import re
import logging
import hashlib
import json
from datetime import datetime
from typing import Optional, Dict, List, Any

from .models import ApprovalStatus, DiscountType

logger = logging.getLogger(__name__)


# ================================================================== #
#  1. INPUT SANITIZATION & VALIDATION
# ================================================================== #

# Max lengths to prevent abuse
MAX_TEXT_INPUT_LENGTH = 2000
MAX_CUSTOMER_ID_LENGTH = 20
MAX_PRODUCT_IDS = 20

# Patterns that indicate potential injection attempts
INJECTION_PATTERNS = [
    r"ignore\s+(previous|above|all)\s+(instructions|prompts|rules)",
    r"you\s+are\s+now\s+(a|an)\s+",
    r"system\s*:\s*",
    r"<\s*script",
    r"javascript\s*:",
    r"\{\{.*\}\}",
    r"exec\s*\(",
    r"eval\s*\(",
    r"__import__",
    r"os\.system",
]

_compiled_patterns = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def sanitize_text_input(text: str) -> str:
    """Sanitize user text input.

    - Truncates to max length
    - Strips control characters
    - Detects prompt injection attempts

    Returns the sanitized text. Logs warnings for suspicious input.
    """
    if not text:
        return ""

    # Truncate
    if len(text) > MAX_TEXT_INPUT_LENGTH:
        logger.warning(
            f"[SECURITY] Text input truncated from {len(text)} to {MAX_TEXT_INPUT_LENGTH} chars"
        )
        text = text[:MAX_TEXT_INPUT_LENGTH]

    # Strip control characters (keep newlines and tabs)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Check for injection patterns
    for pattern in _compiled_patterns:
        if pattern.search(text):
            logger.warning(
                f"[SECURITY] Potential prompt injection detected: '{text[:100]}...'"
            )
            audit_log("prompt_injection_attempt", {"text_preview": text[:200]})
            break

    return text


def validate_customer_id(customer_id: str) -> bool:
    """Validate customer ID format (CY-XXXX-XXXX)."""
    if not customer_id:
        return False
    if len(customer_id) > MAX_CUSTOMER_ID_LENGTH:
        return False
    return bool(re.match(r"^CY-\d{4}-\d{4}$", customer_id))


def validate_product_ids(product_ids: List[str]) -> List[str]:
    """Validate and sanitize product ID list."""
    if not product_ids:
        return []
    # Limit count
    if len(product_ids) > MAX_PRODUCT_IDS:
        logger.warning(
            f"[SECURITY] Too many product IDs ({len(product_ids)}), truncating to {MAX_PRODUCT_IDS}"
        )
        product_ids = product_ids[:MAX_PRODUCT_IDS]
    # Validate format (alphanumeric + hyphens only)
    valid = [pid for pid in product_ids if re.match(r"^[A-Za-z0-9\-_]+$", pid)]
    if len(valid) != len(product_ids):
        logger.warning(
            f"[SECURITY] Filtered {len(product_ids) - len(valid)} invalid product IDs"
        )
    return valid


# ================================================================== #
#  2. DATA PROTECTION & PRIVACY (PII Handling)
# ================================================================== #

# PII patterns for detection and redaction
PII_PATTERNS = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "phone": re.compile(
        r"\b\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b"
    ),
    "credit_card": re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
    "address": re.compile(
        r"\b\d{1,5}\s+\w+\s+(street|st|avenue|ave|road|rd|boulevard|blvd|lane|ln|drive|dr)\b",
        re.IGNORECASE,
    ),
}


def detect_pii(text: str) -> Dict[str, bool]:
    """Detect PII types present in text."""
    found = {}
    for pii_type, pattern in PII_PATTERNS.items():
        if pattern.search(text):
            found[pii_type] = True
    return found


def redact_pii(text: str) -> str:
    """Redact PII from text for safe logging."""
    redacted = text
    for pii_type, pattern in PII_PATTERNS.items():
        redacted = pattern.sub(f"[REDACTED_{pii_type.upper()}]", redacted)
    return redacted


def hash_pii(value: str) -> str:
    """One-way hash PII for analytics without exposing raw data."""
    return hashlib.sha256(value.encode()).hexdigest()[:16]


# ================================================================== #
#  3. AI-SPECIFIC SECURITY (Model Armor + Local Checks)
# ================================================================== #

# Model Armor client (initialized lazily)
_model_armor_client = None


def _get_model_armor_client():
    """Lazy-init the Model Armor client."""
    global _model_armor_client
    if _model_armor_client is None:
        try:
            from google.api_core.client_options import ClientOptions
            from google.cloud import modelarmor_v1
            import os

            location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
            _model_armor_client = modelarmor_v1.ModelArmorClient(
                transport="rest",
                client_options=ClientOptions(
                    api_endpoint=f"modelarmor.{location}.rep.googleapis.com"
                ),
            )
            logger.info("[MODEL ARMOR] Client initialized")
        except Exception as e:
            logger.warning(f"[MODEL ARMOR] Not available, using local checks: {e}")
    return _model_armor_client


def sanitize_with_model_armor(text: str, is_prompt: bool = True) -> Dict[str, Any]:
    """Sanitize text using Google Cloud Model Armor.

    Args:
        text: The text to sanitize.
        is_prompt: True for user prompts (input), False for model responses (output).

    Returns:
        Dict with 'safe' bool, 'findings' list, and optionally 'sanitized_text'.
    """
    client = _get_model_armor_client()
    if client is None:
        return {"safe": True, "findings": [], "source": "skipped"}

    try:
        import os
        from google.cloud import modelarmor_v1

        project_id = os.environ.get("PROJECT_ID", "")
        location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        template_id = (
            "cymbal-prompt-sanitizer" if is_prompt else "cymbal-response-sanitizer"
        )
        template_name = (
            f"projects/{project_id}/locations/{location}/templates/{template_id}"
        )
        data_item = modelarmor_v1.DataItem(text=text)

        if is_prompt:
            request = modelarmor_v1.SanitizeUserPromptRequest(
                name=template_name,
                user_prompt_data=data_item,
            )
            response = client.sanitize_user_prompt(request=request)
        else:
            request = modelarmor_v1.SanitizeModelResponseRequest(
                name=template_name,
                model_response_data=data_item,
            )
            response = client.sanitize_model_response(request=request)

        match_state = str(response.sanitization_result.filter_match_state)
        is_safe = "MATCH_FOUND" not in match_state

        findings = []
        result = response.sanitization_result
        if hasattr(result, "filter_results"):
            for filter_name, filter_result in result.filter_results.items():
                if "MATCH_FOUND" in str(filter_result.match_state):
                    findings.append(filter_name)

        if not is_safe:
            logger.warning(
                f"[MODEL ARMOR] {'Prompt' if is_prompt else 'Response'} "
                f"flagged: {findings}"
            )
            audit_log(
                "model_armor_finding",
                {
                    "type": "prompt" if is_prompt else "response",
                    "findings": findings,
                    "text_preview": text[:100],
                },
            )

        return {"safe": is_safe, "findings": findings, "source": "model_armor"}

    except Exception as e:
        logger.warning(f"[MODEL ARMOR] Sanitization failed, using local checks: {e}")
        return {"safe": True, "findings": [], "source": "fallback"}


def check_ai_safety(text: str) -> Dict[str, Any]:
    """Check text for AI safety concerns.

    Returns a dict with safety assessment:
    - safe: bool
    - concerns: list of detected concern types
    """
    concerns = []

    # Check for prompt injection
    for pattern in _compiled_patterns:
        if pattern.search(text):
            concerns.append("prompt_injection")
            break

    # Check for attempts to extract system prompts
    extraction_patterns = [
        r"(show|tell|reveal|display|print|output)\s+(me\s+)?your\s+(system\s+)?(prompt|instructions|rules)",
        r"(show|tell|reveal|display|print|output)\s+(me\s+)?the\s+system\s*(prompt|instructions|rules)",
        r"what\s+(are|is)\s+your\s+(system\s+)?(prompt|instructions)",
        r"repeat\s+(your|the)\s+(system\s+)?(prompt|message)",
    ]
    for pattern in extraction_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            concerns.append("system_prompt_extraction")
            break

    # Check for jailbreak attempts
    jailbreak_patterns = [
        r"DAN\s+mode",
        r"developer\s+mode",
        r"pretend\s+you\s+(are|have)\s+no\s+(rules|restrictions|limits)",
        r"bypass\s+(safety|content)\s+(filter|policy)",
    ]
    for pattern in jailbreak_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            concerns.append("jailbreak_attempt")
            break

    is_safe = len(concerns) == 0

    if not is_safe:
        logger.warning(f"[AI SAFETY] Concerns detected: {concerns}")
        audit_log(
            "ai_safety_concern", {"concerns": concerns, "text_preview": text[:200]}
        )

    return {"safe": is_safe, "concerns": concerns}


# ================================================================== #
#  4. COMPLIANCE & GOVERNANCE (Audit Logging)
# ================================================================== #

_audit_log_buffer: List[Dict] = []
AUDIT_LOG_FLUSH_SIZE = 50


def audit_log(event_type: str, details: Dict[str, Any], user_email: str = "system"):
    """Record an audit event for compliance tracking.

    Events are buffered and flushed to Firestore/GCS periodically.
    Covers: auth events, data access, AI safety, admin actions.
    """
    event = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "user": user_email,
        "details": details,
    }

    logger.info(f"[AUDIT] {event_type}: {json.dumps(details, default=str)[:200]}")
    _audit_log_buffer.append(event)

    if len(_audit_log_buffer) >= AUDIT_LOG_FLUSH_SIZE:
        flush_audit_log()


def flush_audit_log():
    """Flush buffered audit events to persistent storage."""
    global _audit_log_buffer
    if not _audit_log_buffer:
        return

    events = _audit_log_buffer.copy()
    _audit_log_buffer.clear()

    try:
        from google.cloud import firestore

        db = firestore.Client()
        batch = db.batch()
        for event in events:
            doc_ref = db.collection("audit_logs").document()
            batch.set(doc_ref, event)
        batch.commit()
        logger.info(f"[AUDIT] Flushed {len(events)} audit events to Firestore")
    except Exception as e:
        logger.error(f"[AUDIT] Failed to flush audit log: {e}")
        # Re-buffer events that failed to flush
        _audit_log_buffer.extend(events)


# -- Data retention policy --
DATA_RETENTION_DAYS = {
    "session_recordings": 90,  # Eval session logs
    "audit_logs": 365,  # Compliance audit trail
    "customer_carts": 30,  # Shopping cart data
    "generated_images": 7,  # Imagen outputs
}


def get_retention_policy() -> Dict[str, int]:
    """Get data retention policy for compliance documentation."""
    return DATA_RETENTION_DAYS
