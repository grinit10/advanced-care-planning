"""
ACP Voice Agent — Entry Point

Connects to LiveKit, runs the voice pipeline, manages sessions,
records audio, and serves the HTTP API for frontend interactions.
"""

import asyncio
import logging
import os
import threading
from pathlib import Path

from acp_agent import (
    create_extractor_llm,
    create_initial_context,
    create_stt,
    create_tts,
    create_vad,
    create_voice_llm,
)
from audio_recorder import ConversationRecorder
from dotenv import load_dotenv
from http_server import init as init_http_server
from http_server import run_server as run_http_server
from livekit.agents import (
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
    tokenize,
)
from livekit.agents.tts import StreamAdapter
from livekit.agents.voice import Agent, AgentSession
from preference_extractor import EMPTY_PREFERENCES, extract_preferences
from session_store import SessionStore, TranscriptEntry

# Load .env from the project root
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

logger = logging.getLogger("acp-agent")

# Global session store — shared across agent and HTTP server
session_store = SessionStore()

# Track active recorders keyed by room_id for cleanup
_active_recorders: dict[str, ConversationRecorder] = {}


class ACPAgent(Agent):
    """Custom Agent subclass for Advanced Care Planning conversations.

    Uses lifecycle hooks (on_enter, on_user_turn_completed, on_exit)
    to manage transcripts, recordings, and session cleanup.
    """

    # Debounce window for preference extraction — avoids an LLM call after
    # every single utterance when the user is speaking rapidly.
    _PREF_DEBOUNCE_SECONDS = 3.0

    def __init__(self, chat_ctx, room_id: str, llm_instance: llm.LLM):
        super().__init__(
            instructions="",  # instructions not used — chat_ctx carries the system prompt
            chat_ctx=chat_ctx,
        )
        self.room_id = room_id
        self.last_msg_count = 0
        self._llm = llm_instance
        self._pref_lock = asyncio.Lock()
        self._debounce_task: asyncio.Task | None = None

    async def on_enter(self):
        """Called when the agent session starts — greet the user."""
        await self.session.say(
            "Hi, I'm your Advanced Care Planning assistant. "
            "I'm here to help you think through and document your healthcare wishes "
            "for the future. There are no right or wrong answers — this is about "
            "what matters most to you. Shall we begin?"
        )
        # Log the first agent message
        greeting_entry = TranscriptEntry(role="agent", text=(
            "Hi, I'm your Advanced Care Planning assistant. "
            "I'm here to help you think through and document your healthcare wishes "
            "for the future. There are no right or wrong answers — this is about "
            "what matters most to you. Shall we begin?"
        ))
        await session_store.add_transcript_entry(self.room_id, greeting_entry)
        self.last_msg_count = len(self.chat_ctx.messages())

    async def on_user_turn_completed(
        self,
        turn_ctx: llm.ChatContext,
        new_message: llm.ChatMessage,
    ):
        """Called after each user turn completes — store transcript entries."""
        msgs = self.chat_ctx.messages()
        for i in range(self.last_msg_count, len(msgs)):
            # Extract text from content list (list[ChatContent] where text is str)
            content = msgs[i].content
            text = " ".join(
                c for c in (content or [])
                if isinstance(c, str)
            ) or ""
            entry = TranscriptEntry(
                role="user" if msgs[i].role == "user" else "agent",
                text=text,
            )
            await session_store.add_transcript_entry(self.room_id, entry)
        self.last_msg_count = len(msgs)

        # Debounced preference extraction — cancels any pending extraction
        # and restarts the timer. This prevents an LLM call after every single
        # utterance when the user is speaking rapidly. Extraction fires only
        # after {_PREF_DEBOUNCE_SECONDS}s of inactivity.
        if self._debounce_task is not None:
            self._debounce_task.cancel()
        self._debounce_task = asyncio.create_task(self._debounced_extract())

    async def _debounced_extract(self):
        """Wait for the debounce window, then extract preferences.

        If cancelled by a new user turn arriving within the window,
        the extraction is silently skipped.
        """
        try:
            await asyncio.sleep(self._PREF_DEBOUNCE_SECONDS)
            await self._extract_preferences()
        except asyncio.CancelledError:
            pass  # New turn arrived — extraction will re-schedule

    async def _extract_preferences(self):
        """Extract structured preferences from the latest exchange asynchronously."""
        async with self._pref_lock:
            try:
                # Get the latest user+agent exchange
                msgs = self.chat_ctx.messages()
                if len(msgs) < 2:
                    return

                # Build exchange text from the last pair of messages
                exchange_parts = []
                for msg in msgs[-4:]:  # last 2 turns (user + agent = 4 messages)
                    role = "User" if msg.role == "user" else "Assistant"
                    text = " ".join(
                        c for c in (msg.content or [])
                        if isinstance(c, str)
                    ) or ""
                    if text.strip():
                        exchange_parts.append(f"{role}: {text.strip()}")

                exchange = "\n".join(exchange_parts)
                if not exchange.strip():
                    return

                # Get existing preferences from Redis
                existing = await session_store.get_preferences_json(self.room_id)

                # Extract new preferences
                updated = await extract_preferences(
                    self._llm,
                    exchange,
                    existing_prefs=existing or EMPTY_PREFERENCES,
                )

                # Save back to Redis
                if updated:
                    await session_store.save_preferences_json(self.room_id, updated)
                    logger.info(
                        "Extracted preferences for session %s",
                        self.room_id,
                    )
            except Exception as e:
                logger.error("Preference extraction error: %s", e)

    async def on_exit(self):
        """Called when the agent session ends — clean up recording."""
        # Cancel any pending debounced extraction
        if self._debounce_task is not None:
            self._debounce_task.cancel()
            self._debounce_task = None
        await _cleanup_session(self.room_id)


def prewarm(proc: JobProcess):
    """Preload VAD model before the first job arrives."""
    proc.userdata["vad"] = create_vad()


async def entrypoint(job: JobContext):
    """Called when a new room is created and the agent is dispatched."""
    room_id = job.room.name
    logger.info("Connecting to room: %s", room_id)
    await job.connect()

    # Connect to Redis — this runs in the child process, so we need
    # a separate connection from the one in the parent's HTTP server thread
    if session_store._redis is None:
        await session_store.connect()

    # Wait for the first participant to join
    participant = await job.wait_for_participant()
    logger.info("Participant joined: %s (room: %s)", participant.identity, room_id)

    # Create the session in Redis
    await session_store.create_session(room_id, participant.identity)

    # Start audio recording
    recorder = ConversationRecorder(
        job.room,
        participant.identity,
        records_dir=os.environ.get("RECORDINGS_DIR", "recordings"),
    )
    await recorder.start()
    _active_recorders[room_id] = recorder

    # Create the LLM instances (separate for voice conversation and preference extraction)
    voice_llm_instance = create_voice_llm()
    extractor_llm_instance = create_extractor_llm()

    # Create the agent instance (captures conversation logic)
    agent = ACPAgent(
        chat_ctx=create_initial_context(),
        room_id=room_id,
        llm_instance=extractor_llm_instance,
    )

    # Create the agent session (runtime that manages VAD → STT → LLM → TTS)
    # Wrap TTS with a sentence tokenizer so it starts speaking sooner —
    # instead of waiting for the full LLM response, it streams audio
    # sentence-by-sentence for more natural pacing.
    tts = StreamAdapter(
        tts=create_tts(),
        sentence_tokenizer=tokenize.basic.SentenceTokenizer(),
    )

    session = AgentSession(
        vad=job.proc.userdata["vad"],
        stt=create_stt(),
        llm=voice_llm_instance,
        tts=tts,
        turn_handling={
            # Enable interruptions — user can cut in at any time
            "interruption": {
                "enabled": True,
                "mode": "vad",
                "min_duration": 0.3,
                "min_words": 2,
            },
            # Fixed endpointing — waits for a short silence to confirm
            # the user has finished speaking. Reduced delays from the
            # original 0.6/3.0 for faster turn-taking.
            "endpointing": {
                "mode": "fixed",
                "min_delay": 0.3,
                "max_delay": 1.0,
            },
            # Preemptive generation + TTS — starts LLM inference before
            # the user finishes speaking, AND streams TTS audio from
            # partial LLM output so the user hears the first sound
            # ~800ms sooner.
            "preemptive_generation": {
                "enabled": True,
                "preemptive_tts": True,
                "max_speech_duration": 10.0,
            },
        },
    )

    # Start the session — this calls agent.on_enter() automatically
    await session.start(agent=agent, room=job.room)


async def _cleanup_session(room_id: str):
    """Stop recording, save audio path, and register cleanup."""
    recorder = _active_recorders.pop(room_id, None)
    if recorder:
        await recorder.stop()
        audio_path = recorder.save(room_id)
        if audio_path:
            await session_store.set_audio_path(room_id, audio_path)
        logger.info("Recording saved for session: %s", room_id)
    # Session data stays in Redis until user closes it via the API


async def _start_background_services():
    """Connect to Redis and start the HTTP API server."""
    await session_store.connect()
    init_http_server(session_store)
    logger.info("Background services initialised")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    # ── Architecture Note ──────────────────────────────────────────────────
    # The LiveKit Agent SDK's cli.run_app() is a blocking call that manages
    # its own internal asyncio event loop. It cannot be await'd or wrapped
    # in asyncio.gather() — it takes over the main thread.
    #
    # The HTTP API server (for session management, email, etc.) runs in a
    # separate daemon thread with its own event loop. This is the standard
    # pattern for sidecar HTTP servers alongside LiveKit agents.
    #
    # Both share the same Redis-backed SessionStore (via a separate Redis
    # connection in the child process — see session_store.connect()).
    # ────────────────────────────────────────────────────────────────────────

    def _start_http_server():
        """Run the HTTP API server in a background thread.

        Uses asyncio.run() for clean event loop lifecycle management
        (creates, runs, and closes the loop automatically).
        """
        async def startup():
            await _start_background_services()
            await run_http_server()

        asyncio.run(startup())

    http_thread = threading.Thread(
        target=_start_http_server,
        name="acp-http-server",
        daemon=True,
    )
    http_thread.start()
    logger.info("HTTP API server started on http://0.0.0.0:8082 (thread: %s)", http_thread.name)

    # Start the LiveKit agent (blocking — takes over the main thread)
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        )
    )
