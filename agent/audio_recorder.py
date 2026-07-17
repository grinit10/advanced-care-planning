"""Conversation audio recorder.

Captures both sides of the conversation (user mic + agent TTS output)
from LiveKit room audio tracks and saves them as a single WAV file.
"""

import asyncio
import contextlib
import logging
import os
import time
import wave
from pathlib import Path

from livekit import rtc

logger = logging.getLogger("acp-agent.audio")

SAMPLE_RATE = 24000
CHANNELS = 1
SAMPLE_WIDTH = 2


class ConversationRecorder:
    """Records a LiveKit room conversation to a WAV file."""

    def __init__(
        self,
        room: rtc.Room,
        participant_identity: str,
        records_dir: str = "recordings",
    ):
        self._room = room
        self._participant_identity = participant_identity
        self._records_dir = Path(records_dir)
        self._audio_frames: list[bytes] = []
        self._recording = False
        self._read_task: asyncio.Task | None = None
        self._all_streams: list[rtc.AudioStream] = []

    async def start(self):
        """Subscribe to all audio tracks in the room and start recording."""
        self._records_dir.mkdir(parents=True, exist_ok=True)
        self._audio_frames = []
        self._recording = True

        streams = []

        # Wait up to 5 seconds for the participant's audio track to be published and subscribed
        for _ in range(50):
            if not self._recording:
                return
            participant = self._room.remote_participants.get(self._participant_identity)
            if participant:
                for pub in participant.track_publications.values():
                    if pub.kind == rtc.TrackKind.KIND_AUDIO and pub.track:
                        stream = rtc.AudioStream(pub.track)
                        streams.append(stream)
                        break
            if streams:
                break
            await asyncio.sleep(0.1)

        if not streams:
            logger.warning(
                "No audio track for %s after waiting. Recording disabled.",
                self._participant_identity,
            )
            self._recording = False
            return

        self._all_streams = streams
        self._read_task = asyncio.create_task(self._read_all_streams())
        logger.info("Started recording audio for %s", self._participant_identity)

    async def _read_all_streams(self):
        """Read audio frames from all subscribed streams concurrently."""

        async def read_one(stream: rtc.AudioStream):
            try:
                async for event in stream:
                    if not self._recording:
                        break
                    frame = getattr(event, "frame", event)
                    # frame.data is a memoryview/numpy array; convert to bytes
                    raw = getattr(frame, "data", None)
                    if raw is not None:
                        self._audio_frames.append(bytes(raw))
            except Exception as e:
                if self._recording:
                    logger.error("Audio stream error: %s", e)

        await asyncio.gather(*[read_one(s) for s in self._all_streams])

    async def stop(self):
        """Stop recording."""
        self._recording = False
        for stream in self._all_streams:
            with contextlib.suppress(Exception):
                await stream.aclose()  # type: ignore[attr-defined]
        self._all_streams.clear()
        if self._read_task:
            self._read_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._read_task
            self._read_task = None
        logger.info(
            "Stopped recording. Captured %d audio frames",
            len(self._audio_frames),
        )

    def save(self, room_id: str) -> str | None:
        """Save recorded audio to a WAV file and return the file path."""
        if not self._audio_frames:
            logger.warning("No audio frames to save")
            return None

        filename = f"conversation_{room_id}_{int(time.time())}.wav"
        filepath = str(self._records_dir / filename)

        try:
            with wave.open(filepath, "wb") as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(SAMPLE_WIDTH)
                wf.setframerate(SAMPLE_RATE)
                for frame_data in self._audio_frames:
                    wf.writeframes(frame_data)

            file_size = os.path.getsize(filepath)
            logger.info(
                "Saved recording: %s (%d bytes)",
                filepath,
                file_size,
            )
            return filepath
        except Exception as e:
            logger.error("Failed to save recording: %s", e)
            return None

    @staticmethod
    def cleanup(filepath: str):
        """Delete a recording file."""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info("Deleted recording: %s", filepath)
        except Exception as e:
            logger.warning("Failed to delete recording %s: %s", filepath, e)
