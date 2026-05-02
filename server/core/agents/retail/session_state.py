"""
Session state management for home decor consultations.
Tracks multi-turn conversation state across WebSocket connections.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import threading


class HomeDecorSessionState:
    """Manages state for home decor consultation sessions."""

    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def create_session(self, customer_id: str, session_id: str) -> Dict[str, Any]:
        """Create a new consultation session."""
        with self._lock:
            session_data = {
                "session_id": session_id,
                "customer_id": customer_id,
                "created_at": datetime.now().isoformat(),
                "current_stage": "stage_1_room_identification",
                "collected_data": {
                    "room_type": None,
                    "room_purpose": None,  # "decoration" or "redesign"
                    "age_context": None,  # Age of room occupant
                    "constraints": None,  # Items to keep/remove
                    "room_photos_analyzed": False,  # Phase 3: Photo analysis complete
                    "photo_analysis": None,  # Room analysis results
                    "order_history": None,  # Customer order history
                    "style_preferences": None,
                    "color_preferences": None,
                    "room_dimensions": None,  # {"length": float, "width": float} in meters
                    "room_photo_base64": None,  # Base64 of first uploaded room photo for visualization
                    "room_photos_list": [],  # List of all uploaded photo base64 strings
                },
                "conversation_history": [],
                "moodboard_generated": False,
            }
            self._sessions[session_id] = session_data
            return session_data

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a session by ID."""
        with self._lock:
            return self._sessions.get(session_id)

    def get_customer_session(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recent session for a customer."""
        with self._lock:
            customer_sessions = [
                s for s in self._sessions.values() if s["customer_id"] == customer_id
            ]
            if customer_sessions:
                # Return most recent
                return sorted(
                    customer_sessions, key=lambda x: x["created_at"], reverse=True
                )[0]
            return None

    def update_session(
        self,
        session_id: str,
        room_type: Optional[str] = None,
        room_purpose: Optional[str] = None,
        age_context: Optional[str] = None,
        constraints: Optional[Dict[str, List[str]]] = None,
        room_photos_analyzed: Optional[bool] = None,
        photo_analysis: Optional[Dict[str, Any]] = None,
        order_history: Optional[List[Dict[str, Any]]] = None,
        style_preferences: Optional[List[str]] = None,
        color_preferences: Optional[List[str]] = None,
        room_dimensions: Optional[Dict[str, float]] = None,
        room_photo_base64: Optional[str] = None,
        stage: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update session data."""
        with self._lock:
            if session_id not in self._sessions:
                return None

            session = self._sessions[session_id]

            if room_type is not None:
                session["collected_data"]["room_type"] = room_type

            if room_purpose is not None:
                session["collected_data"]["room_purpose"] = room_purpose

            if age_context is not None:
                session["collected_data"]["age_context"] = age_context

            if constraints is not None:
                session["collected_data"]["constraints"] = constraints

            if room_photos_analyzed is not None:
                session["collected_data"]["room_photos_analyzed"] = room_photos_analyzed

            if photo_analysis is not None:
                session["collected_data"]["photo_analysis"] = photo_analysis

            if order_history is not None:
                session["collected_data"]["order_history"] = order_history

            if style_preferences is not None:
                session["collected_data"]["style_preferences"] = style_preferences

            if color_preferences is not None:
                session["collected_data"]["color_preferences"] = color_preferences

            if room_dimensions is not None:
                session["collected_data"]["room_dimensions"] = room_dimensions

            if room_photo_base64 is not None:
                session["collected_data"]["room_photo_base64"] = room_photo_base64

            if stage is not None:
                session["current_stage"] = stage

            session["updated_at"] = datetime.now().isoformat()

            return session

    def mark_moodboard_generated(self, session_id: str) -> None:
        """Mark that moodboard has been generated for this session."""
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id]["moodboard_generated"] = True
                self._sessions[session_id]["current_stage"] = "moodboard_presented"

    def add_conversation_turn(
        self,
        session_id: str,
        user_message: str,
        agent_response: str,
        tool_called: Optional[str] = None,
    ) -> None:
        """Add a conversation turn to the session history."""
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id]["conversation_history"].append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "user": user_message,
                        "agent": agent_response,
                        "tool": tool_called,
                    }
                )

    def clear_old_sessions(self, hours: int = 24) -> int:
        """Clear sessions older than specified hours. Returns count of cleared sessions."""
        with self._lock:
            now = datetime.now()
            to_remove = []

            for session_id, session in self._sessions.items():
                created = datetime.fromisoformat(session["created_at"])
                age_hours = (now - created).total_seconds() / 3600

                if age_hours > hours:
                    to_remove.append(session_id)

            for session_id in to_remove:
                del self._sessions[session_id]

            return len(to_remove)

    def delete_session(self, session_id: str) -> bool:
        """Delete a specific session."""
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False

    def get_all_active_sessions(self) -> List[Dict[str, Any]]:
        """Get all active sessions."""
        with self._lock:
            return list(self._sessions.values())


# Global singleton instance
_state_manager = HomeDecorSessionState()


def get_state_manager() -> HomeDecorSessionState:
    """Get the global state manager instance."""
    return _state_manager
