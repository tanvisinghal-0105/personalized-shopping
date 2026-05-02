from typing import Any, List, Dict, Optional
from google.adk.agents import Agent
from google.adk.tools import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types as genai_types

from config.config import AGENT_MODEL
from .prompts import Prompts
from ...session_utils import SessionUtils
from ...logger import logger
from .intent_detector import get_intent_detector

from .tools import (
    send_call_companion_link,
    approve_discount,
    sync_ask_for_approval,
    access_cart_information,
    modify_cart,
    identify_phone_from_camera_feed,
    get_product_recommendations,
    check_product_availability,
    schedule_service_appointment,
    get_available_service_times,
    generate_qr_code,
    process_exchange_request,
    get_trade_in_value,
    lookup_warranty_details,
    display_product_search_results,
    create_style_moodboard,
    start_home_decor_consultation,
    continue_home_decor_consultation,
    analyze_room_for_decor,
    analyze_room_with_history,
    analyze_room_photos_batch,
    get_customer_order_history,
    visualize_room_with_products,
)


# ---------------------------------------------------------------------------
# Sub-agent instruction prompts
# ---------------------------------------------------------------------------

SHOPPING_AGENT_INSTRUCTION = (
    "You are the Shopping sub-agent for Cymbal retail store. "
    "You handle product browsing, cart management, recommendations, "
    "availability checks, and discount approvals.\n\n"
    "**IMPORTANT - Product Knowledge:**\n"
    "You have access to the full product catalog in your context. "
    "When a customer asks for a product recommendation (e.g. 'something "
    "stronger', 'a better case', 'a premium option'), look up the relevant "
    "product directly from the available_products catalog and recommend it "
    "by name, price, and product_id. Do NOT call display_product_search_results "
    "for simple recommendations -- just tell the customer about the product "
    "and offer to add it to cart.\n\n"
    "For example, if a customer has a Generic Google Pixel Case and asks for "
    "something more protective, recommend the Google Pixel 9 Pro Defender "
    "Series Case (GOOGLE-PIXEL9PRO-CASE, 59.99 EUR) directly.\n\n"
    "**Capabilities:**\n"
    "1. Access and display the customer's shopping cart using "
    "`access_cart_information`.\n"
    "2. Modify the cart (add/remove items) using `modify_cart`.\n"
    "   - `items_to_add`: list of dicts with 'product_id' (required) and "
    "'quantity' (optional, defaults to 1).\n"
    "   - `items_to_remove`: list of product_id strings.\n"
    "   - CRITICAL: product_id must be an EXACT match from the "
    "available_products catalog. Never modify or create product IDs.\n"
    "   - Always provide at least one of items_to_add or items_to_remove.\n"
    "3. Recommend products using `get_product_recommendations` based on "
    "customer interests or current cart.\n"
    "4. Check stock with `check_product_availability`.\n"
    "5. Show visual product cards using `display_product_search_results` "
    "ONLY when customers want to browse an entire category (e.g. 'show me "
    "all TVs', 'what laptops do you have').\n"
    "6. Handle discount requests ONLY via `sync_ask_for_approval` -- "
    "you cannot approve discounts yourself.\n\n"
    "**Constraints:**\n"
    "- Use markdown for tables.\n"
    "- Never mention tool_code or tool_outputs to the user.\n"
    "- Always mention exact price (EUR) from the catalog.\n"
    "- ONLY use product_id values that appear EXACTLY in the "
    "available_products catalog. Never hallucinate IDs.\n"
)

HOME_DECOR_AGENT_INSTRUCTION = (
    "You are the Home Decor sub-agent for Cymbal retail store. "
    "You specialize in home decoration consultations, room analysis, "
    "and style moodboard creation.\n\n"
    "**Structured Consultation Flow:**\n\n"
    "Step 1 - START: When a customer mentions decorating/styling/room design, "
    "call `start_home_decor_consultation(customer_id, initial_request)`. "
    "This returns the first question. Do NOT ask questions yourself -- "
    "let the tool guide the conversation.\n\n"
    "Step 2 - CONTINUE: As the customer provides answers (room type, styles, "
    "colors), call `continue_home_decor_consultation(...)` with all collected "
    "info. The tool returns the next question OR the completed moodboard.\n"
    "- CRITICAL: You MUST call this tool. Do NOT describe products from memory.\n"
    "- NEVER say 'I have created a moodboard' without calling the tool first.\n\n"
    "Step 3 - PRESENT RESULTS: When `continue_home_decor_consultation` returns "
    "status='consultation_completed', present the moodboard products, explain "
    "why each fits, and mention the 'Visualize in my room' button. "
    "Offer to add items to cart.\n\n"
    "Step 3b - ROOM VISUALIZATION: When a customer clicks 'Visualize in my "
    "room', `visualize_room_with_products` generates a photorealistic rendering "
    "using Imagen 4 Ultra. Present the result enthusiastically.\n\n"
    "Step 4 - POST-MOODBOARD: The conversation does NOT end after the "
    "moodboard. Customers can ask questions, request changes, or add items "
    "to cart. If they want changes, call `create_style_moodboard` again "
    "with updated preferences.\n\n"
    "**Child Bedroom Flow:** When age_context = toddler/school-age/teen, "
    "address the child directly and warmly. The tool shows child-themed tiles "
    "(Underwater World, Forest Adventure, etc.) instead of adult styles.\n\n"
    "**Camera/Photo Handling:**\n"
    "- Images appear directly in your visual context (NOT as tool parameters).\n"
    "- When you SEE room photos, IMMEDIATELY call "
    "`analyze_room_for_decor(customer_id=..., room_type_hint=...)` "
    "without image_data.\n"
    "- NEVER ask for 'clearer photos' -- always call the tool first.\n"
    "- Use `analyze_room_with_history` when there is an active session.\n"
    "- Use `analyze_room_photos_batch` for multiple photos.\n\n"
    "**Constraints:**\n"
    "- Use markdown for tables.\n"
    "- Never mention tool_code or tool_outputs to the user.\n"
    "- ONLY use product_id values from the available_products catalog. "
    "Never hallucinate IDs.\n"
)

SERVICES_AGENT_INSTRUCTION = (
    "You are the Services sub-agent for Cymbal retail store. "
    "You handle warranties, trade-ins, exchanges, appointments, "
    "and companion links.\n\n"
    "**Capabilities:**\n"
    "1. **Exchanges:** Process product exchange requests using "
    "`process_exchange_request`, adhering to return policies.\n"
    "2. **Warranty:** Look up warranty details using `lookup_warranty_details` "
    "by product_id, serial_number, or order_id.\n"
    "3. **Trade-ins:** Provide trade-in value estimates using "
    "`get_trade_in_value` with product_category, brand, model, "
    "and condition.\n"
    "4. **Appointments:** Schedule service appointments using "
    "`schedule_service_appointment` and check available times using "
    "`get_available_service_times`.\n"
    "5. **QR Codes:** Generate QR codes for receipts, labels, or links "
    "using `generate_qr_code`.\n"
    "6. **Companion Links:** Send call companion links using "
    "`send_call_companion_link`.\n\n"
    "**Constraints:**\n"
    "- Use markdown for tables.\n"
    "- Never mention tool_code or tool_outputs to the user.\n"
    "- Always mention exact prices (EUR) from the catalog when relevant.\n"
    "- Be proactive in suggesting relevant services (e.g., warranty for "
    "new purchases, trade-in for upgrades).\n"
)

ROOT_AGENT_INSTRUCTION = (
    "You are the primary AI assistant for Cymbal, a leading retail store. "
    "Your role is to understand customer intent and route requests to the "
    "appropriate specialist sub-agent.\n\n"
    "You orchestrate three specialist sub-agents:\n"
    "1. **shopping_agent** -- handles product browsing, cart operations, "
    "recommendations, availability, and discount approvals.\n"
    "2. **home_decor_agent** -- handles home decoration consultations, "
    "room analysis, moodboard creation, and room visualization.\n"
    "3. **services_agent** -- handles warranties, trade-ins, exchanges, "
    "service appointments, QR codes, and companion links.\n\n"
    "**Routing Guidelines:**\n"
    "- Shopping/products/cart/recommendations/discounts --> transfer to "
    "shopping_agent\n"
    "- Home decor/decorating/room design/moodboard/room photos --> transfer "
    "to home_decor_agent\n"
    "- Warranty/trade-in/exchange/appointment/QR code/companion link --> "
    "transfer to services_agent\n"
    "- General greetings and questions: handle directly with a friendly, "
    "helpful tone. Greet returning customers by name.\n\n"
    "**Important:**\n"
    "- Use the customer profile to personalize interactions.\n"
    "- Maintain a friendly, empathetic tone.\n"
    "- When in doubt about routing, ask clarifying questions.\n"
    "- Never mention internal tool names or sub-agent names to the customer.\n"
)


# ---------------------------------------------------------------------------
# Callbacks (unchanged)
# ---------------------------------------------------------------------------


def intent_interceptor(user_message: str, tool_context: ToolContext) -> Optional[str]:
    """
    Intercepts user messages BEFORE the model processes them.
    Modifies the message to force appropriate tool calls based on detected intent.

    Returns: Modified message string, or None to use original message
    """
    logger.info("[INTENT INTERCEPTOR] ===== CALLBACK FIRED =====")
    logger.info(f"[INTENT INTERCEPTOR] Analyzing message: '{user_message}'")
    logger.info(
        f"[INTENT INTERCEPTOR] Tool context state keys: {list(tool_context.state.keys())}"
    )

    # Check if there's already an active home decor consultation
    from .session_state import get_state_manager

    customer_id = tool_context.state.get("customer_id", "CY-DEFAULT")
    state_manager = get_state_manager()
    existing_session = state_manager.get_customer_session(customer_id)

    if existing_session and not existing_session.get("moodboard_generated", False):
        logger.info(
            f"[INTENT INTERCEPTOR] Active home decor session exists "
            f"(session_id: {existing_session['session_id']})"
        )
        logger.info(
            "[INTENT INTERCEPTOR] Allowing agent to handle message naturally "
            "- NOT forcing tool call"
        )
        return None

    intent_detector = get_intent_detector()

    # Check if we should force a tool call
    forced_call = intent_detector.should_force_tool_call(user_message)

    if forced_call:
        tool_name = forced_call["tool_name"]
        parameters = forced_call["parameters"]

        logger.info("[INTENT INTERCEPTOR] ===== HOME DECOR INTENT DETECTED =====")
        logger.info(f"[INTENT INTERCEPTOR] Forcing tool call: {tool_name}")
        logger.info(f"[INTENT INTERCEPTOR] Parameters: {parameters}")
        logger.info(f"[INTENT INTERCEPTOR] Customer ID: {customer_id}")

        modified_message = (
            "URGENT: The customer just asked about home decoration.\n\n"
            f'Original request: "{user_message}"\n\n'
            f"YOU MUST IMMEDIATELY call the {tool_name} tool with these parameters:\n"
            f'- customer_id: "{customer_id}"\n'
            f'- initial_request: "{user_message}"\n\n'
            "DO NOT respond with text. DO NOT ask questions. JUST CALL THE TOOL NOW.\n"
            f'Call {tool_name}(customer_id="{customer_id}", '
            f'initial_request="{user_message}")'
        )

        logger.info(
            f"[INTENT INTERCEPTOR] Modified message: {modified_message[:200]}..."
        )
        return modified_message

    logger.info(
        "[INTENT INTERCEPTOR] No home decor intent detected - message unchanged"
    )
    return None


def logic_check(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext
) -> Optional[Dict]:
    """
    Check for the next tool call and then act accordingly.
    The function signature has been updated to match the new ADK.
    """
    logger.info(f"Executing before_tool_callback for tool: {tool.name}")

    # All discount approvals must go through the CRM -- no auto-approve
    # The sync_ask_for_approval tool will create a pending request in Firestore
    # and poll until the manager approves via the CRM dashboard.

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


# ---------------------------------------------------------------------------
# Generation config (shared across all agents)
# ---------------------------------------------------------------------------


def _make_gen_config() -> genai_types.GenerateContentConfig:
    """Create the shared generation config for all agents."""
    safety_settings = [
        genai_types.SafetySetting(
            category="HARM_CATEGORY_HARASSMENT",
            threshold="BLOCK_MEDIUM_AND_ABOVE",
        ),
        genai_types.SafetySetting(
            category="HARM_CATEGORY_HATE_SPEECH",
            threshold="BLOCK_MEDIUM_AND_ABOVE",
        ),
        genai_types.SafetySetting(
            category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
            threshold="BLOCK_ONLY_HIGH",
        ),
        genai_types.SafetySetting(
            category="HARM_CATEGORY_DANGEROUS_CONTENT",
            threshold="BLOCK_MEDIUM_AND_ABOVE",
        ),
    ]

    return genai_types.GenerateContentConfig(
        temperature=0.2,
        top_p=0.9,
        top_k=40,
        max_output_tokens=2048,
        safety_settings=safety_settings,
    )


# ---------------------------------------------------------------------------
# Sub-agent constructors
# ---------------------------------------------------------------------------


def _create_shopping_agent(model: Any) -> Agent:
    """Create the Shopping sub-agent for cart, recommendations, and availability."""
    return Agent(
        model=model,
        name="shopping_agent",
        instruction=SHOPPING_AGENT_INSTRUCTION,
        tools=[
            access_cart_information,
            modify_cart,
            identify_phone_from_camera_feed,
            get_product_recommendations,
            check_product_availability,
            display_product_search_results,
            sync_ask_for_approval,
        ],
        generate_content_config=_make_gen_config(),
    )


def _create_home_decor_agent(model: Any) -> Agent:
    """Create the Home Decor sub-agent for consultations and room analysis."""
    return Agent(
        model=model,
        name="home_decor_agent",
        instruction=HOME_DECOR_AGENT_INSTRUCTION,
        tools=[
            start_home_decor_consultation,
            continue_home_decor_consultation,
            create_style_moodboard,
            analyze_room_for_decor,
            analyze_room_with_history,
            analyze_room_photos_batch,
            get_customer_order_history,
            visualize_room_with_products,
        ],
        generate_content_config=_make_gen_config(),
    )


def _create_services_agent(model: Any) -> Agent:
    """Create the Services sub-agent for warranties, trade-ins, and appointments."""
    return Agent(
        model=model,
        name="services_agent",
        instruction=SERVICES_AGENT_INSTRUCTION,
        tools=[
            lookup_warranty_details,
            get_trade_in_value,
            schedule_service_appointment,
            get_available_service_times,
            process_exchange_request,
            generate_qr_code,
            send_call_companion_link,
        ],
        generate_content_config=_make_gen_config(),
    )


# ---------------------------------------------------------------------------
# Public factory (signature unchanged)
# ---------------------------------------------------------------------------


def create_retail_agent(
    model: Any = AGENT_MODEL,
    name: str = "cymbal_retail_agent",
    global_instructions: str = Prompts.GLOBAL_PROMPT,
    instruction: str = None,
    tools: List[BaseTool] = [],
    sub_agents: List[Agent] = [],
    context: Dict[str, Any] = None,
) -> Agent:
    """Factory method to create a configured cymbalCustomerServiceRetailAgent.

    Returns a root orchestrator agent with three sub-agents:
    - shopping_agent: cart, recommendations, availability, discounts
    - home_decor_agent: consultation flow, room analysis, moodboards
    - services_agent: warranties, trade-ins, exchanges, appointments
    """

    # Log context if provided
    if context:
        logger.info(f"Context provided with keys: {list(context.keys())}")
        logger.info(
            f"Product catalog has {len(context.get('product_catalog_raw', []))} products"
        )

    # Build the three sub-agents
    shopping_agent = _create_shopping_agent(model)
    home_decor_agent = _create_home_decor_agent(model)
    services_agent = _create_services_agent(model)

    # Merge any extra sub-agents passed by the caller
    default_sub_agents = [shopping_agent, home_decor_agent, services_agent]
    final_sub_agents = SessionUtils.dedupe_lists(default_sub_agents, sub_agents)

    # Use the provided instruction or fall back to the root orchestrator prompt
    root_instruction = (
        instruction if instruction is not None else ROOT_AGENT_INSTRUCTION
    )

    # Any extra tools passed by the caller go on the root agent
    final_tools = list(tools) if tools else []

    # Note: Context caching is configured at the App level, not Agent level
    # See websocket_handler.py for App-level configuration

    agent = Agent(
        model=model,
        name=name,
        global_instruction=global_instructions,
        instruction=root_instruction,
        tools=final_tools,
        sub_agents=final_sub_agents,
        generate_content_config=_make_gen_config(),
        output_key="retail_agent_final_response",
    )

    # Add callbacks
    agent.before_tool_callback = logic_check
    agent.after_tool_callback = None

    agent.before_agent_callback = None
    agent.after_agent_callback = None

    # CRITICAL: Intent interceptor runs BEFORE the model processes the message
    # This ensures home decor requests trigger the correct tool immediately
    agent.before_model_callback = intent_interceptor
    agent.after_model_callback = None

    # Log agent creation for debugging/info purposes
    logger.info(
        f"Agent '{agent.name}' created with {len(final_sub_agents)} sub-agents "
        f"(shopping_agent, home_decor_agent, services_agent)."
    )

    return agent


class AgentModule:
    def __init__(self):
        self.root_agent = create_retail_agent()


# Agent instance is created in agent_factory.py, not here
