"""
Enhanced consultation with backstage intelligence.
Integrates customer profiles, context detection, and persona system.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from .customer_profile import get_profile_manager
from .context_detector import get_context_detector
from .persona_system import get_persona_system
from .tools import start_home_decor_consultation, continue_home_decor_consultation
from .session_state import get_state_manager
from ...logger import logger


def start_intelligent_consultation(
    customer_id: str,
    initial_request: Optional[str] = None,
    timestamp: Optional[datetime] = None
) -> dict:
    """
    Start a consultation with full backstage intelligence.

    This function:
    1. Loads customer profile and purchase history
    2. Detects time-of-day and contextual factors
    3. Analyzes project scope and complexity
    4. Selects appropriate agent persona
    5. Generates personalized greeting
    6. Routes to appropriate consultation flow

    Args:
        customer_id: The ID of the customer.
        initial_request: Optional initial request from the customer.
        timestamp: Optional timestamp (defaults to now).

    Returns:
        Enhanced consultation response with backstage context.
    """
    logger.info(f"[INTELLIGENT CONSULTATION] Starting for customer {customer_id}")

    # === BACKSTAGE ACTION 1: Load Customer Profile ===
    profile_manager = get_profile_manager()
    customer_profile = profile_manager.get_profile(customer_id)
    context_summary = profile_manager.get_context_summary(customer_id)

    if customer_profile:
        logger.info(f"[PROFILE] Loaded: {customer_profile.get('name')}, {customer_profile.get('loyalty_tier')} tier")
        logger.info(f"[PROFILE] Family members: {len(context_summary.get('family_members', []))}")
        logger.info(f"[PROFILE] Past purchases: {len(customer_profile.get('purchase_history', []))}")

    # === BACKSTAGE ACTION 2: Detect Context ===
    context_detector = get_context_detector()
    full_context = context_detector.get_full_context(
        initial_request=initial_request or "",
        customer_profile=customer_profile,
        timestamp=timestamp
    )

    time_ctx = full_context["time_context"]
    project_scope = full_context["project_scope"]
    urgency = full_context["urgency"]
    family_presence = full_context["family_presence"]

    logger.info(f"[CONTEXT] Time: {time_ctx['shopping_context']}, Day: {time_ctx['day_of_week']}")
    logger.info(f"[CONTEXT] Project: {project_scope['scope']}, Complexity: {project_scope['complexity']}")
    logger.info(f"[CONTEXT] Urgency: {urgency['urgency_level']}, Timeline: {urgency['timeline']}")
    logger.info(f"[CONTEXT] Family collaboration: {family_presence['collaborative_decision']}")

    # === BACKSTAGE ACTION 3: Select Agent Persona ===
    persona_system = get_persona_system()
    selected_persona = persona_system.select_persona(
        project_scope=project_scope["scope"],
        complexity=project_scope["complexity"]
    )

    logger.info(f"[PERSONA] Selected: {selected_persona.name}")

    # === BACKSTAGE ACTION 4: Generate Personalized Greeting ===
    customer_name = customer_profile.get("name", "").split()[0] if customer_profile else None

    # Build context-aware greeting additions
    greeting_context = ""

    # Add time-aware context
    if time_ctx["is_weekend"] and time_ctx["period"] == "morning":
        greeting_context += "Perfect timing for a weekend project! "

    # Add family context
    if family_presence["family_detected"] and family_presence["members_mentioned"]:
        for member in family_presence["members_mentioned"]:
            if member["age_range"] in ["toddler", "school-age"]:
                greeting_context += f"Hello {member['name']}, your first big room upgrade! "

    # Add urgency context
    if urgency["urgency_level"] == "high":
        greeting_context += "I can see this is time-sensitive - let's get started right away! "

    # Add purchase history context
    if customer_profile:
        recent_purchases = profile_manager.get_relevant_purchases(
            customer_id=customer_id,
            category="Furniture"
        )
        if recent_purchases:
            greeting_context += f"I see we've helped with your space before. "

    personalized_greeting = persona_system.get_persona_greeting(
        customer_name=customer_name,
        context=greeting_context
    )

    logger.info(f"[GREETING] {personalized_greeting}")

    # === BACKSTAGE ACTION 5: Pre-fill Known Information ===
    prefilled_data = {}

    # Try to infer age context from family members
    if "bedroom" in (initial_request or "").lower():
        inferred_age = profile_manager.infer_age_context(
            customer_id=customer_id,
            room_type="bedroom"
        )
        if inferred_age:
            prefilled_data["age_context_hint"] = inferred_age
            logger.info(f"[PREFILL] Inferred age context: {inferred_age}")

    # Suggest styles from profile
    if customer_profile:
        style_prefs = profile_manager.get_style_preferences(customer_id)
        if style_prefs:
            prefilled_data["style_suggestions"] = style_prefs
            logger.info(f"[PREFILL] Style preferences from profile: {style_prefs}")

    # === ROUTE TO CONSULTATION ===
    # Start the standard consultation flow
    consultation_result = start_home_decor_consultation(
        customer_id=customer_id,
        initial_request=initial_request
    )

    # === ENHANCE RESPONSE WITH BACKSTAGE CONTEXT ===
    enhanced_response = {
        **consultation_result,
        "backstage_context": {
            "customer_known": context_summary.get("customer_known", False),
            "loyalty_tier": customer_profile.get("loyalty_tier") if customer_profile else None,
            "time_context": time_ctx["shopping_context"],
            "project_complexity": project_scope["complexity"],
            "urgency_level": urgency["urgency_level"],
            "family_collaboration": family_presence["collaborative_decision"],
            "selected_persona": selected_persona.name,
            "interaction_style": full_context["suggested_approach"]["consultation_style"],
            "prefilled_data": prefilled_data
        },
        "personalized_greeting": personalized_greeting,
        "system_instructions": persona_system.get_persona_instructions(),
        "recommended_tools": persona_system.get_recommended_tools()
    }

    # Add style suggestions to the response if available
    if "style_suggestions" in prefilled_data:
        enhanced_response["style_suggestions_from_profile"] = prefilled_data["style_suggestions"]

    # Add age context hint if available
    if "age_context_hint" in prefilled_data:
        enhanced_response["age_context_hint"] = prefilled_data["age_context_hint"]

    # Add family context to message
    if family_presence["collaborative_decision"]:
        if "message" in enhanced_response:
            enhanced_response["message"] = personalized_greeting + "\n\n" + enhanced_response["message"]

    logger.info(f"[CONSULTATION] Started with persona: {selected_persona.name}")

    return enhanced_response


def continue_intelligent_consultation(
    customer_id: str,
    session_id: Optional[str] = None,
    room_type: Optional[str] = None,
    room_purpose: Optional[str] = None,
    age_context: Optional[str] = None,
    constraints: Optional[Dict] = None,
    style_preferences: Optional[list] = None,
    color_preferences: Optional[list] = None
) -> dict:
    """
    Continue consultation with intelligent context awareness.

    Args:
        customer_id: The ID of the customer.
        session_id: The consultation session ID.
        room_type: The room type.
        room_purpose: The room purpose.
        age_context: Age context for the room.
        constraints: Constraints (items to keep/remove).
        style_preferences: Style preferences.
        color_preferences: Color preferences.

    Returns:
        Enhanced consultation response.
    """
    logger.info(f"[INTELLIGENT CONSULTATION] Continuing for customer {customer_id}")

    # Load profile for context
    profile_manager = get_profile_manager()
    customer_profile = profile_manager.get_profile(customer_id)

    # Get session state
    state_manager = get_state_manager()
    session = state_manager.get_session(session_id) if session_id else state_manager.get_customer_session(customer_id)

    # === SMART DEFAULTS ===
    # If age context not provided but can be inferred, suggest it
    if room_type and not age_context and session:
        collected = session.get("collected_data", {})
        if collected.get("room_purpose") == "redesign" and not collected.get("age_context"):
            inferred_age = profile_manager.infer_age_context(customer_id, room_type)
            if inferred_age:
                logger.info(f"[SMART DEFAULT] Suggesting age context: {inferred_age}")
                # Don't auto-fill, but provide as hint in response

    # === STYLE VALIDATION ===
    # If customer has style preferences in profile, validate against new selection
    if style_preferences and customer_profile:
        profile_styles = profile_manager.get_style_preferences(customer_id)
        if profile_styles:
            # Check if new preferences align with historical preferences
            matching = [s for s in style_preferences if s in profile_styles]
            if matching:
                logger.info(f"[STYLE VALIDATION] Matches historical preferences: {matching}")

    # Continue standard consultation
    consultation_result = continue_home_decor_consultation(
        customer_id=customer_id,
        session_id=session_id,
        room_type=room_type,
        room_purpose=room_purpose,
        age_context=age_context,
        constraints=constraints,
        style_preferences=style_preferences,
        color_preferences=color_preferences
    )

    # Enhance with relevant purchase history if moodboard was generated
    if consultation_result.get("status") == "consultation_completed":
        moodboard = consultation_result.get("moodboard", {})
        products = moodboard.get("products", [])

        # Check for complementary items from purchase history
        if customer_profile and room_type:
            relevant_purchases = profile_manager.get_relevant_purchases(
                customer_id=customer_id,
                room_type=room_type
            )

            if relevant_purchases:
                consultation_result["existing_items_in_room"] = [
                    {
                        "name": p["name"],
                        "category": p["category"],
                        "purchased": p["order_date"]
                    }
                    for p in relevant_purchases
                ]
                logger.info(f"[CONTEXT] Found {len(relevant_purchases)} existing items in {room_type}")

    return consultation_result


def get_consultation_context(customer_id: str, session_id: str) -> Dict[str, Any]:
    """
    Get comprehensive context for an ongoing consultation.

    Args:
        customer_id: The customer ID.
        session_id: The session ID.

    Returns:
        Dictionary with all relevant context.
    """
    profile_manager = get_profile_manager()
    state_manager = get_state_manager()
    persona_system = get_persona_system()

    customer_profile = profile_manager.get_profile(customer_id)
    session = state_manager.get_session(session_id)
    current_persona = persona_system.get_current_persona()

    context = {
        "customer": {
            "id": customer_id,
            "name": customer_profile.get("name") if customer_profile else None,
            "loyalty_tier": customer_profile.get("loyalty_tier") if customer_profile else None,
            "family_members": profile_manager.get_family_members(customer_id),
            "style_preferences": profile_manager.get_style_preferences(customer_id)
        },
        "session": {
            "id": session_id,
            "stage": session.get("current_stage") if session else None,
            "collected_data": session.get("collected_data") if session else {},
            "created_at": session.get("created_at") if session else None
        },
        "persona": {
            "name": current_persona.name,
            "description": current_persona.description
        }
    }

    return context
