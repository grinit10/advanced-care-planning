"""
Redis-backed session store for ACP conversation data.

Each active session stores:
  - Transcript (list of {role, text, timestamp})
  - Extracted preferences (key-value pairs)
  - Registered email addresses
  - Audio recording file path
  - Generated plan summary
  - Status (active | closed)

Key schema:
  session:{room_id}:status
  session:{room_id}:transcript   (list in Redis)
  session:{room_id}:preferences  (hash)
  session:{room_id}:emails       (set)
  session:{room_id}:metadata     (hash — room name, participant, timestamps)
"""

import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from typing import cast

import redis.asyncio as aioredis

logger = logging.getLogger("acp-agent.session")


@dataclass
class TranscriptEntry:
    role: str  # "user" | "agent"
    text: str
    timestamp: float = field(default_factory=time.time)


class SessionStore:
    """Redis-backed session store. One instance per agent process."""

    def __init__(self, redis_url: str = "redis://redis:6379/1"):
        self.redis_url = redis_url
        self._redis: aioredis.Redis | None = None
        self._prefix = "session"
        self.ttl = int(os.environ.get("SESSION_TTL", "86400"))

    async def _expire(self, key: str):
        """Set expiration TTL on the given key."""
        await self._r.expire(key, self.ttl)

    async def connect(self):
        """Connect to Redis."""
        self._redis = aioredis.from_url(self.redis_url, decode_responses=True)
        await self._redis.ping()
        logger.info("Connected to Redis session store")

    async def disconnect(self):
        if self._redis:
            await self._redis.close()

    def _key(self, room_id: str, *parts: str) -> str:
        return f"{self._prefix}:{room_id}:" + ":".join(parts)

    @property
    def _r(self) -> aioredis.Redis:  # type: ignore[type-arg]
        """Return the connected Redis client, raising if not yet connected."""
        if self._redis is None:
            raise RuntimeError("SessionStore: not connected — call connect() first")
        return self._redis

    # --- Status ---

    async def set_status(self, room_id: str, status: str):
        key = self._key(room_id, "status")
        await self._r.set(key, status)
        await self._expire(key)

    async def get_status(self, room_id: str) -> str | None:
        return cast("str | None", await self._r.get(self._key(room_id, "status")))

    # --- Metadata ---

    async def save_metadata(self, room_id: str, **kwargs):
        key = self._key(room_id, "metadata")
        await self._r.hset(key, mapping=kwargs)  # type: ignore[arg-type]
        await self._expire(key)

    # --- Transcript ---

    async def add_transcript_entry(self, room_id: str, entry: TranscriptEntry):
        """Append a single transcript entry."""
        key = self._key(room_id, "transcript")
        await self._r.rpush(key, json.dumps(asdict(entry)))
        # Keep only last 500 entries per session
        await self._r.ltrim(key, -500, -1)
        await self._expire(key)

    async def get_transcript(self, room_id: str) -> list[dict]:
        """Get full transcript for a session."""
        key = self._key(room_id, "transcript")
        raw = await self._r.lrange(key, 0, -1)
        return [json.loads(e) for e in raw]

    # --- Preferences ---

    async def set_preference(self, room_id: str, key: str, value: str):
        """Set a single preference key-value pair (flat string storage)."""
        pref_key = self._key(room_id, "preferences")
        await self._r.hset(pref_key, key, value)
        await self._expire(pref_key)

    async def get_preferences(self, room_id: str) -> dict:
        """Get all preferences. Returns a flat dict from Redis."""
        raw = await self._r.hgetall(self._key(room_id, "preferences"))
        return raw or {}

    async def get_preferences_json(self, room_id: str) -> dict:
        """Get the full nested preferences JSON object."""
        raw = cast(
            "str | None", await self._r.get(self._key(room_id, "preferences_json"))
        )
        if raw:
            try:
                return json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                pass
        return {}

    async def save_preferences_json(self, room_id: str, prefs: dict):
        """Save the full nested preferences JSON object (replaces entirely)."""
        key = self._key(room_id, "preferences_json")
        await self._r.set(
            key,
            json.dumps(prefs, default=str),
        )
        await self._expire(key)

    # --- Emails ---

    async def add_email(self, room_id: str, email: str):
        key = self._key(room_id, "emails")
        await self._r.sadd(key, email.lower())
        await self._expire(key)

    async def get_emails(self, room_id: str) -> list[str]:
        raw = await self._r.smembers(self._key(room_id, "emails"))
        return sorted(str(e) for e in raw) if raw else []

    # --- Audio ---

    async def set_audio_path(self, room_id: str, path: str):
        key = self._key(room_id, "audio_path")
        await self._r.set(key, path)
        await self._expire(key)

    async def get_audio_path(self, room_id: str) -> str | None:
        return cast("str | None", await self._r.get(self._key(room_id, "audio_path")))

    # --- Plan Summary ---

    async def set_plan_summary(self, room_id: str, summary: str):
        key = self._key(room_id, "plan_summary")
        await self._r.set(key, summary)
        await self._expire(key)

    async def get_plan_summary(self, room_id: str) -> str | None:
        return cast("str | None", await self._r.get(self._key(room_id, "plan_summary")))

    # --- Session lifecycle ---

    async def create_session(self, room_id: str, participant_identity: str = ""):
        """Initialise a new session."""
        await self.set_status(room_id, "active")
        await self.save_metadata(
            room_id,
            created_at=str(time.time()),
            participant_identity=participant_identity,
        )
        logger.info(
            "Session created: room=%s participant=%s", room_id, participant_identity
        )

    async def close_session(self, room_id: str) -> dict:
        """Close a session and return all data before deletion."""
        data = await self.get_session_data(room_id)
        await self.set_status(room_id, "closed")
        # Delete all keys for this session
        pattern = f"{self._prefix}:{room_id}:*"
        cursor = 0
        deleted = 0
        while True:
            cursor, keys = await self._r.scan(cursor, match=pattern, count=100)
            if keys:
                await self._r.delete(*keys)
                deleted += len(keys)
            if cursor == 0:
                break
        logger.info("Session closed: room=%s (%d keys deleted)", room_id, deleted)
        return data

    async def get_session_data(self, room_id: str) -> dict:
        """Return all session data for sending."""
        return {
            "room_id": room_id,
            "status": await self.get_status(room_id),
            "transcript": await self.get_transcript(room_id),
            "preferences": await self.get_preferences(room_id),
            "preferences_json": await self.get_preferences_json(room_id),
            "emails": await self.get_emails(room_id),
            "audio_path": await self.get_audio_path(room_id),
            "plan_summary": await self.get_plan_summary(room_id),
        }
