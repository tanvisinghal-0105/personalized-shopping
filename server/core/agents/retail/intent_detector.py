"""
Intent detection system for routing customer requests to appropriate tools.
This ensures the agent calls the correct tool based on conversation context.
"""

import re
from typing import Dict, Optional, List, Any
from ...logger import logger


class IntentDetector:
    """Detects customer intent and forces appropriate tool calls."""

    # Home decor intent patterns
    HOME_DECOR_KEYWORDS = [
        r"\bdecorate\b",
        r"\bdecorating\b",
        r"\bdecoration\b",
        r"\bredecorate\b",
        r"\bredesign\b",
        r"\bredesigning\b",
        r"\bstyle\b",
        r"\bstyling\b",
        r"\bdesign\b",
        r"\bdesigning\b",
        r"\binterior\b",
        r"\bhome decor\b",
        r"\broom\b",
        r"\bbedroom\b",
        r"\bliving room\b",
        r"\boffice\b",
        r"\bkitchen\b",
        r"\bdining room\b",
        r"\bbathroom\b",
        r"\bspace\b",
        r"\bmoodboard\b",
        r"\btransform\b",
        r"\btransformation\b",
    ]

    # Combine into single pattern
    HOME_DECOR_PATTERN = re.compile(
        "|".join(HOME_DECOR_KEYWORDS), re.IGNORECASE
    )

    @classmethod
    def detect_home_decor_intent(cls, message: str) -> bool:
        """
        Detect if message contains home decor intent.
        Now more conservative - requires explicit action verbs or clear intent.

        Args:
            message: User message text

        Returns:
            True if home decor intent detected
        """
        if not message:
            return False

        message_lower = message.lower()

        # Exclude greetings and introductions
        greeting_patterns = [
            r"\bmy name is\b",
            r"\bi'm\s+\w+",
            r"\bhello\b",
            r"\bhi\b",
            r"\bcustomer\s+id\b",
            r"\bemail\b.*@",
        ]

        for pattern in greeting_patterns:
            if re.search(pattern, message_lower):
                logger.info("[INTENT DETECTOR] Message appears to be greeting/intro - no home decor intent")
                return False

        # Require action words with home decor keywords
        action_patterns = [
            r"\b(want|need|looking|help|can you|could you|would like|planning)\b.*\b(decorate|redesign|design|style|transform|redecorate)",
            r"\b(decorate|redesign|design|style|transform|redecorate)\b.*\b(room|bedroom|living room|office|kitchen|space)",
        ]

        for pattern in action_patterns:
            if re.search(pattern, message_lower):
                logger.info(
                    f"[INTENT DETECTOR] Home decor intent detected with action: '{pattern}'"
                )
                return True

        logger.info("[INTENT DETECTOR] No clear home decor intent detected")
        return False

    @classmethod
    def extract_room_type(cls, message: str) -> Optional[str]:
        """Extract room type from message if present."""
        message_lower = message.lower()

        room_types = {
            "living room": ["living room", "lounge", "sitting room"],
            "bedroom": ["bedroom", "bed room", "master bedroom"],
            "office": ["office", "study", "workspace", "home office"],
            "kitchen": ["kitchen"],
            "dining room": ["dining room", "dining area"],
            "bathroom": ["bathroom", "bath"],
            "entryway": ["entryway", "entry way", "entrance", "foyer"],
        }

        for room, patterns in room_types.items():
            for pattern in patterns:
                if pattern in message_lower:
                    logger.info(
                        f"[INTENT DETECTOR] Extracted room type: {room}"
                    )
                    return room

        return None

    @classmethod
    def extract_style_preferences(cls, message: str) -> Optional[List[str]]:
        """Extract style preferences from message if present."""
        message_lower = message.lower()

        styles = {
            "modern": ["modern", "contemporary"],
            "minimalist": ["minimalist", "minimal", "simple"],
            "bohemian": ["bohemian", "boho", "eclectic"],
            "coastal": ["coastal", "beach", "nautical", "seaside"],
            "industrial": ["industrial", "urban", "loft"],
            "scandinavian": ["scandinavian", "nordic", "scandi"],
            "traditional": ["traditional", "classic", "elegant"],
            "rustic": ["rustic", "farmhouse", "country"],
        }

        detected_styles = []
        for style, patterns in styles.items():
            for pattern in patterns:
                if pattern in message_lower:
                    detected_styles.append(style)
                    break

        if detected_styles:
            logger.info(
                f"[INTENT DETECTOR] Extracted styles: {detected_styles}"
            )

        return detected_styles if detected_styles else None

    @classmethod
    def extract_color_preferences(cls, message: str) -> Optional[List[str]]:
        """Extract color preferences from message if present."""
        message_lower = message.lower()

        # Common color patterns
        colors = [
            "red",
            "blue",
            "green",
            "yellow",
            "orange",
            "purple",
            "pink",
            "brown",
            "black",
            "white",
            "gray",
            "grey",
            "beige",
            "gold",
            "silver",
            "navy",
            "teal",
            "turquoise",
            "cream",
            "ivory",
        ]

        detected_colors = []
        for color in colors:
            if re.search(rf"\b{color}\b", message_lower):
                detected_colors.append(color)

        if detected_colors:
            logger.info(
                f"[INTENT DETECTOR] Extracted colors: {detected_colors}"
            )

        return detected_colors if detected_colors else None

    @classmethod
    def should_force_tool_call(
        cls, message: str, conversation_history: List[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Determine if we should force a specific tool call based on intent.

        Args:
            message: Current user message
            conversation_history: Previous conversation turns

        Returns:
            Dict with tool_name and parameters if tool call should be forced, None otherwise
        """
        # Check for home decor intent
        if cls.detect_home_decor_intent(message):
            logger.info(
                "[INTENT DETECTOR] Forcing start_home_decor_consultation tool call"
            )

            # Extract any information from the message
            room_type = cls.extract_room_type(message)
            style_preferences = cls.extract_style_preferences(message)
            color_preferences = cls.extract_color_preferences(message)

            # If customer has already provided all info in first message, skip consultation
            if room_type and style_preferences:
                logger.info(
                    "[INTENT DETECTOR] Customer provided complete info, calling create_style_moodboard directly"
                )
                return {
                    "tool_name": "create_style_moodboard",
                    "parameters": {
                        "style_preferences": style_preferences,
                        "room_type": room_type,
                        "color_preferences": color_preferences,
                    },
                }

            # Otherwise start the structured consultation
            return {
                "tool_name": "start_home_decor_consultation",
                "parameters": {"initial_request": message},
            }

        return None


# Singleton instance
_detector = IntentDetector()


def get_intent_detector() -> IntentDetector:
    """Get the global intent detector instance."""
    return _detector
