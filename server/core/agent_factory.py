from config.config import DEMO_TYPE
from core.agents.retail.agent import create_retail_agent
from core.agents.retail.context import RetailContext

from .logger import logger


def get_agent_config():
    agent_config = {"app_name": None, "root_agent": None, "context": None}

    logger.info("===== get_agent_config() called =====")
    print(f"===== get_agent_config() called =====")
    print(f"DEMO_TYPE: {DEMO_TYPE}")

    if DEMO_TYPE == "retail":
        agent_config["app_name"] = "cymbal_retail_assistant"
        agent_config["context"] = RetailContext.CUSTOMER_PROFILE
        # Pass context to agent so prompts are formatted with actual values
        agent_config["root_agent"] = create_retail_agent(context=RetailContext.CUSTOMER_PROFILE)

    else:
        raise ValueError(f"Unknown DEMO_TYPE: `{DEMO_TYPE}`")

    return agent_config
