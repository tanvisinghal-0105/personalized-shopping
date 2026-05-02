"""
Context detection system for shopping interactions.
Detects time-of-day, urgency, family member presence, and interaction patterns.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, time
from ...logger import logger


class ContextDetector:
    """Detects contextual information about the shopping interaction."""

    def __init__(self):
        """Initialize the context detector."""
        pass

    def detect_time_context(
        self, timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Detect time-of-day context.

        Args:
            timestamp: Optional datetime to analyze. Defaults to now.

        Returns:
            Dictionary with time context information.
        """
        if timestamp is None:
            timestamp = datetime.now()

        hour = timestamp.hour
        day_of_week = timestamp.strftime("%A")
        is_weekend = timestamp.weekday() >= 5  # Saturday = 5, Sunday = 6

        # Determine time period
        if 5 <= hour < 12:
            period = "morning"
            energy = "fresh"
        elif 12 <= hour < 17:
            period = "afternoon"
            energy = "active"
        elif 17 <= hour < 21:
            period = "evening"
            energy = "relaxed"
        else:
            period = "night"
            energy = "quiet"

        # Determine shopping context
        if is_weekend and period == "morning":
            shopping_context = "weekend_morning"
            mood = "leisurely"
            availability = "high"  # More time to browse
        elif is_weekend:
            shopping_context = "weekend_leisure"
            mood = "relaxed"
            availability = "medium"
        elif period == "evening":
            shopping_context = "after_work"
            mood = "tired_but_browsing"
            availability = "medium"
        elif period == "morning":
            shopping_context = "morning_rush"
            mood = "quick"
            availability = "low"  # Probably busy
        else:
            shopping_context = "midday"
            mood = "focused"
            availability = "medium"

        return {
            "timestamp": timestamp.isoformat(),
            "hour": hour,
            "day_of_week": day_of_week,
            "is_weekend": is_weekend,
            "period": period,
            "energy": energy,
            "shopping_context": shopping_context,
            "mood": mood,
            "availability": availability,
            "suggested_interaction_style": self._suggest_interaction_style(
                shopping_context, mood
            ),
        }

    def _suggest_interaction_style(self, shopping_context: str, mood: str) -> str:
        """
        Suggest an interaction style based on context.

        Args:
            shopping_context: The shopping context.
            mood: The detected mood.

        Returns:
            Suggested interaction style.
        """
        if shopping_context in ["weekend_morning", "weekend_leisure"]:
            return "conversational_detailed"  # Customer has time
        elif shopping_context == "morning_rush":
            return "quick_efficient"  # Customer is busy
        elif shopping_context == "after_work":
            return "helpful_patient"  # Customer may be tired
        else:
            return "balanced"

    def detect_family_presence(
        self, transcript: str, family_members: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Detect if family members are mentioned or present in the conversation.

        Args:
            transcript: Recent conversation transcript.
            family_members: List of known family members from profile.

        Returns:
            Dictionary with family presence information.
        """
        if not transcript:
            return {
                "family_detected": False,
                "members_mentioned": [],
                "collaborative_decision": False,
            }

        transcript_lower = transcript.lower()
        members_mentioned = []
        collaborative_signals = []

        # Check for family member names
        if family_members:
            for member in family_members:
                name = member.get("name", "").lower()
                if name and name in transcript_lower:
                    members_mentioned.append(
                        {
                            "name": member.get("name"),
                            "relationship": member.get("relationship"),
                            "age_range": member.get("age_range"),
                        }
                    )

        # Check for collaborative decision signals
        collaborative_keywords = [
            "wants to help",
            "is here",
            "we both",
            "together",
            "co-decide",
            "with me",
            "helping choose",
            "can help decide",
        ]

        for keyword in collaborative_keywords:
            if keyword in transcript_lower:
                collaborative_signals.append(keyword)

        # Check for child/family references
        family_keywords = [
            "my daughter",
            "my son",
            "my child",
            "my kid",
            "our daughter",
            "our son",
            "family",
            "children",
        ]

        for keyword in family_keywords:
            if keyword in transcript_lower:
                collaborative_signals.append(keyword)

        return {
            "family_detected": len(members_mentioned) > 0
            or len(collaborative_signals) > 0,
            "members_mentioned": members_mentioned,
            "collaborative_signals": collaborative_signals,
            "collaborative_decision": len(collaborative_signals) > 0,
            "suggested_tone": (
                "inclusive_child_friendly"
                if any(
                    m.get("age_range") in ["toddler", "school-age"]
                    for m in members_mentioned
                )
                else "family_oriented"
            ),
        }

    def detect_urgency(self, transcript: str) -> Dict[str, Any]:
        """
        Detect urgency level from the conversation.

        Args:
            transcript: Recent conversation transcript.

        Returns:
            Dictionary with urgency information.
        """
        if not transcript:
            return {
                "urgency_level": "normal",
                "urgency_signals": [],
                "timeline": "flexible",
            }

        transcript_lower = transcript.lower()
        urgency_signals = []
        urgency_level = "normal"
        timeline = "flexible"

        # High urgency signals
        high_urgency = [
            "asap",
            "urgent",
            "quickly",
            "right away",
            "immediately",
            "today",
            "this week",
            "soon",
            "starting school",
            "moving in",
        ]

        # Medium urgency signals
        medium_urgency = [
            "next month",
            "few weeks",
            "upcoming",
            "before",
            "in time for",
            "by the time",
        ]

        # Low urgency signals
        low_urgency = [
            "eventually",
            "someday",
            "when we can",
            "no rush",
            "thinking about",
            "considering",
            "exploring",
        ]

        # Check for urgency signals
        for signal in high_urgency:
            if signal in transcript_lower:
                urgency_signals.append(signal)
                urgency_level = "high"
                timeline = "immediate"

        if urgency_level == "normal":
            for signal in medium_urgency:
                if signal in transcript_lower:
                    urgency_signals.append(signal)
                    urgency_level = "medium"
                    timeline = "near_term"

        if urgency_level == "normal":
            for signal in low_urgency:
                if signal in transcript_lower:
                    urgency_signals.append(signal)
                    urgency_level = "low"
                    timeline = "long_term"

        return {
            "urgency_level": urgency_level,
            "urgency_signals": urgency_signals,
            "timeline": timeline,
            "suggested_response_speed": "fast" if urgency_level == "high" else "normal",
        }

    def detect_project_scope(self, transcript: str) -> Dict[str, Any]:
        """
        Detect the scope and complexity of the request.

        Args:
            transcript: Recent conversation transcript.

        Returns:
            Dictionary with project scope information.
        """
        if not transcript:
            return {"scope": "unknown", "complexity": "simple", "signals": []}

        transcript_lower = transcript.lower()
        scope_signals = []

        # Room redesign signals (high complexity)
        redesign_signals = [
            "redesign",
            "redesigning",
            "redo",
            "redoing",
            "transform",
            "complete makeover",
            "starting from scratch",
            "everything",
            "furniture and decor",
            "entire room",
            "whole room",
        ]

        # Multi-product signals (medium complexity)
        multi_product_signals = [
            "desk, bed",
            "bed and",
            "desk and",
            "wardrobe and",
            "need several",
            "multiple items",
            "a few things",
            "some furniture",
            "few pieces",
        ]

        # Single product signals (low complexity)
        single_product_signals = [
            "just a",
            "only need",
            "looking for one",
            "single",
            "one item",
            "specific product",
        ]

        # Decoration only signals (low-medium complexity)
        decoration_signals = [
            "decoration",
            "decorating",
            "decor",
            "accessories",
            "finishing touches",
            "accent pieces",
            "some art",
        ]

        # Check for redesign (highest complexity)
        for signal in redesign_signals:
            if signal in transcript_lower:
                scope_signals.append(signal)
                return {
                    "scope": "full_room_redesign",
                    "complexity": "high",
                    "signals": scope_signals,
                    "estimated_products": "8-15",
                    "suggested_persona": "interior_designer",
                }

        # Check for multi-product
        for signal in multi_product_signals:
            if signal in transcript_lower:
                scope_signals.append(signal)
                return {
                    "scope": "multi_product",
                    "complexity": "medium",
                    "signals": scope_signals,
                    "estimated_products": "3-7",
                    "suggested_persona": "product_consultant",
                }

        # Check for decoration only
        for signal in decoration_signals:
            if signal in transcript_lower:
                scope_signals.append(signal)
                return {
                    "scope": "decoration_only",
                    "complexity": "medium",
                    "signals": scope_signals,
                    "estimated_products": "4-8",
                    "suggested_persona": "style_advisor",
                }

        # Check for single product
        for signal in single_product_signals:
            if signal in transcript_lower:
                scope_signals.append(signal)
                return {
                    "scope": "single_product",
                    "complexity": "low",
                    "signals": scope_signals,
                    "estimated_products": "1-2",
                    "suggested_persona": "sales_assistant",
                }

        # Default
        return {
            "scope": "unclear",
            "complexity": "medium",
            "signals": [],
            "estimated_products": "3-5",
            "suggested_persona": "general_assistant",
        }

    def get_full_context(
        self,
        initial_request: str,
        customer_profile: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get comprehensive context analysis for the interaction.

        Args:
            initial_request: The customer's initial request.
            customer_profile: Optional customer profile data.
            timestamp: Optional timestamp for time context.

        Returns:
            Complete context dictionary.
        """
        time_context = self.detect_time_context(timestamp)
        urgency = self.detect_urgency(initial_request)
        project_scope = self.detect_project_scope(initial_request)

        family_members = (
            customer_profile.get("family_members", []) if customer_profile else []
        )
        family_presence = self.detect_family_presence(initial_request, family_members)

        logger.info(
            f"Context detected: {project_scope['scope']}, urgency: {urgency['urgency_level']}, time: {time_context['shopping_context']}"
        )

        return {
            "timestamp": (
                timestamp.isoformat() if timestamp else datetime.now().isoformat()
            ),
            "time_context": time_context,
            "urgency": urgency,
            "project_scope": project_scope,
            "family_presence": family_presence,
            "suggested_approach": self._suggest_approach(
                time_context, urgency, project_scope, family_presence
            ),
        }

    def _suggest_approach(
        self,
        time_context: Dict[str, Any],
        urgency: Dict[str, Any],
        project_scope: Dict[str, Any],
        family_presence: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Suggest the best approach based on all context factors.

        Args:
            time_context: Time context information.
            urgency: Urgency information.
            project_scope: Project scope information.
            family_presence: Family presence information.

        Returns:
            Suggested approach dictionary.
        """
        # Determine consultation style
        if project_scope["complexity"] == "high":
            consultation_style = "structured_consultation"
        elif urgency["urgency_level"] == "high":
            consultation_style = "quick_guided"
        elif time_context["availability"] == "low":
            consultation_style = "quick_efficient"
        else:
            consultation_style = "conversational_detailed"

        # Determine tone
        if family_presence["collaborative_decision"]:
            tone = "inclusive_family_friendly"
        elif urgency["urgency_level"] == "high":
            tone = "efficient_helpful"
        elif time_context["mood"] == "relaxed":
            tone = "warm_conversational"
        else:
            tone = "professional_friendly"

        # Determine pacing
        if urgency["urgency_level"] == "high" or time_context["availability"] == "low":
            pacing = "fast"
        elif family_presence["collaborative_decision"]:
            pacing = "patient"  # Allow for discussion
        else:
            pacing = "normal"

        return {
            "consultation_style": consultation_style,
            "tone": tone,
            "pacing": pacing,
            "persona": project_scope.get("suggested_persona", "general_assistant"),
            "interaction_notes": [
                f"Customer availability: {time_context['availability']}",
                f"Project complexity: {project_scope['complexity']}",
                f"Urgency: {urgency['urgency_level']}",
                f"Family collaboration: {family_presence['collaborative_decision']}",
            ],
        }


# Global singleton instance
_context_detector = None


def get_context_detector() -> ContextDetector:
    """Get the global context detector instance."""
    global _context_detector
    if _context_detector is None:
        _context_detector = ContextDetector()
    return _context_detector
