from typing import Any, List, Dict, Optional
from google.adk.agents import Agent
from google.adk.tools import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.adk.agents.callback_context import CallbackContext
from google.genai import types as genai_types

from config.config import AGENT_MODEL
from .prompts import Prompts
from ...session_utils import SessionUtils
from ...logger import logger

from .tools import (
    send_call_companion_link,
    approve_discount,
    sync_ask_for_approval,
    access_cart_information,
    modify_cart,
    get_product_recommendations,
    check_product_availability,
    schedule_service_appointment,
    get_available_service_times,
    send_product_information,
    generate_qr_code,
    process_exchange_request,
    get_trade_in_value,
    lookup_warranty_details,
    identify_phone_from_camera_feed
)

def logic_check(tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext) -> Optional[Dict]:
    """
    Check for the next tool call and then act accordingly.
    The function signature has been updated to match the new ADK.
    """
    logger.info(f"Executing before_tool_callback for tool: {tool.name}")
    
    if tool.name == "sync_ask_for_approval":
        amount = args.get("value")
        if amount is not None and amount <= 10:
            reason = args.get("reason", "").lower()
            if "10%" in reason or "preferred care" in reason:
                tool_context.state["temp:discount_approved"] = True
                tool_context.state["user:pixel_9_pro_charger_info"] = "The Pixel 9 Pro does not include a charger. Suggest the 30W adapter as a solution."
                return {"result": "You can approve this discount; no manager needed. In addition, make sure to inform the user that the pixel 9 pro does not include a charger. Suggest the 30W adapter as a solution."}
            else:
                tool_context.state["temp:discount_approved"] = True
                return {"result": "You can approve this discount; no manager needed."}

    if tool.name == "modify_cart":
        items_added = args.get("items_added")
        items_removed = args.get("items_removed")
        if items_added and items_removed:
            return {"result": "I have added and removed the requested items."}
        elif items_added:
            return {"result": "I have added the requested items."}
        elif items_removed:
            return {"result": "I have removed the requested items."}
    
    return None


def create_retail_agent(
        model: Any = AGENT_MODEL,
        name: str = "cymbal_retail_agent",
        global_instructions: str = Prompts.GLOBAL_PROMPT,
        instruction: str = Prompts.RETAIL_ASSIST_MAIN,
        tools: List[BaseTool] = [],
        sub_agents: List[Agent] = []
        ) -> Agent:
    """Factory method to create a configured cymbalCustomerServiceRetailAgent."""

    default_tools = [
        send_call_companion_link,
        approve_discount,
        sync_ask_for_approval,
        access_cart_information,
        modify_cart,
        get_product_recommendations,
        check_product_availability,
        schedule_service_appointment,
        send_product_information,
        get_available_service_times,
        generate_qr_code,
        process_exchange_request,
        get_trade_in_value,
        lookup_warranty_details,
        identify_phone_from_camera_feed,
        ]
    default_sub_agents = []

    final_tools = SessionUtils.dedupe_lists(default_tools, tools)
    final_sub_agents = SessionUtils.dedupe_lists(default_sub_agents, sub_agents)

    # Enhanced generation config with latest features
    gen_config = genai_types.GenerateContentConfig(
        temperature=0.2,
        top_p=0.9,
        top_k=40,
        max_output_tokens=2048  # Increased for better responses
    )

    # Note: Context caching is configured at the App level, not Agent level
    # See websocket_handler.py for App-level configuration

    agent = Agent(
        model=model,
        name=name,
        global_instruction=global_instructions,
        instruction=instruction,
        tools=final_tools,
        sub_agents=final_sub_agents,
        generate_content_config=gen_config,
        output_key="retail_agent_final_response",
    )

    # Add callbacks
    agent.before_tool_callback = logic_check
    agent.after_tool_callback = None

    agent.before_agent_callback = None
    agent.after_agent_callback = None

    agent.before_model_callback = None
    agent.after_model_callback = None

    # Log agent creation for debugging/info purposes
    logger.info(f"Agent \'{agent.name}\' created with {len(agent.tools)} tools.")

    return agent

class AgentModule:
    def __init__(self):
        
        self.root_agent = create_retail_agent()

agent = AgentModule()

agent = AgentModule()



