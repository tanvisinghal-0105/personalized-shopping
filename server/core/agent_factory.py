from config.config import DEMO_TYPE
from core.agents.retail.agent import create_retail_agent
from core.agents.retail.context import RetailContext, create_customer_profile

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

        # Create personalized customer profile if customer info is provided
        if customer_id or first_name or last_name or email:
            logger.info(f"Creating personalized profile for customer: {first_name} {last_name} ({customer_id})")
            customer_profile = create_customer_profile(
                customer_id=customer_id,
                first_name=first_name,
                last_name=last_name,
                email=email
            )
        else:
            logger.info("Using default customer profile")
            customer_profile = RetailContext.CUSTOMER_PROFILE

        agent_config["context"] = customer_profile
        # Pass context to agent so prompts are formatted with actual values
        agent_config["root_agent"] = create_retail_agent(context=customer_profile)

    else:
        raise ValueError(f"Unknown DEMO_TYPE: `{DEMO_TYPE}`")

    return agent_config
