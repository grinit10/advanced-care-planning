import json
import logging
import os
import uuid
from contextvars import ContextVar

from aiohttp import web
from livekit import api

# Thread-local / async task correlation ID tracker
CORRELATION_ID_VAR = ContextVar("correlation_id", default="")

class StructuredJSONFormatter(logging.Formatter):
    """Log formatter that outputs log lines as parseable JSON objects.

    Automatically injects the current correlation ID if present in the async context.
    """
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": CORRELATION_ID_VAR.get() or "none",
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

def setup_logging():
    """Initialise global logging formatter based on the LOG_FORMAT env var."""
    log_format = os.environ.get("LOG_FORMAT", "text").strip().lower()
    text_format = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"

    root_logger = logging.getLogger()

    if root_logger.handlers:
        for handler in root_logger.handlers:
            if log_format == "json":
                handler.setFormatter(StructuredJSONFormatter())
            else:
                handler.setFormatter(logging.Formatter(text_format))
    else:
        handler = logging.StreamHandler()
        if log_format == "json":
            handler.setFormatter(StructuredJSONFormatter())
        else:
            handler.setFormatter(logging.Formatter(text_format))
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)


@web.middleware
async def correlation_id_middleware(request: web.Request, handler):
    """Extract or generate a unique correlation ID for request tracing."""
    corr_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    CORRELATION_ID_VAR.set(corr_id)

    response = await handler(request)
    response.headers["X-Correlation-ID"] = corr_id
    return response

# Parse CORS allowed origins from environment (comma-separated list, e.g. "http://localhost:5173,https://acp.yourdomain.com")
# Defaults to "*" if not defined.
_ALLOWED_CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("ALLOWED_CORS_ORIGINS", "*").split(",")
    if origin.strip()
]


@web.middleware
async def cors_middleware(request: web.Request, handler):
    """Add CORS headers to every response, and handle OPTIONS preflight."""
    origin = request.headers.get("Origin")

    allowed_origin = None
    if origin:
        if "*" in _ALLOWED_CORS_ORIGINS or origin in _ALLOWED_CORS_ORIGINS:
            allowed_origin = origin
    else:
        if "*" in _ALLOWED_CORS_ORIGINS:
            allowed_origin = "*"

    # If Origin header is present but not whitelisted, return 403 for OPTIONS, or omit CORS headers
    if origin and not allowed_origin:
        if request.method == "OPTIONS":
            return web.Response(status=403, text="CORS Origin Not Allowed")
        return await handler(request)

    headers = {
        "Access-Control-Allow-Origin": allowed_origin or "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }

    if request.method == "OPTIONS":
        return web.Response(headers=headers)

    resp = await handler(request)
    for key, val in headers.items():
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

    token = (
        api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(identity)
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,
            )
        )
        .to_jwt()
    )

    logger.info(f"Token generated: room={room_name}, identity={identity}")
    return web.json_response({"token": token})


async def handle_health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


def create_app() -> web.Application:
    app = web.Application(middlewares=[correlation_id_middleware, cors_middleware])
    app.router.add_get("/token", handle_token)
    app.router.add_get("/health", handle_health)
    return app


if __name__ == "__main__":
    # Initialize unified logging configuration
    setup_logging()
    port = int(os.environ.get("PORT", "8081"))
    web.run_app(create_app(), host="0.0.0.0", port=port)  # noqa: S104
