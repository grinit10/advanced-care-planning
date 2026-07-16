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
    """Create an Azure OpenAI LLM instance.

    Uses a slightly elevated temperature (0.7) for more varied,
    natural-sounding speech rather than robotic repetition.
    """
    return openai.LLM(
        base_url=f"{AZURE_ENDPOINT}/openai/deployments/{AZURE_LLM_DEPLOYMENT}",
        api_key=AZURE_API_KEY,
        model=AZURE_LLM_DEPLOYMENT,
        extra_query={"api-version": AZURE_API_VERSION},
        temperature=0.7,
    )


def create_stt() -> deepgram.STT:
    """Create a Deepgram STT instance using the Australian endpoint.

    Configures streaming STT with smart formatting, natural endpointing,
    and filler words for more humane conversation transcripts.
    All voice data stays in Australia (AWS ap-southeast-2, Sydney).
    """
    return deepgram.STT(
        model="nova-3",
        language="en",
        api_key=DEEPGRAM_API_KEY,
        base_url="https://api.au.deepgram.com/v1/listen",
        # Smart formatting — numbers, dates, currency read naturally
        smart_format=True,
        # Keep filler words ("um", "uh") for natural transcripts
        filler_words=True,
        # Shorter endpointing for faster turn detection — 300ms
        endpointing_ms=300,
        # Return interim results for live transcription
        interim_results=True,
        # Enable VAD events for better turn detection
        vad_events=True,
        # No delay — stream audio as it arrives
        no_delay=True,
        # Punctuate for readability
        punctuate=True,
    )


def create_tts() -> deepgram.TTS:
    """Create a Deepgram TTS instance using the Australian endpoint.

    Uses the Aura-2 model for more natural, expressive speech.
    All voice data stays in Australia (AWS ap-southeast-2, Sydney).
    """
    return deepgram.TTS(
        model="aura-2-theia-en",
        api_key=DEEPGRAM_API_KEY,
        base_url="https://api.au.deepgram.com/v1/speak",
        # 24kHz sample rate for high-quality audio
        sample_rate=24000,
        # Linear16 encoding for wide compatibility
        encoding="linear16",
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
