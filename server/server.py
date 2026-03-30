"""
Vertex AI Gemini Multimodal Live Proxy Server with Tool Support
Uses Python SDK for communication with Gemini API
"""

import asyncio
import os
from core.websocket_handler import handle_client
from core.logger import logger


async def main() -> None:
    """Starts the WebSocket server."""
    port = int(os.environ.get("PORT", "8081"))

    import websockets

    print(f"Running websocket server on 0.0.0.0:{port}...")
    async with websockets.serve(
        handle_client,
        "0.0.0.0",
        port,
        ping_interval=30,
        ping_timeout=10,
    ):
        print(f"Running websocket server on 0.0.0.0:{port}...")
        logger.info(f"Running websocket server on 0.0.0.0:{port}...")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
