from livekit.plugins import deepgram, openai, silero
from livekit.agents import ChatContext, ChatMessage

from acp_prompts import get_system_prompt

import os


# =============================================================================
# Credentials loaded from .env (via load_dotenv in main.py)
# =============================================================================
AZURE_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
AZURE_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY", "")
AZURE_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
AZURE_LLM_DEPLOYMENT = os.environ.get("AZURE_OPENAI_LLM_DEPLOYMENT", "")

DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY", "")


def create_llm() -> openai.LLM:
    """Create an Azure OpenAI LLM instance."""
    return openai.LLM(
        base_url=f"{AZURE_ENDPOINT}/openai/deployments/{AZURE_LLM_DEPLOYMENT}",
        api_key=AZURE_API_KEY,
        model=AZURE_LLM_DEPLOYMENT,
        extra_query={"api-version": AZURE_API_VERSION},
    )


def create_stt() -> deepgram.STT:
    """Create a Deepgram STT instance with default config."""
    return deepgram.STT(
        model="nova-3",
        language="en",
        api_key=DEEPGRAM_API_KEY,
    )


def create_tts() -> deepgram.TTS:
    """Create a Deepgram TTS instance with default config."""
    return deepgram.TTS(
        model="aura-asteria-en",
        api_key=DEEPGRAM_API_KEY,
    )


def create_vad():
    """Create a Silero VAD instance (runs locally on CPU)."""
    return silero.VAD.load()


def create_initial_context() -> ChatContext:
    """Create the initial chat context with the ACP system prompt.

    The prompt is loaded from prompt.yaml (user-editable) with
    locked TTS formatting rules appended automatically.
    """
    return ChatContext(
        items=[
            ChatMessage(
                role="system",
                content=[get_system_prompt()],
            ),
        ]
    )
