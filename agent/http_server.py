"""
HTTP API server for session management.

Runs alongside the LiveKit agent on a separate port (8082).
Provides endpoints for the frontend to manage ACP sessions.

Endpoints:
  GET   /health                        — Health check
  GET   /plan/{room_id}                — Get session data (transcript, preferences, summary)
  POST  /email/{room_id}               — Register an email address  {email: "..."}
  POST  /send-plan/{room_id}           — Email the plan to all registered addresses
  POST  /close/{room_id}               — Close session, delete data + audio
"""

import asyncio
import json
import logging
import os
from typing import Optional

from aiohttp import web

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


from email_sender import is_configured as email_configured, send_plan_email
from session_store import SessionStore

logger = logging.getLogger("acp-agent.http")

# Global reference set by the agent at startup
_store: Optional[SessionStore] = None


def init(store: SessionStore):
    """Initialise the HTTP server with a reference to the session store."""
    global _store
    _store = store


async def _get_store() -> SessionStore:
    assert _store is not None, "HTTP server not initialised with session store"
    return _store


# --- Helper: generate plan summary via LLM ---

async def _generate_summary(room_id: str) -> str:
    """Generate a plain-text summary of ACP preferences from the transcript."""
    store = await _get_store()
    transcript = await store.get_transcript(room_id)

    if not transcript:
        return "The conversation was too short to generate a summary."

    # Build a concise summary from the transcript content
    # Extract key topics discussed
    topics_discussed = set()
    for entry in transcript:
        text = entry.get("text", "").lower()
        if "substitute decision-maker" in text or "power of attorney" in text:
            topics_discussed.add("Substitute Decision-Maker")
        if "life support" in text or "ventilator" in text or "cpr" in text:
            topics_discussed.add("Life-Sustaining Treatment Preferences")
        if "quality of life" in text:
            topics_discussed.add("Quality of Life Values")
        if "dementia" in text or "coma" in text:
            topics_discussed.add("Specific Scenarios (Dementia/Coma)")
        if "palliative" in text or "comfort" in text or "pain" in text:
            topics_discussed.add("Palliative and Comfort Care")
        if "values" in text or "belief" in text or "faith" in text or "religion" in text:
            topics_discussed.add("Personal Values and Beliefs")
        if "terminal" in text or "end of life" in text:
            topics_discussed.add("End-of-Life Care Preferences")

    summary_parts = [
        "You had a conversation about your future healthcare wishes. "
        "Here is a summary of what was discussed:\n"
    ]

    if topics_discussed:
        summary_parts.append(
            "Topics covered:\n" +
            "\n".join(f"  - {t}" for t in sorted(topics_discussed))
        )
    else:
        summary_parts.append(
            "The conversation was exploratory in nature. "
            "Topics included general values and preferences for future healthcare."
        )

    summary_parts.append(
        f"\n\nThe conversation had {len(transcript)} exchanges. "
        "Your full transcript and any extracted preferences are included below."
    )

    return "\n".join(summary_parts)


# --- Route handlers ---

async def handle_health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


async def handle_get_plan(request: web.Request) -> web.Response:
    room_id = request.match_info["room_id"]
    store = await _get_store()
    status = await store.get_status(room_id)

    if not status:
        return web.json_response(
            {"error": "Session not found"}, status=404
        )

    transcript = await store.get_transcript(room_id)
    preferences = await store.get_preferences(room_id)
    summary = await store.get_plan_summary(room_id)

    if not summary:
        summary = await _generate_summary(room_id)
        await store.set_plan_summary(room_id, summary)

    return web.json_response({
        "room_id": room_id,
        "status": status,
        "summary": summary,
        "preferences": preferences,
        "transcript": transcript[-50:],  # last 50 entries
        "email_count": len(await store.get_emails(room_id)),
    })


async def handle_add_email(request: web.Request) -> web.Response:
    room_id = request.match_info["room_id"]
    store = await _get_store()

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    email = body.get("email", "").strip().lower()
    if not email or "@" not in email:
        return web.json_response(
            {"error": "Valid email address required"}, status=400
        )

    await store.add_email(room_id, email)
    email_count = len(await store.get_emails(room_id))
    logger.info("Email added for session %s: %s", room_id, email)

    return web.json_response({
        "status": "ok",
        "email": email,
        "email_count": email_count,
        "message": "Email address registered. Click 'Send Plan' when you're ready.",
    })


async def handle_send_plan(request: web.Request) -> web.Response:
    room_id = request.match_info["room_id"]
    store = await _get_store()

    if not email_configured():
        return web.json_response({
            "error": (
                "Email service not configured. "
                "Set ACS_CONNECTION_STRING and ACS_SENDER_DOMAIN in .env"
            ),
        }, status=500)

    emails = await store.get_emails(room_id)
    if not emails:
        return web.json_response({
            "error": "No email addresses registered. Add an email first.",
        }, status=400)

    # Get session data
    transcript = await store.get_transcript(room_id)
    preferences = await store.get_preferences(room_id)
    summary = await store.get_plan_summary(room_id)
    audio_path = await store.get_audio_path(room_id)

    if not summary:
        summary = await _generate_summary(room_id)
        await store.set_plan_summary(room_id, summary)

    # Send to all registered emails
    results = []
    for email in emails:
        success = send_plan_email(
            to_email=email,
            plan_summary=summary,
            transcript=transcript,
            preferences=preferences,
            audio_path=audio_path,
        )
        results.append({"email": email, "success": success})

    success_count = sum(1 for r in results if r["success"])
    logger.info(
        "Plan sent for session %s: %d/%d emails delivered",
        room_id, success_count, len(results),
    )

    return web.json_response({
        "status": "partial" if success_count < len(results) else "sent",
        "results": results,
        "message": (
            f"Plan sent to {success_count} of {len(results)} email(s)."
        ),
    })


async def handle_close(request: web.Request) -> web.Response:
    room_id = request.match_info["room_id"]
    store = await _get_store()

    status = await store.get_status(room_id)
    if not status:
        return web.json_response({"error": "Session not found"}, status=404)

    if status == "closed":
        return web.json_response({"error": "Session already closed"}, status=400)

    # Get audio path for cleanup
    audio_path = await store.get_audio_path(room_id)

    # Close session and delete Redis data
    data = await store.close_session(room_id)

    # Delete audio file
    if audio_path:
        from audio_recorder import ConversationRecorder
        ConversationRecorder.cleanup(audio_path)

    transcript_count = len(data.get("transcript", []))
    logger.info(
        "Session closed: %s (%d transcript entries, audio deleted: %s)",
        room_id, transcript_count, "yes" if audio_path else "no",
    )

    return web.json_response({
        "status": "closed",
        "room_id": room_id,
        "message": "Session closed. Your data has been deleted.",
    })


# --- App factory ---

def create_app() -> web.Application:
    """Create the aiohttp application."""
    app = web.Application(middlewares=[cors_middleware])
    app.router.add_get("/health", handle_health)
    app.router.add_get("/plan/{room_id}", handle_get_plan)
    app.router.add_post("/email/{room_id}", handle_add_email)
    app.router.add_post("/send-plan/{room_id}", handle_send_plan)
    app.router.add_post("/close/{room_id}", handle_close)
    return app


async def run_server(host: str = "0.0.0.0", port: int = 8082):
    """Start the HTTP server."""
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logger.info("HTTP API server running on http://%s:%d", host, port)
    # Keep running
    await asyncio.Event().wait()