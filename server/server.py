"""
Vertex AI Gemini Multimodal Live Proxy Server with Tool Support.

Runs a WebSocket server for real-time audio/video communication
with a lightweight HTTP health check endpoint for Cloud Run probes.
"""

import asyncio
import os
import json
from aiohttp import web
from core.websocket_handler import handle_client
from core.logger import logger


async def health_handler(request):
    """Health check endpoint for Cloud Run / K8s liveness probes."""
    return web.Response(
        text=json.dumps({"status": "healthy", "service": "shopping-backend"}),
        content_type="application/json",
    )


async def main() -> None:
    """Starts the WebSocket server with HTTP health endpoint."""
    port = int(os.environ.get("PORT", "8081"))
    health_port = int(os.environ.get("HEALTH_PORT", str(port)))

    import websockets

    # Start HTTP health check server (same port via aiohttp)
    app = web.Application()
    app.router.add_get("/health", health_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    health_site = web.TCPSite(runner, "0.0.0.0", health_port + 1)
    await health_site.start()
    logger.info(f"Health endpoint running on 0.0.0.0:{health_port + 1}/health")

    # Start WebSocket server
    logger.info(f"Starting WebSocket server on 0.0.0.0:{port}...")
    async with websockets.serve(
        handle_client,
        "0.0.0.0",
        port,
        ping_interval=30,
        ping_timeout=60,
        max_size=10 * 1024 * 1024,
    ):
        logger.info(f"WebSocket server running on 0.0.0.0:{port}")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
