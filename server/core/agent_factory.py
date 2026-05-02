from config.config import DEMO_TYPE
from core.agents.retail.agent import create_retail_agent
from core.agents.retail.context import RetailContext, create_customer_profile
from core.agents.retail.customer_profile import get_profile_manager
from core.agents.retail.context_detector import get_context_detector
from core.agents.retail.persona_system import get_persona_system
from datetime import datetime

from .logger import logger


def get_agent_config(customer_id=None, first_name=None, last_name=None, email=None):
    """
    Get agent configuration with optional customer personalization.

    Args:
        customer_id: Customer ID (e.g., "CY-1234-5678")
        first_name: Customer's first name
        last_name: Customer's last name
        email: Customer's email address

    Returns:
        dict: Agent configuration with app_name, root_agent, and context
    """
    agent_config = {"app_name": None, "root_agent": None, "context": None}

    logger.info("===== get_agent_config() called =====")
    print("===== get_agent_config() called =====")
    print(f"DEMO_TYPE: {DEMO_TYPE}")

    if DEMO_TYPE == "retail":
        agent_config["app_name"] = "cymbal_retail_assistant"

        # Create basic customer profile for legacy context
        if customer_id or first_name or last_name or email:
            logger.info(
                f"Creating personalized profile for customer: {first_name} {last_name} ({customer_id})"
            )
            customer_profile = create_customer_profile(
                customer_id=customer_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
            )
        else:
            logger.info("Using default customer profile")
            customer_profile = RetailContext.CUSTOMER_PROFILE

        # ===== BACKSTAGE INTELLIGENCE =====
        # Load enhanced customer profile if customer_id is provided
        enhanced_profile = None
        backstage_context = {}
        personalized_greeting = None
        custom_instructions = None

        if customer_id:
            try:
                logger.info(f"[BACKSTAGE] Loading enhanced profile for {customer_id}")

                # 1. Load customer profile from JSON
                profile_manager = get_profile_manager()
                enhanced_profile = profile_manager.get_profile(customer_id)

                if enhanced_profile:
                    logger.info(
                        f"[BACKSTAGE] Profile loaded: {enhanced_profile.get('name')}, {enhanced_profile.get('loyalty_tier')} tier"
                    )

                    # 2. Detect context (time, urgency, family)
                    context_detector = get_context_detector()
                    full_context = context_detector.get_full_context(
                        initial_request="",  # Will be filled in by first message
                        customer_profile=enhanced_profile,
                        timestamp=datetime.now(),
                    )
                    logger.info(
                        f"[BACKSTAGE] Context detected: {full_context['time_context']['shopping_context']}"
                    )

                    # 3. Select persona based on context
                    persona_system = get_persona_system()
                    selected_persona = persona_system.select_persona(
                        project_scope=full_context["project_scope"]["scope"],
                        complexity=full_context["project_scope"]["complexity"],
                    )
                    logger.info(
                        f"[BACKSTAGE] Persona selected: {persona_system.current_persona}"
                    )

                    # 4. Generate personalized greeting
                    customer_name = enhanced_profile.get("name", "").split()[0]
                    greeting_context = {
                        "time_context": full_context["time_context"][
                            "shopping_context"
                        ],
                        "loyalty_tier": enhanced_profile.get("loyalty_tier"),
                        "has_purchase_history": len(
                            enhanced_profile.get("purchase_history", [])
                        )
                        > 0,
                    }
                    personalized_greeting = persona_system.get_persona_greeting(
                        customer_name=customer_name, context=greeting_context
                    )
                    logger.info(
                        f"[BACKSTAGE] Greeting generated: {personalized_greeting[:50]}..."
                    )

                    # 5. Get persona-specific instructions
                    custom_instructions = selected_persona.get_system_instructions()

                    # 6. Store backstage context for agent
                    backstage_context = {
                        "customer_profile": enhanced_profile,
                        "full_context": full_context,
                        "selected_persona": persona_system.current_persona,
                        "personalized_greeting": personalized_greeting,
                    }

                    # Merge enhanced profile data into customer_profile context
                    customer_profile["style_preferences"] = enhanced_profile.get(
                        "home_info", {}
                    ).get("style_preferences", [])
                    customer_profile["loyalty_tier"] = enhanced_profile.get(
                        "loyalty_tier"
                    )
                    customer_profile["customer_name"] = enhanced_profile.get("name")

                else:
                    logger.info(
                        f"[BACKSTAGE] No enhanced profile found for {customer_id}, using basic profile"
                    )

            except Exception as e:
                logger.error(f"[BACKSTAGE] Error loading enhanced profile: {e}")
                import traceback

                traceback.print_exc()
        # ===== END BACKSTAGE INTELLIGENCE =====

        agent_config["context"] = customer_profile
        agent_config["backstage_context"] = backstage_context  # Store for later use
        agent_config["personalized_greeting"] = personalized_greeting

        # Pass context to agent so prompts are formatted with actual values
        # Use custom instructions if persona was selected
        if custom_instructions:
            agent_config["root_agent"] = create_retail_agent(
                context=customer_profile, instruction=custom_instructions
            )
        else:
            agent_config["root_agent"] = create_retail_agent(context=customer_profile)

    else:
        raise ValueError(f"Unknown DEMO_TYPE: `{DEMO_TYPE}`")

    return agent_config
