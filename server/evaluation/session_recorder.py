"""
Session Recorder - Captures live session data for offline evaluation.

Intercepts tool calls, transcriptions, latencies, and agent responses
during a live session and writes them to a JSON log file for later
evaluation with Vertex AI Gen AI Evaluation Service.
"""

import json
import time
import os
from datetime import datetime
from typing import Any, Optional


EVAL_LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(EVAL_LOG_DIR, exist_ok=True)


class SessionRecorder:
    """Records a single conversation session for evaluation."""

    def __init__(self, session_id: str, customer_id: str = "unknown"):
        self.session_id = session_id
        self.customer_id = customer_id
        self.start_time = time.time()
        self.events = []
        self.tool_calls = []
        self.transcriptions = []
        self.turn_count = 0
        self.cost_usd = 0.0
        self.token_usage = {"input_tokens": 0, "output_tokens": 0}

    def record_token_usage(
        self, input_tokens: int = 0, output_tokens: int = 0, cost_usd: float = 0.0
    ):
        """Record token usage from Gemini responses for cost tracking."""
        self.token_usage["input_tokens"] += input_tokens
        self.token_usage["output_tokens"] += output_tokens
        self.cost_usd += cost_usd

    def record_user_input(self, transcription: str, timestamp: Optional[float] = None):
        ts = timestamp or time.time()
        self.turn_count += 1
        event = {
            "type": "user_input",
            "turn": self.turn_count,
            "transcription": transcription,
            "timestamp": ts,
            "elapsed_ms": int((ts - self.start_time) * 1000),
        }
        self.events.append(event)
        self.transcriptions.append(
            {
                "role": "user",
                "text": transcription,
                "turn": self.turn_count,
            }
        )

    def record_agent_response(
        self,
        transcription: str,
        latency_first_byte_ms: Optional[int] = None,
        latency_total_ms: Optional[int] = None,
        timestamp: Optional[float] = None,
    ):
        ts = timestamp or time.time()
        event = {
            "type": "agent_response",
            "turn": self.turn_count,
            "transcription": transcription,
            "latency_first_byte_ms": latency_first_byte_ms,
            "latency_total_ms": latency_total_ms,
            "timestamp": ts,
            "elapsed_ms": int((ts - self.start_time) * 1000),
        }
        self.events.append(event)
        self.transcriptions.append(
            {
                "role": "agent",
                "text": transcription,
                "turn": self.turn_count,
            }
        )

    def record_tool_call(
        self,
        tool_name: str,
        args: dict,
        result: Any,
        stage: Optional[str] = None,
        ui_type: Optional[str] = None,
        timestamp: Optional[float] = None,
    ):
        ts = timestamp or time.time()
        tool_entry = {
            "tool_name": tool_name,
            "args": _safe_serialize(args),
            "result_keys": list(result.keys()) if isinstance(result, dict) else [],
            "stage": stage or result.get("stage") if isinstance(result, dict) else None,
            "ui_type": (
                result.get("ui_data", {}).get("display_type")
                if isinstance(result, dict)
                else None
            ),
            "status": result.get("status") if isinstance(result, dict) else None,
            "image_gcs_path": (
                result.get("image_gcs_path") if isinstance(result, dict) else None
            ),
            "products_shown": (
                result.get("products_shown") if isinstance(result, dict) else None
            ),
            "turn": self.turn_count,
            "timestamp": ts,
            "elapsed_ms": int((ts - self.start_time) * 1000),
        }
        self.tool_calls.append(tool_entry)
        self.events.append({"type": "tool_call", **tool_entry})
        # Auto-save after each tool call so data isn't lost if connection drops
        self._autosave()

    def record_moodboard(
        self, products: list, style_preferences: list, color_preferences: list
    ):
        self.events.append(
            {
                "type": "moodboard_generated",
                "product_count": len(products),
                "products": [
                    {
                        "product_id": p.get("product_id"),
                        "name": p.get("name"),
                        "category": p.get("category"),
                        "style_tags": p.get("style_tags", []),
                        "color_palette": p.get("color_palette", []),
                    }
                    for p in products
                ],
                "style_preferences": style_preferences,
                "color_preferences": color_preferences,
                "turn": self.turn_count,
                "timestamp": time.time(),
            }
        )

    def _autosave(self):
        """Save current state to disk after each tool call.
        This ensures data is not lost if the WebSocket drops unexpectedly."""
        try:
            self.save()
        except Exception:
            pass

    def save(self):
        """Persist the session log locally and optionally to GCS."""
        record = {
            "session_id": self.session_id,
            "customer_id": self.customer_id,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "duration_seconds": round(time.time() - self.start_time, 1),
            "turn_count": self.turn_count,
            "tool_call_count": len(self.tool_calls),
            "predicted_trajectory": [
                {"tool_name": tc["tool_name"], "args": tc["args"]}
                for tc in self.tool_calls
            ],
            "tool_calls": self.tool_calls,
            "transcriptions": self.transcriptions,
            "events": self.events,
            "cost_usd": round(self.cost_usd, 6),
            "token_usage": self.token_usage,
        }
        filename = f"session_{self.session_id}_{int(self.start_time)}.json"
        filepath = os.path.join(EVAL_LOG_DIR, filename)
        with open(filepath, "w") as f:
            json.dump(record, f, indent=2, default=str)

        # Also upload to GCS if configured
        _upload_to_gcs(filename, record)

        return filepath


def _safe_serialize(obj):
    """Return a JSON-safe copy, dropping large binary blobs."""
    if not isinstance(obj, dict):
        return obj
    clean = {}
    for k, v in obj.items():
        if isinstance(v, str) and len(v) > 10000:
            clean[k] = f"<{len(v)} chars>"
        elif isinstance(v, bytes):
            clean[k] = f"<{len(v)} bytes>"
        elif isinstance(v, dict):
            clean[k] = _safe_serialize(v)
        elif isinstance(v, list):
            clean[k] = [_safe_serialize(i) if isinstance(i, dict) else i for i in v]
        else:
            clean[k] = v
    return clean


# -- Global recorder registry (one per active session) --
_active_recorders = {}


def get_recorder(session_id: str, customer_id: str = "unknown") -> SessionRecorder:
    if session_id not in _active_recorders:
        _active_recorders[session_id] = SessionRecorder(session_id, customer_id)
    return _active_recorders[session_id]


def finish_recorder(session_id: str) -> Optional[str]:
    recorder = _active_recorders.pop(session_id, None)
    if recorder:
        return recorder.save()
    return None


def _upload_to_gcs(filename: str, record: dict):
    """Upload session log to GCS bucket if configured."""
    try:
        from config.config import GCS_BUCKET_NAME, GCS_EVAL_PREFIX

        if not GCS_BUCKET_NAME:
            return
        from google.cloud import storage

        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(f"{GCS_EVAL_PREFIX}/{filename}")
        blob.upload_from_string(
            json.dumps(record, indent=2, default=str),
            content_type="application/json",
        )
    except Exception:
        pass  # GCS upload is best-effort, local save is the primary
