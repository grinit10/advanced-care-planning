import os
import logging

from aiohttp import web
from livekit import api

# CORS headers — allow the frontend dev server to call this API
_CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


@web.middleware
async def cors_middleware(request: web.Request, handler):
    """Add CORS headers to every response, and handle OPTIONS preflight."""
    if request.method == "OPTIONS":
        return web.Response(headers=_CORS_HEADERS)
    resp = await handler(request)
    for key, val in _CORS_HEADERS.items():
        resp.headers[key] = val
    return resp

logger = logging.getLogger("token-server")

# Load credentials from environment
LIVEKIT_API_KEY = os.environ.get("LIVEKIT_API_KEY", "devkey")
LIVEKIT_API_SECRET = os.environ.get("LIVEKIT_API_SECRET", "devsecret")


async def handle_token(request: web.Request) -> web.Response:
    room_name = request.query.get("room", "acp-room")
    identity = request.query.get("identity", "user")

    if not room_name or not identity:
        return web.json_response(
            {"error": "Missing 'room' or 'identity' query parameter"},
            status=400,
        )

    token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET) \
        .with_identity(identity) \
        .with_grants(api.VideoGrants(
            room_join=True,
            room=room_name,
        )).to_jwt()

    logger.info(f"Token generated: room={room_name}, identity={identity}")
    return web.json_response({"token": token})


async def handle_health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


def create_app() -> web.Application:
    app = web.Application(middlewares=[cors_middleware])
    app.router.add_get("/token", handle_token)
    app.router.add_get("/health", handle_health)
    return app


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    port = int(os.environ.get("PORT", "8081"))
    web.run_app(create_app(), host="0.0.0.0", port=port)