"""
Customer profile management system.
Loads customer data including purchase history, family info, and preferences.
"""

import json
import os
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime
from ...logger import logger


class CustomerProfileManager:
    """Manages customer profiles and purchase history."""

    def __init__(self, profiles_path: Optional[str] = None):
        """
        Initialize the customer profile manager.

        Args:
            profiles_path: Path to the customer profiles JSON file.
                          Defaults to data/customer_profiles.json
        """
        if profiles_path is None:
            # Default to data/customer_profiles.json relative to this file
            base_dir = Path(__file__).parent.parent.parent.parent
            profiles_path = base_dir / "data" / "customer_profiles.json"

        self.profiles_path = profiles_path
        self.profiles: Dict[str, Dict[str, Any]] = {}
        self._load_profiles()

    def _load_profiles(self):
        """Load customer profiles from JSON file."""
        try:
            if os.path.exists(self.profiles_path):
                with open(self.profiles_path, 'r') as f:
                    self.profiles = json.load(f)
                logger.info(f"Loaded {len(self.profiles)} customer profiles")
            else:
                logger.warning(f"Customer profiles file not found: {self.profiles_path}")
                self.profiles = {}
        except Exception as e:
            logger.error(f"Error loading customer profiles: {e}")
            self.profiles = {}

    def get_profile(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a customer profile by ID.

        Args:
            customer_id: The customer ID to look up.

        Returns:
            Customer profile dict or None if not found.
        """
        profile = self.profiles.get(customer_id)
        if profile:
            logger.info(f"Retrieved profile for customer {customer_id}")
        else:
            logger.warning(f"No profile found for customer {customer_id}")
        return profile

    def get_purchase_history(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Get purchase history for a customer.

        Args:
            customer_id: The customer ID to look up.

        Returns:
            List of purchase records.
        """
        profile = self.get_profile(customer_id)
        if profile:
            return profile.get("purchase_history", [])
        return []

    def get_family_members(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Get family members for a customer.

        Args:
            customer_id: The customer ID to look up.

        Returns:
            List of family member records.
        """
        profile = self.get_profile(customer_id)
        if profile:
            return profile.get("family_members", [])
        return []

    def get_home_info(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get home information for a customer.

        Args:
            customer_id: The customer ID to look up.

        Returns:
            Home info dict or None.
        """
        profile = self.get_profile(customer_id)
        if profile:
            return profile.get("home_info")
        return None

    def get_style_preferences(self, customer_id: str) -> List[str]:
        """
        Get historical style preferences for a customer.

        Args:
            customer_id: The customer ID to look up.

        Returns:
            List of preferred styles.
        """
        home_info = self.get_home_info(customer_id)
        if home_info:
            return home_info.get("style_preferences", [])
        return []

    def infer_age_context(self, customer_id: str, room_type: str) -> Optional[str]:
        """
        Infer age context based on family members and room type.

        Args:
            customer_id: The customer ID.
            room_type: The room type being decorated (e.g., "bedroom").

        Returns:
            Age context string (toddler, school-age, teen, adult) or None.
        """
        family_members = self.get_family_members(customer_id)

        # If it's a child's bedroom, infer from family members
        if "bedroom" in room_type.lower():
            children = [m for m in family_members if m.get("relationship") in ["daughter", "son", "child"]]

            if len(children) == 1:
                # Single child - use their age range
                return children[0].get("age_range")
            elif len(children) > 1:
                # Multiple children - would need more context
                logger.info(f"Multiple children found for {customer_id}, cannot auto-infer age context")
                return None

        # For office/workspace, assume adult
        if "office" in room_type.lower() or "workspace" in room_type.lower():
            return "adult"

        return None

    def get_relevant_purchases(
        self,
        customer_id: str,
        room_type: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get relevant past purchases filtered by room or category.

        Args:
            customer_id: The customer ID.
            room_type: Optional room type filter.
            category: Optional category filter.

        Returns:
            List of relevant purchase items.
        """
        history = self.get_purchase_history(customer_id)
        relevant_items = []

        for order in history:
            for item in order.get("items", []):
                # Apply filters
                if room_type and item.get("room") != room_type:
                    continue
                if category and item.get("category") != category:
                    continue

                # Add order context to item
                relevant_items.append({
                    **item,
                    "order_date": order.get("date"),
                    "order_id": order.get("order_id")
                })

        return relevant_items

    def get_personalized_greeting(self, customer_id: str) -> str:
        """
        Generate a personalized greeting for the customer.

        Args:
            customer_id: The customer ID.

        Returns:
            Personalized greeting string.
        """
        profile = self.get_profile(customer_id)
        if not profile:
            return "Hello! How can I help you today?"

        name = profile.get("name", "there").split()[0]  # First name
        tier = profile.get("loyalty_tier", "")
        family_members = self.get_family_members(customer_id)

        greeting = f"Hello, {name}!"

        # Add family context if applicable
        if family_members:
            family_names = [m.get("name") for m in family_members if m.get("name")]
            if len(family_names) == 1:
                greeting = f"Hello, {name}! Is {family_names[0]} around?"
            elif len(family_names) > 1:
                greeting = f"Hello, {name}! Great to see you again."

        # Add tier context
        if tier == "Platinum":
            greeting += " Thank you for being a valued Platinum member."
        elif tier == "Gold":
            greeting += " Always a pleasure to assist our Gold members."

        return greeting

    def get_context_summary(self, customer_id: str) -> Dict[str, Any]:
        """
        Get a comprehensive context summary for the customer.

        Args:
            customer_id: The customer ID.

        Returns:
            Dictionary with relevant context for personalization.
        """
        profile = self.get_profile(customer_id)
        if not profile:
            return {
                "customer_known": False,
                "greeting": "Hello! How can I help you today?"
            }

        return {
            "customer_known": True,
            "name": profile.get("name"),
            "loyalty_tier": profile.get("loyalty_tier"),
            "family_members": self.get_family_members(customer_id),
            "home_info": self.get_home_info(customer_id),
            "style_preferences": self.get_style_preferences(customer_id),
            "recent_purchases": self.get_purchase_history(customer_id)[-3:],  # Last 3 orders
            "greeting": self.get_personalized_greeting(customer_id),
            "preferred_communication": profile.get("preferences", {}).get("communication_channel", "voice"),
            "values": profile.get("preferences", {}).get("values", [])
        }


# Global singleton instance
_profile_manager = None


def get_profile_manager() -> CustomerProfileManager:
    """Get the global profile manager instance."""
    global _profile_manager
    if _profile_manager is None:
        _profile_manager = CustomerProfileManager()
    return _profile_manager
