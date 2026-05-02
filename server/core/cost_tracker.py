"""
AI Cost Management & Resource Efficiency.

Tracks token usage, API call costs, and provides budget monitoring
for Gemini, Imagen, and embedding API calls.
"""

import time
import logging
import threading
from typing import Dict, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

# Approximate pricing per 1K tokens (USD) -- update as pricing changes
PRICING = {
    "gemini-live-2.5-flash-native-audio": {"input": 0.00015, "output": 0.0006},
    "gemini-2.5-flash": {"input": 0.00015, "output": 0.0006},
    "gemini-3-pro-image-preview": {"input": 0.00125, "output": 0.005},
    "text-embedding-005": {"input": 0.000025, "output": 0.0},
    "imagen-4.0-ultra-generate-001": {"per_image": 0.06},
    "imagen-3.0-capability-001": {"per_image": 0.04},
}

# Budget alert threshold (USD per session)
SESSION_BUDGET_ALERT_USD = 1.0


class CostTracker:
    """Track API costs per session and globally."""

    def __init__(self):
        self._lock = threading.Lock()
        self._sessions: Dict[str, Dict] = {}
        self._global_stats = defaultdict(
            lambda: {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
        )

    def record_llm_call(
        self,
        session_id: str,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ):
        """Record an LLM API call with token counts."""
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = {
                    "start_time": time.time(),
                    "calls": defaultdict(
                        lambda: {
                            "count": 0,
                            "input_tokens": 0,
                            "output_tokens": 0,
                            "cost_usd": 0.0,
                        }
                    ),
                    "total_cost_usd": 0.0,
                }

            pricing = PRICING.get(model, {"input": 0.001, "output": 0.002})
            cost = (input_tokens / 1000 * pricing.get("input", 0)) + (
                output_tokens / 1000 * pricing.get("output", 0)
            )

            session = self._sessions[session_id]
            session["calls"][model]["count"] += 1
            session["calls"][model]["input_tokens"] += input_tokens
            session["calls"][model]["output_tokens"] += output_tokens
            session["calls"][model]["cost_usd"] += cost
            session["total_cost_usd"] += cost

            self._global_stats[model]["calls"] += 1
            self._global_stats[model]["input_tokens"] += input_tokens
            self._global_stats[model]["output_tokens"] += output_tokens
            self._global_stats[model]["cost_usd"] += cost

            # Budget alert
            if session["total_cost_usd"] > SESSION_BUDGET_ALERT_USD:
                logger.warning(
                    f"[COST] Session {session_id} exceeded budget: "
                    f"${session['total_cost_usd']:.4f} > ${SESSION_BUDGET_ALERT_USD}"
                )

    def record_image_generation(self, session_id: str, model: str, count: int = 1):
        """Record an image generation API call."""
        pricing = PRICING.get(model, {"per_image": 0.05})
        cost = count * pricing.get("per_image", 0.05)

        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = {
                    "start_time": time.time(),
                    "calls": defaultdict(
                        lambda: {
                            "count": 0,
                            "input_tokens": 0,
                            "output_tokens": 0,
                            "cost_usd": 0.0,
                        }
                    ),
                    "total_cost_usd": 0.0,
                }

            session = self._sessions[session_id]
            session["calls"][model]["count"] += count
            session["calls"][model]["cost_usd"] += cost
            session["total_cost_usd"] += cost

            self._global_stats[model]["calls"] += count
            self._global_stats[model]["cost_usd"] += cost

    def get_session_cost(self, session_id: str) -> Dict:
        """Get cost breakdown for a session."""
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return {"total_cost_usd": 0.0, "models": {}}

            return {
                "total_cost_usd": round(session["total_cost_usd"], 6),
                "duration_seconds": round(time.time() - session["start_time"], 1),
                "models": {
                    model: {
                        "count": stats["count"],
                        "input_tokens": stats["input_tokens"],
                        "output_tokens": stats["output_tokens"],
                        "cost_usd": round(stats["cost_usd"], 6),
                    }
                    for model, stats in session["calls"].items()
                },
            }

    def get_global_stats(self) -> Dict:
        """Get global cost stats across all sessions."""
        with self._lock:
            total_cost = sum(s["cost_usd"] for s in self._global_stats.values())
            return {
                "total_cost_usd": round(total_cost, 4),
                "active_sessions": len(self._sessions),
                "models": dict(self._global_stats),
            }

    def cleanup_session(self, session_id: str) -> Optional[Dict]:
        """Remove session and return final cost report."""
        with self._lock:
            session = self._sessions.pop(session_id, None)
            if session:
                report = {
                    "session_id": session_id,
                    "total_cost_usd": round(session["total_cost_usd"], 6),
                    "duration_seconds": round(time.time() - session["start_time"], 1),
                }
                logger.info(
                    f"[COST] Session {session_id} final cost: ${report['total_cost_usd']:.4f} "
                    f"({report['duration_seconds']}s)"
                )
                return report
            return None


# Global singleton
_tracker = CostTracker()


def get_cost_tracker() -> CostTracker:
    return _tracker
