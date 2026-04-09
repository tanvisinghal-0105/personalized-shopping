"""
WebSocket message handling from the client/frontend to proxy and from proxy to the live Agent
"""

import json
import asyncio
import base64
import traceback
import datetime
from typing import Any, Optional, Dict

from google.genai import types
from google.adk.agents.run_config import RunConfig
from google.adk.runners import InMemoryRunner
from google.adk.agents import LiveRequestQueue
from google.genai.types import (
    Part,
    Content,
    Blob,
)

from core.agent_factory import get_agent_config
from .logger import logger
from config.config import (
    CONFIG,
    VAD_ENABLED,
    VAD_START_SENSITIVITY,
    VAD_END_SENSITIVITY,
    VAD_PREFIX_PADDING_MS,
    VAD_SILENCE_DURATION_MS,
    ALLOW_INTERRUPTION,
)
from core.agents.retail.intent_detector import get_intent_detector

# Global session storage now holds the request queue for each session.
ACTIVE_SESSIONS: Dict[str, LiveRequestQueue] = {}
# Global session context storage for customer info
SESSION_CONTEXTS: Dict[str, Dict[str, Any]] = {}


async def send_error_message(websocket: Any, error_data: dict) -> None:
    """
    Sends a formatted error message to the client via the websocket connection.
    """
    try:
        await websocket.send(json.dumps({"type": "error", "data": error_data}))
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")


async def start_agent_session(
    user_id: str,
    run_config: RunConfig,
    initial_session_state: Dict[str, Any],
    agent_config: dict,
) -> tuple[Any, LiveRequestQueue]:
    """Starts an agent session with a new runner and request queue."""
    root_agent = agent_config.get("root_agent")
    app_name = agent_config.get("app_name")

    runner = InMemoryRunner(
        app_name=app_name,
        agent=root_agent,
    )

    session_obj = await runner.session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        state=initial_session_state,
    )

    live_request_queue = LiveRequestQueue()

    live_events = runner.run_live(
        session=session_obj,
        live_request_queue=live_request_queue,
        run_config=run_config,
    )
    return live_events, live_request_queue


async def create_session(
    session_id: str, context: Dict[str, Any], agent_config: dict
) -> Any:
    """
    Creates and stores a new session, leveraging the new ADK live session runner.
    """
    response_modalities_from_config = CONFIG["generation_config"][
        "response_modalities"
    ]

    print(f"Voice: {CONFIG['generation_config']['speech_config']}")
    print(
        f"Modalities for session {session_id} (from CONFIG): {response_modalities_from_config}"
    )

    # Configure Voice Activity Detection (VAD) for interruption handling
    vad_config = None
    if VAD_ENABLED:
        # Map string sensitivity to enum values
        start_sensitivity = (
            types.StartSensitivity.START_SENSITIVITY_HIGH
            if VAD_START_SENSITIVITY == "HIGH"
            else types.StartSensitivity.START_SENSITIVITY_LOW
        )
        end_sensitivity = (
            types.EndSensitivity.END_SENSITIVITY_HIGH
            if VAD_END_SENSITIVITY == "HIGH"
            else types.EndSensitivity.END_SENSITIVITY_LOW
        )

        vad_config = types.AutomaticActivityDetection(
            disabled=False,
            start_of_speech_sensitivity=start_sensitivity,
            end_of_speech_sensitivity=end_sensitivity,
            prefix_padding_ms=VAD_PREFIX_PADDING_MS,
            silence_duration_ms=VAD_SILENCE_DURATION_MS,
        )
        logger.info(
            f"VAD configured - Start: {VAD_START_SENSITIVITY}, End: {VAD_END_SENSITIVITY}, "
            f"Padding: {VAD_PREFIX_PADDING_MS}ms, Silence: {VAD_SILENCE_DURATION_MS}ms"
        )
    else:
        vad_config = types.AutomaticActivityDetection(disabled=True)
        logger.info("VAD disabled - manual activity control required")

    # Configure realtime input with VAD settings
    realtime_config = types.RealtimeInputConfig(
        automatic_activity_detection=vad_config
    )

    # Set activity handling based on interruption configuration
    if not ALLOW_INTERRUPTION:
        realtime_config.activity_handling = (
            types.ActivityHandling.NO_INTERRUPTION
        )
        logger.info(
            "Interruptions disabled - model responses cannot be interrupted"
        )

    run_config = RunConfig(
        response_modalities=response_modalities_from_config,
        realtime_input_config=realtime_config,
    )

    live_events, live_request_queue = await start_agent_session(
        session_id, run_config, context, agent_config
    )

    ACTIVE_SESSIONS[session_id] = live_request_queue
    logger.info(f"Session {session_id} created with new ADK runner.")
    return live_events


def get_session_request_queue(session_id: str) -> Optional[LiveRequestQueue]:
    """
    Retrieves the LiveRequestQueue for an existing session.
    """
    return ACTIVE_SESSIONS.get(session_id)


def remove_session(session_id: str) -> None:
    """
    Removes a session's LiveRequestQueue from the active sessions dictionary.
    """
    if session_id in ACTIVE_SESSIONS:
        # The close operation is now handled in cleanup_session
        del ACTIVE_SESSIONS[session_id]


async def cleanup_session(session_id: str) -> None:
    """
    Cleans up session resources by closing the LiveRequestQueue and removing it from active sessions.
    """
    try:
        live_request_queue = get_session_request_queue(session_id)
        if live_request_queue:
            live_request_queue.close()
            logger.info(f"LiveRequestQueue for session {session_id} closed.")

        remove_session(session_id)

        # Clean up session context
        if session_id in SESSION_CONTEXTS:
            del SESSION_CONTEXTS[session_id]
            logger.info(f"Session context for {session_id} removed")

        logger.info(f"Session {session_id} cleaned up and ended")
    except Exception as cleanup_error:
        logger.error(f"Error during session cleanup: {cleanup_error}")


async def handle_agent_responses(websocket: Any, live_events: Any, session_id: str, live_request_queue: LiveRequestQueue) -> None:
    """
    Handles responses from the agent, forwarding data to the client/frontend via websocket.
    Enhanced with improved interruption handling using Gemini SDK features.
    Includes voice intent detection for home decor consultations.
    """
    try:
        full_text = ""
        intent_detector = get_intent_detector()

        async for event in live_events:
            logger.info(event)

            # Check for voice input transcriptions to detect intent
            # ONLY process when transcription is finished to avoid duplicate detections
            if hasattr(event, 'input_transcription') and event.input_transcription:
                transcribed_text = event.input_transcription.text
                is_finished = getattr(event.input_transcription, 'finished', False)

                if transcribed_text and is_finished:
                    logger.info(f"[VOICE INTENT] User said (finished): '{transcribed_text}'")

                    # Get session context for all intent checks
                    from core.agents.retail.session_state import get_state_manager
                    session_context = SESSION_CONTEXTS.get(session_id, {})
                    customer_id = session_context.get("customer_id", "CY-DEFAULT")
                    state_manager = get_state_manager()
                    existing_session = state_manager.get_customer_session(customer_id)

                    # Check for photo analysis intent first
                    forced_call = intent_detector.should_force_tool_call(transcribed_text)

                    if forced_call and forced_call["tool_name"] == "analyze_photos":
                        # User said something like "analyze the photos" or "analyze my room"
                        logger.info("[VOICE INTENT] ===== PHOTO ANALYSIS INTENT DETECTED =====")

                        # Signal frontend to automatically submit uploaded photos
                        await websocket.send(
                            json.dumps({
                                "type": "trigger_photo_analysis",
                                "data": {
                                    "trigger": "voice_command",
                                    "transcription": transcribed_text
                                }
                            })
                        )
                        logger.info("[VOICE INTENT] Sent trigger_photo_analysis to frontend")
                        continue

                    # IMPORTANT: Check if there's already an active home decor consultation
                    # If yes (and moodboard not yet generated), allow natural conversation flow without forcing tool calls
                    # After moodboard is presented, allow forced tool calls for new requests
                    if existing_session and existing_session.get("current_stage") not in ["moodboard_presented", None]:
                        logger.info(f"[VOICE INTENT] Active home decor session exists (session_id: {existing_session['session_id']})")
                        logger.info(f"[VOICE INTENT] Stage: {existing_session.get('current_stage')}")
                        logger.info("[VOICE INTENT] Allowing natural conversation flow - NOT forcing tool call")
                        # Don't process voice intent detection, let the message flow naturally
                        continue

                    if forced_call:
                        tool_name = forced_call["tool_name"]
                        parameters = forced_call["parameters"]

                        logger.info(f"[VOICE INTENT] ===== HOME DECOR INTENT DETECTED IN VOICE =====")
                        logger.info(f"[VOICE INTENT] Forcing tool call: {tool_name}")
                        logger.info(f"[VOICE INTENT] Parameters: {parameters}")

                        # Get customer_id from session context
                        session_context = SESSION_CONTEXTS.get(session_id, {})
                        customer_id = session_context.get("customer_id", "CY-DEFAULT")
                        logger.info(f"[VOICE INTENT] Customer ID: {customer_id}")

                        # Build the forced call instruction
                        if tool_name == "create_style_moodboard":
                            # Direct moodboard creation with extracted parameters
                            style_prefs = parameters.get("style_preferences", [])
                            room_type = parameters.get("room_type", "")
                            color_prefs = parameters.get("color_preferences", None)

                            forced_message = f"""URGENT: The customer just asked about home decoration via voice.

Original voice request: "{transcribed_text}"

Detected room: {room_type}
Detected styles: {style_prefs}
Detected colors: {color_prefs if color_prefs else 'None'}

YOU MUST IMMEDIATELY call create_style_moodboard with these parameters:
- customer_id: "{customer_id}"
- style_preferences: {style_prefs}
- room_type: "{room_type}"
- color_preferences: {color_prefs if color_prefs else None}

DO NOT respond with text. DO NOT ask questions. JUST CALL THE TOOL NOW."""
                        else:
                            # Start consultation
                            forced_message = f"""URGENT: The customer just asked about home decoration via voice.

Original voice request: "{transcribed_text}"

YOU MUST IMMEDIATELY call start_home_decor_consultation with these parameters:
- customer_id: "{customer_id}"
- initial_request: "{transcribed_text}"

DO NOT respond with text. DO NOT ask questions. JUST CALL THE TOOL NOW."""

                        logger.info(f"[VOICE INTENT] Injecting forced tool call message")
                        live_request_queue.send_content(
                            Content(
                                role="user",
                                parts=[Part.from_text(text=forced_message)],
                            )
                        )
                        continue

            # --- PRIORITY 1: Check for interruption FIRST (before processing any other data) ---
            # This ensures immediate handling of user interruptions via VAD
            if event.interrupted:
                logger.info(
                    "Interruption detected via VAD - user started speaking"
                )
                await websocket.send(
                    json.dumps(
                        {
                            "type": "interrupted",
                            "data": {
                                "message": "Response interrupted by user input",
                                "timestamp": datetime.datetime.now(
                                    datetime.timezone.utc
                                ).isoformat(),
                            },
                        }
                    )
                )
                # Clear any buffered text
                full_text = ""
                continue

            # --- PRIORITY 2: Check for alternative interruption pattern (server_content.interrupted) ---
            if hasattr(event, "server_content") and event.server_content:
                if getattr(event.server_content, "interrupted", False):
                    logger.info(
                        "Interruption detected via server_content.interrupted pattern"
                    )
                    await websocket.send(
                        json.dumps(
                            {
                                "type": "interrupted",
                                "data": {
                                    "message": "Response interrupted",
                                    "timestamp": datetime.datetime.now(
                                        datetime.timezone.utc
                                    ).isoformat(),
                                },
                            }
                        )
                    )
                    full_text = ""
                    continue

            if event.content is None:
                logger.info(
                    f"None content - turn_complete:{event.turn_complete}"
                )
                continue

            # --- Tool Call and Result handling ---
            if event.content.parts[0].function_call:
                print("Function call detected")
                tool = event.content.parts[0].function_call
                await websocket.send(
                    json.dumps(
                        {
                            "type": "tool_call",
                            "data": {"name": tool.name, "args": tool.args},
                        }
                    )
                )
            elif event.content.parts[0].function_response:
                print("Function response detected")
                tool_result = event.content.parts[0].function_response
                await websocket.send(
                    json.dumps(
                        {"type": "tool_result", "data": tool_result.response}
                    )
                )

            # --- Text and Markdown handling ---
            if event.content.parts and event.content.parts[0].text:
                full_text = event.content.parts[0].text
                print(f"Full text: {full_text}")
                if not event.partial and full_text:
                    await websocket.send(
                        json.dumps({"type": "text", "data": full_text})
                    )
                    full_text = ""

            # --- Image handling ---
            inline_data = (
                event.content.parts and event.content.parts[0].inline_data
            )
            if inline_data and inline_data.mime_type.startswith("image"):
                image_base64 = base64.b64encode(inline_data.data).decode(
                    "utf-8"
                )
                await websocket.send(
                    json.dumps(
                        {
                            "type": "image",
                            "data": f"data:{inline_data.mime_type};base64,{image_base64}",
                        }
                    )
                )
                continue

            # --- Audio handling ---
            if inline_data and inline_data.mime_type.startswith("audio/pcm"):
                audio_base64 = base64.b64encode(inline_data.data).decode(
                    "utf-8"
                )
                await websocket.send(
                    json.dumps({"type": "audio", "data": audio_base64})
                )
                continue
            await asyncio.sleep(0)
    except Exception as e:
        logger.error(f"Error handling agent response: {e}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")


async def handle_client_messages(
    websocket: Any, live_request_queue: LiveRequestQueue, session_id: str
) -> None:
    """
    Handles incoming messages from the client, processing and forwarding them to the agent.
    Now intercepts images and calls analysis tools directly when home decor consultation is active.
    """
    try:
        async for message in websocket:
            try:
                data = json.loads(message)

                msg_type = data.get("type")
                logger.info(f"[WEBSOCKET] Received message type: {msg_type}, data length: {len(str(data.get('data', '')))}")

                if msg_type == "audio":
                    logger.debug("Client -> Agent: Handling audio data...")
                    decoded_data = base64.b64decode(data.get("data"))
                    live_request_queue.send_realtime(
                        Blob(data=decoded_data, mime_type="audio/pcm")
                    )
                    logger.debug("Audio sent to Agent")
                elif msg_type == "image":
                    logger.info("[IMAGE INTERCEPTOR] ===== IMAGE RECEIVED =====")
                    # Handle both data URI format and raw base64
                    image_data_raw = data.get("data")
                    if "," in image_data_raw:
                        # Data URI format:
                        # "data:image/jpeg;base64,<base64data>"
                        image_data_str = image_data_raw.split(",")[1]
                    else:
                        # Raw base64 format
                        image_data_str = image_data_raw

                    # Check if there's an active home decor consultation
                    from core.agents.retail.session_state import get_state_manager
                    session_context = SESSION_CONTEXTS.get(session_id, {})
                    customer_id = session_context.get("customer_id", "CY-DEFAULT")
                    state_manager = get_state_manager()
                    existing_session = state_manager.get_customer_session(customer_id)

                    # Allow photo analysis during active consultations AND after moodboard is presented
                    # (for follow-up questions and refinements)
                    if existing_session:
                        logger.info(f"[IMAGE INTERCEPTOR] Active home decor session found (session_id: {existing_session['session_id']})")

                        # Check the current stage to determine which analysis tool to call
                        current_stage = existing_session.get("stage", "")
                        collected_data = existing_session.get("collected_data", {})
                        room_type = collected_data.get("room_type")
                        age_context = collected_data.get("age_context")
                        decor_session_id = existing_session["session_id"]

                        # If we're in Phase 3 (after constraints, awaiting photos for redesign), call analyze_room_with_history
                        # This cross-references with order history
                        if current_stage == "stage_1d_photo_request" and collected_data.get("room_purpose") == "redesign":
                            logger.info("[IMAGE INTERCEPTOR] Phase 3: Calling analyze_room_with_history for order history cross-reference")
                            from core.agents.retail.tools import analyze_room_with_history

                            try:
                                tool_result = await asyncio.to_thread(
                                    analyze_room_with_history,
                                    customer_id=customer_id,
                                    session_id=decor_session_id,
                                    age_context=age_context,
                                    room_type=room_type,
                                    image_data=image_data_str
                                )
                                logger.info(f"[IMAGE INTERCEPTOR] Tool result status: {tool_result.get('status')}")
                            except Exception as tool_error:
                                logger.error(f"[IMAGE INTERCEPTOR] Error calling analyze_room_with_history: {tool_error}")
                                logger.error(f"Full traceback:\n{traceback.format_exc()}")
                                # Fall through to normal processing if tool call fails
                                decoded_data = base64.b64decode(image_data_str)
                                live_request_queue.send_realtime(
                                    Blob(data=decoded_data, mime_type="image/jpeg")
                                )
                                logger.debug("Image sent to Agent via multimodal context after tool error")
                                continue
                        else:
                            # For other scenarios (simple decor requests without order history), call analyze_room_for_decor
                            logger.info("[IMAGE INTERCEPTOR] Calling analyze_room_for_decor directly")
                            from core.agents.retail.tools import analyze_room_for_decor

                            try:
                                tool_result = await asyncio.to_thread(
                                    analyze_room_for_decor,
                                    customer_id=customer_id,
                                    room_type_hint=room_type,
                                    image_data=image_data_str
                                )
                                logger.info(f"[IMAGE INTERCEPTOR] Tool result status: {tool_result.get('status')}")
                            except Exception as tool_error:
                                logger.error(f"[IMAGE INTERCEPTOR] Error calling analyze_room_for_decor: {tool_error}")
                                logger.error(f"Full traceback:\n{traceback.format_exc()}")
                                # Fall through to normal processing if tool call fails
                                decoded_data = base64.b64decode(image_data_str)
                                live_request_queue.send_realtime(
                                    Blob(data=decoded_data, mime_type="image/jpeg")
                                )
                                logger.debug("Image sent to Agent via multimodal context after tool error")
                                continue

                        # Mark room photos as analyzed in session state so the consultation can advance
                        if tool_result.get('status') == 'success':
                            try:
                                state_manager.update_session(
                                    session_id=decor_session_id,
                                    room_photos_analyzed=True,
                                    photo_analysis=tool_result.get('analysis', {})
                                )
                                logger.info(f"[IMAGE INTERCEPTOR] Updated session {decor_session_id} with room_photos_analyzed=True")
                            except Exception as update_error:
                                logger.error(f"[IMAGE INTERCEPTOR] Failed to update session state: {update_error}")

                        # Send the tool result to the agent as if it came from a function response
                        # This way the agent can present the recommendations naturally
                        tool_response_message = f"""The room analysis tool has been called automatically and returned results:

Status: {tool_result.get('status')}
Analysis: {tool_result.get('analysis', {})}

IMPORTANT: After presenting these room analysis results to the customer:
1. Present the analysis in a friendly, conversational way
2. Explain what you see in their space
3. Then IMMEDIATELY call continue_home_decor_consultation to proceed to the next phase (style discovery)

DO NOT wait for the customer to respond after presenting the analysis. The consultation flow must continue automatically."""

                        live_request_queue.send_content(
                            Content(
                                role="user",
                                parts=[Part.from_text(text=tool_response_message)],
                            )
                        )

                        # Also send acknowledgment to client
                        await websocket.send(
                            json.dumps({
                                "type": "tool_call",
                                "data": {
                                    "name": "analyze_room_for_decor" if current_stage != "stage_1d_photo_request" else "analyze_room_with_history",
                                    "args": {
                                        "customer_id": customer_id,
                                        "room_type_hint": room_type
                                    }
                                }
                            })
                        )

                        await websocket.send(
                            json.dumps({
                                "type": "tool_result",
                                "data": tool_result
                            })
                        )

                        logger.info("[IMAGE INTERCEPTOR] Successfully processed image and sent results")
                        continue

                    # Normal processing: send image to agent via multimodal context
                    # This is only reached if no active consultation or tool call failed
                    decoded_data = base64.b64decode(image_data_str)
                    live_request_queue.send_realtime(
                        Blob(data=decoded_data, mime_type="image/jpeg")
                    )
                    logger.debug("Image sent to Agent via multimodal context")
                elif msg_type == "text":
                    logger.info("Client -> Agent: Sending text data...")
                    live_request_queue.send_content(
                        Content(
                            role="user",
                            parts=[Part.from_text(text=data.get("data"))],
                        )
                    )
                    logger.info("Text sent to Agent")
                elif msg_type == "end":
                    logger.info("Received end signal from client.")
                else:
                    debug_data = data.copy()
                    if (
                        "data" in debug_data
                        and debug_data.get("type") == "audio"
                    ):
                        debug_data["data"] = "<audio data>"
                    logger.warning(f"Unsupported message type from client: {data.get('type')}. Full data: {debug_data}")

            except json.JSONDecodeError:
                logger.error(
                    f"Failed to decode JSON from client message: {message}"
                )
            except Exception as e:
                logger.error(f"Error handling client message: {e}")
                logger.error(f"Full traceback:\n{traceback.format_exc()}")
    except Exception as e:
        if "connection closed" not in str(e).lower():
            logger.error(f"WebSocket connection error: {e}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
        raise


async def handle_messages(
    websocket: Any, live_events: Any, live_request_queue: LiveRequestQueue, session_id: str
) -> None:
    """Handles bidirectional message flow between client and Agent."""
    client_task = None
    agent_task = None

    try:
        async with asyncio.TaskGroup() as tg:
            client_task = tg.create_task(
                handle_client_messages(websocket, live_request_queue, session_id)
            )
            agent_task = tg.create_task(
                handle_agent_responses(websocket, live_events, session_id, live_request_queue)
            )
    except Exception as eg:
        handled = False
        # In TaskGroup, exceptions are in eg.exceptions
        for exc in getattr(eg, "exceptions", [eg]):
            if "Quota exceeded" in str(exc):
                logger.info("Quota exceeded error occurred")
                try:
                    await send_error_message(
                        websocket,
                        {
                            "message": "Quota exceeded.",
                            "action": "Please wait a moment and try again in a few minutes.",
                            "error_type": "quota_exceeded",
                        },
                    )
                    await websocket.send(
                        json.dumps(
                            {
                                "type": "text",
                                "data": "⚠️ Quota exceeded. Please wait a moment and try again in a few minutes.",
                            }
                        )
                    )
                    handled = True
                    break
                except Exception as send_err:
                    logger.error(
                        f"Failed to send quota error message: {send_err}"
                    )
            elif "connection closed" in str(exc).lower():
                logger.info("WebSocket connection closed")
                handled = True
                break
            elif "input audio" in str(exc).lower() or "1007" in str(exc):
                logger.warning(f"Gemini Live audio session error: {exc}")
                try:
                    await websocket.send(
                        json.dumps({
                            "type": "error",
                            "data": {
                                "message": "Audio session interrupted. Please reconnect.",
                                "error_type": "audio_session_error",
                                "action": "reconnect",
                            }
                        })
                    )
                except Exception:
                    pass
                handled = True
                break

        if not handled:
            logger.error(f"Error in message handling: {eg}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            raise
    finally:
        if client_task and not client_task.done():
            client_task.cancel()
        if agent_task and not agent_task.done():
            agent_task.cancel()


async def handle_client(websocket: Any) -> None:
    """
    Handles a new client connection by creating and managing an agent session.
    """
    session_id = str(id(websocket))
    logger.info(f"New client connected. Session ID: {session_id}")

    try:
        # Extract customer info from query parameters
        from urllib.parse import urlparse, parse_qs

        parsed_url = urlparse(websocket.request.path)
        query_params = parse_qs(parsed_url.query) if parsed_url.query else {}

        # Get customer info from query parameters (each value is a list, take
        # first element)
        customer_id = query_params.get("customer_id", [None])[0]
        first_name = query_params.get("first_name", [None])[0]
        last_name = query_params.get("last_name", [None])[0]
        email = query_params.get("email", [None])[0]

        if customer_id:
            logger.info(
                f"Customer info received: {first_name} {last_name} ({customer_id}) - {email}"
            )

        # Get agent config with customer personalization
        agent_config = get_agent_config(
            customer_id=customer_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )
        initial_session_state = agent_config.get("context", {})

        # Add dynamic context like current time
        # Assuming server is in CEST for this calculation
        current_time_munich = datetime.datetime.now(
            datetime.timezone.utc
        ) + datetime.timedelta(
            hours=2
        )  # CEST is UTC+2
        initial_session_state["current_datetime"] = (
            current_time_munich.strftime("%Y-%m-%d %H:%M:%S %Z")
        )

        live_events = await create_session(
            session_id,
            context=initial_session_state,
            agent_config=agent_config,
        )
        live_request_queue = get_session_request_queue(session_id)

        if not live_request_queue:
            raise ValueError(
                "Failed to create a live request queue for the session."
            )

        # Store session context for voice intent detection
        SESSION_CONTEXTS[session_id] = {
            "customer_id": customer_id or "CY-DEFAULT",
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
        }

        await websocket.send(json.dumps({"ready": True}))
        logger.info(f"New session started: {session_id}")

        # Note: Personalized greeting is handled by the agent's persona system
        # The agent will generate an appropriate greeting with audio automatically
        # No need to send a separate text greeting here

        await handle_messages(websocket, live_events, live_request_queue, session_id)

    except asyncio.TimeoutError:
        logger.info(f"Session {session_id} timed out due to inactivity.")
        await send_error_message(
            websocket,
            {
                "message": "Session timed out due to inactivity.",
                "action": "You can start a new conversation.",
                "error_type": "timeout",
            },
        )
    except Exception as e:
        logger.error(f"Error in handle_client for session {session_id}: {e}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        if "connection closed" in str(e).lower() or "code = 100" in str(e):
            logger.info(
                f"WebSocket connection closed for session {session_id}"
            )
        else:
            await send_error_message(
                websocket,
                {
                    "message": "An unexpected error occurred.",
                    "action": "Please try again.",
                    "error_type": "general",
                },
            )
    finally:
        logger.info(f"Cleaning up session: {session_id}")
        await cleanup_session(session_id)
