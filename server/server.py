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
    from core.observability import get_health, get_metrics

    health_status = get_health().get_status()
    metrics_data = get_metrics().get_metrics()

    return web.Response(
        text=json.dumps(
            {
                "status": health_status["status"],
                "service": "shopping-backend",
                "components": health_status.get("components", {}),
                "uptime_seconds": metrics_data.get("uptime_seconds", 0),
                "total_connections": metrics_data.get("counters", {}).get(
                    "total_connections", 0
                ),
                "error_rate_pct": metrics_data.get("error_rate_pct", 0),
            }
        ),
        content_type="application/json",
    )


async def metrics_handler(request):
    """Metrics endpoint for monitoring dashboards."""
    from core.observability import get_metrics

    return web.Response(
        text=json.dumps(get_metrics().get_metrics()),
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
    app.router.add_get("/metrics", metrics_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    health_http_port = health_port + 2  # 8083 to avoid conflict with CRM on 8082
    health_site = web.TCPSite(runner, "0.0.0.0", health_http_port)
    await health_site.start()
    logger.info(f"Health endpoint running on 0.0.0.0:{health_http_port}/health")

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
