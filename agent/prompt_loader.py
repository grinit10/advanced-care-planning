"""
Prompt loader for the ACP voice agent.

Loads the user-editable conversation prompt from prompt.yaml,
then appends locked TTS formatting rules that must NOT be modified.

Architecture:
  prompt.yaml  (user edits this freely)
       ↓
  prompt_loader.py  (reads yaml, appends locked TTS rules)
       ↓
  acp_prompts.py  →  VoicePipelineAgent
"""

import os
import logging
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # will raise a clear error at load time

logger = logging.getLogger("acp-agent.prompt")

# =============================================================================
# LOCKED: TTS Output Formatting Rules
#
# These rules ensure the LLM outputs text that sounds natural when spoken
# by any TTS engine. Do NOT modify this section. If you need different
# TTS output formatting, configure the TTS voice/model in .env instead.
# =============================================================================

TTS_FORMATTING_RULES = """
## TTS Output Rules (locked — required for voice quality)

Follow these rules so your responses sound natural when spoken by text-to-speech:

### Text Formatting
- Write in complete sentences with proper punctuation (periods, commas, question marks)
- Use natural contractions: don't, can't, it's, you're, I'll, won't
- Spell out all numbers: "three" not "3", "twenty percent" not "20%"
- Spell out abbreviations on first mention: "for example" not "e.g."
- Avoid symbols: write "and" not "&", "dollars" not "$", "percent" not "%"
- Avoid ALL CAPS — use emphasis through sentence structure instead
- Never use ellipsis (...) — end sentences cleanly with periods

### Structure
- Keep each response to 2-4 sentences. Short turns sound more natural.
- Never use markdown formatting (no **bold**, *italic*, `code`, or ## headings)
- Never use bullet points, numbered lists, or dashes for lists
- Never use tables or complex formatting
- Use plain paragraphs only. A single blank line between paragraphs is fine.

### Conversational Flow
- End every response with a complete sentence — never trail off
- Ask one question at a time so the user can respond naturally
- Use the user's own words when reflecting back what they've said
- Avoid repeating the same phrase or question structure in consecutive turns
- If summarizing, keep it brief: one sentence per key point

### Tone for Spoken Delivery
- Use a warm, conversational tone suitable for the "coral" voice
- Speak as if you're sitting across from the user, not reading a document
- Use short, simple sentences that are easy to follow by ear
- Pause naturally with commas and periods — these create breathing room in speech
"""


def load_prompt(prompt_path: str | None = None) -> str:
    """
    Load the user prompt from prompt.yaml and append locked TTS rules.

    Args:
        prompt_path: Path to prompt.yaml. Defaults to <this file's dir>/prompt.yaml.

    Returns:
        Full system prompt string (user ACP content + locked TTS rules).
    """
    if yaml is None:
        raise ImportError(
            "PyYAML is required to load prompt.yaml. "
            "Install it with: pip install pyyaml"
        )

    if prompt_path is None:
        prompt_path = str(Path(__file__).resolve().parent / "prompt.yaml")

    path = Path(prompt_path)

    if not path.exists():
        logger.warning(
            "prompt.yaml not found at %s. Falling back to built-in prompt.",
            path,
        )
        return _builtin_default() + TTS_FORMATTING_RULES

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or "prompt" not in data:
            logger.warning(
                "prompt.yaml is missing the 'prompt' key. Using built-in prompt."
            )
            return _builtin_default() + TTS_FORMATTING_RULES

        user_prompt = data["prompt"].strip()
        full_prompt = user_prompt + "\n\n---\n" + TTS_FORMATTING_RULES.strip()
        logger.info("Loaded prompt from %s (%d chars)", path, len(user_prompt))
        return full_prompt

    except yaml.YAMLError as e:
        logger.error("Failed to parse prompt.yaml: %s", e)
        raise
    except OSError as e:
        logger.error("Failed to read prompt.yaml: %s", e)
        raise


def _builtin_default() -> str:
    """Built-in fallback prompt if prompt.yaml is missing."""
    return (
        "You are a compassionate Advanced Care Planning (ACP) assistant. "
        "Your role is to help people articulate their preferences for future "
        "healthcare decisions in a natural, conversational way.\n\n"
        "Speak calmly, clearly, and with empathy. "
        "Ask one question at a time. "
        "Use plain language. "
        "Never provide medical advice. "
        "Guide the conversation through values, healthcare proxy wishes, "
        "quality of life preferences, and specific care scenarios."
    )