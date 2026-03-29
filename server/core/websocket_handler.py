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
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.agents import LiveRequestQueue
from google.genai.types import (
    Part,
    Content,
    Blob,
)

from core.agent_factory import get_agent_config
from .logger import logger
from config.config import CONFIG

# Global session storage now holds the request queue for each session.
ACTIVE_SESSIONS: Dict[str, LiveRequestQueue] = {}

async def send_error_message(websocket: Any, error_data: dict) -> None:
    """
    Sends a formatted error message to the client via the websocket connection.
    """
    try:
        await websocket.send(json.dumps({
            "type": "error",
            "data": error_data
        }))
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")

async def start_agent_session(user_id: str, run_config: RunConfig, initial_session_state: Dict[str, Any]) -> tuple[Any, LiveRequestQueue]:
    """Starts an agent session with a new runner and request queue."""
    agent_config = get_agent_config()
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
    session_id: str,
    context: Dict[str, Any]
) -> Any:
    """
    Creates and stores a new session, leveraging the new ADK live session runner.
    """
    response_modalities_from_config = CONFIG["generation_config"]["response_modalities"]

    print(f"Voice: {CONFIG['generation_config']['speech_config']}")
    print(f"Modalities for session {session_id} (from CONFIG): {response_modalities_from_config}")

    run_config = RunConfig(
        response_modalities=response_modalities_from_config
    )

    live_events, live_request_queue = await start_agent_session(session_id, run_config, context)

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
        logger.info(f"Session {session_id} cleaned up and ended")
    except Exception as cleanup_error:
        logger.error(f"Error during session cleanup: {cleanup_error}")

async def handle_agent_responses(websocket: Any, live_events: Any) -> None:
    """
    Handles responses from the agent, forwarding data to the client/frontend via websocket.
    """
    try:
        full_text = ""
        async for event in live_events:
            logger.info(event)

            # --- Interruption ---
            if event.interrupted:
                print("Interrupted event detected")
                await websocket.send(json.dumps({
                    "type": "interrupted",
                    "data": {"message": "Response interrupted by user input"}
                }))
                continue

            if event.content is None:
                logger.info(f"None content - turn_complete:{event.turn_complete}")
                continue

            # --- Tool Call and Result handling ---
            if event.content.parts[0].function_call:
                print("Function call detected")
                tool = event.content.parts[0].function_call
                await websocket.send(json.dumps({
                    "type": "tool_call",
                    "data": {"name": tool.name, "args": tool.args}
                }))
            elif event.content.parts[0].function_response:
                print("Function response detected")
                tool_result = event.content.parts[0].function_response
                await websocket.send(json.dumps({
                    "type": "tool_result",
                    "data": tool_result.response
                }))

            # --- Text and Markdown handling ---
            if event.content.parts and event.content.parts[0].text:
                full_text = event.content.parts[0].text
                print(f"Full text: {full_text}")
                if not event.partial and full_text:
                    await websocket.send(json.dumps({
                        "type": "text",
                        "data": full_text
                    }))
                    full_text = ""

            # --- Image handling ---
            inline_data = event.content.parts and event.content.parts[0].inline_data
            if inline_data and inline_data.mime_type.startswith('image'):
                image_base64 = base64.b64encode(inline_data.data).decode('utf-8')
                await websocket.send(json.dumps({
                    "type": "image",
                    "data": f"data:{inline_data.mime_type};base64,{image_base64}"
                }))
                continue

            # --- Audio handling ---
            if inline_data and inline_data.mime_type.startswith('audio/pcm'):
                audio_base64 = base64.b64encode(inline_data.data).decode('utf-8')
                await websocket.send(json.dumps({
                    "type": "audio",
                    "data": audio_base64
                }))
                continue
            await asyncio.sleep(0)
    except Exception as e:
        logger.error(f"Error handling agent response: {e}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")

async def handle_client_messages(websocket: Any, live_request_queue: LiveRequestQueue) -> None:
    """
    Handles incoming messages from the client, processing and forwarding them to the agent.
    """
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                
                msg_type = data.get("type")

                if msg_type == "audio":
                    logger.debug("Client -> Agent: Handling audio data...")
                    decoded_data = base64.b64decode(data.get("data"))
                    live_request_queue.send_realtime(Blob(data=decoded_data, mime_type='audio/pcm'))
                    logger.debug("Audio sent to Agent")
                elif msg_type == "image":
                    print("---------data",data,"------")
                    logger.debug("Client -> Agent: Handling image data...")
                    # Assuming image data is base64 encoded after 'base64,'
                    image_data_str = data.get("data").split(",")[1]
                    decoded_data = base64.b64decode(image_data_str)
                    live_request_queue.send_realtime(Blob(data=decoded_data, mime_type='image/jpeg'))
                    logger.debug("Image sent to Agent")
                elif msg_type == "text":
                    logger.info("Client -> Agent: Sending text data...")
                    live_request_queue.send_content(Content(role='user', parts=[Part.from_text(text=data.get("data"))]))
                    logger.info("Text sent to Agent")
                elif msg_type == "end":
                    logger.info("Received end signal from client.")
                else:
                    debug_data = data.copy()
                    if "data" in debug_data and debug_data.get("type") == "audio":
                        debug_data["data"] = "<audio data>"
                    logger.warning(f"Unsupported message type from client: {data.get('type')}. Full data: {debug_data}")

            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON from client message: {message}")
            except Exception as e:
                logger.error(f"Error handling client message: {e}")
                logger.error(f"Full traceback:\n{traceback.format_exc()}")
    except Exception as e:
        if "connection closed" not in str(e).lower():
            logger.error(f"WebSocket connection error: {e}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
        raise

async def handle_messages(websocket: Any, live_events: Any, live_request_queue: LiveRequestQueue) -> None:
    """Handles bidirectional message flow between client and Agent."""
    client_task = None
    agent_task = None

    try:
        async with asyncio.TaskGroup() as tg:
            client_task = tg.create_task(handle_client_messages(websocket, live_request_queue))
            agent_task = tg.create_task(handle_agent_responses(websocket, live_events))
    except Exception as eg:
        handled = False
        # In TaskGroup, exceptions are in eg.exceptions
        for exc in getattr(eg, 'exceptions', [eg]):
            if "Quota exceeded" in str(exc):
                logger.info("Quota exceeded error occurred")
                try:
                    await send_error_message(websocket, {
                        "message": "Quota exceeded.",
                        "action": "Please wait a moment and try again in a few minutes.",
                        "error_type": "quota_exceeded"
                    })
                    await websocket.send(json.dumps({
                        "type": "text",
                        "data": "⚠️ Quota exceeded. Please wait a moment and try again in a few minutes."
                    }))
                    handled = True
                    break
                except Exception as send_err:
                    logger.error(f"Failed to send quota error message: {send_err}")
            elif "connection closed" in str(exc).lower():
                logger.info("WebSocket connection closed")
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
        agent_config = get_agent_config()
        initial_session_state = agent_config.get("context", {})

        # Add dynamic context like current time
        # Assuming server is in CEST for this calculation
        current_time_munich = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2) # CEST is UTC+2
        initial_session_state["current_datetime"] = current_time_munich.strftime("%Y-%m-%d %H:%M:%S %Z")

        live_events = await create_session(session_id, context=initial_session_state)
        live_request_queue = get_session_request_queue(session_id)

        if not live_request_queue:
            raise ValueError("Failed to create a live request queue for the session.")

        await websocket.send(json.dumps({"ready": True}))
        logger.info(f"New session started: {session_id}")

        await handle_messages(websocket, live_events, live_request_queue)

    except asyncio.TimeoutError:
        logger.info(f"Session {session_id} timed out due to inactivity.")
        await send_error_message(websocket, {
            "message": "Session timed out due to inactivity.",
            "action": "You can start a new conversation.",
            "error_type": "timeout"
        })
    except Exception as e:
        logger.error(f"Error in handle_client for session {session_id}: {e}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        if "connection closed" in str(e).lower() or "code = 100" in str(e):
             logger.info(f"WebSocket connection closed for session {session_id}")
        else:
            await send_error_message(websocket, {
                "message": "An unexpected error occurred.",
                "action": "Please try again.",
                "error_type": "general"
            })
    finally:
        logger.info(f"Cleaning up session: {session_id}")
        await cleanup_session(session_id)