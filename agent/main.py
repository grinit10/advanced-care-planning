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

from dotenv import load_dotenv
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents import tokenize
from livekit.agents.tts import StreamAdapter
from livekit.agents.voice import Agent, AgentSession

from acp_agent import (
    create_initial_context,
    create_llm,
    create_stt,
    create_tts,
    create_vad,
)
from audio_recorder import ConversationRecorder
from http_server import init as init_http_server, run_server as run_http_server
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

    def __init__(self, chat_ctx, room_id: str, llm_instance: llm.LLM):
        super().__init__(
            instructions="",  # instructions not used — chat_ctx carries the system prompt
            chat_ctx=chat_ctx,
        )
        self.room_id = room_id
        self.last_msg_count = 0
        self._llm = llm_instance
        self._tasks = set()
        self._pref_lock = asyncio.Lock()

    async def on_enter(self):
        """Called when the agent session starts — greet the user."""
        await self.session.say(
            "Hi, I'm your Advanced Care Planning assistant. "
            "I'm here to help you think through and document your healthcare wishes "
            "for the future. There are no right or wrong answers — this is about "
            "what matters most to you. Shall we begin?"
        )
        # Log the first agent message
        await session_store.add_transcript_entry(
            self.room_id,
            TranscriptEntry(role="agent", text=(
                "Hi, I'm your Advanced Care Planning assistant. "
                "I'm here to help you think through and document your healthcare wishes "
                "for the future. There are no right or wrong answers — this is about "
                "what matters most to you. Shall we begin?"
            )),
        )
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

        # Fire background preference extraction (doesn't block conversation)
        task = asyncio.create_task(self._extract_preferences())
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

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

    # Create the LLM instance (shared by conversation and preference extraction)
    llm_instance = create_llm()

    # Create the agent instance (captures conversation logic)
    agent = ACPAgent(
        chat_ctx=create_initial_context(),
        room_id=room_id,
        llm_instance=llm_instance,
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
        llm=llm_instance,
        tts=tts,
        turn_handling={
            # Enable interruptions — user can cut in at any time
            "interruption": {
                "enabled": True,
                "mode": "vad",
                "min_duration": 0.3,
                "min_words": 2,
            },
            # Hypothesis endpointing — uses STT interim results to detect
            # sentence completion faster than waiting for silence
            "endpointing": {
                "mode": "hypothesis",
                "min_delay": 0.4,
                "max_delay": 1.5,
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

    # Run the HTTP server in a background thread with its own event loop
    def _run_http_loop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_start_background_services())
        loop.run_until_complete(run_http_server())

    http_thread = threading.Thread(target=_run_http_loop, daemon=True)
    http_thread.start()
    logger.info("HTTP API server thread started on port 8082")

    # Start the LiveKit agent
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        )
    )