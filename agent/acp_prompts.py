"""
ACP system prompt — loaded from prompt.yaml with locked TTS formatting rules.

The user-editable conversation content lives in prompt.yaml.
TTS output formatting rules are appended automatically by prompt_loader.py
and must NOT be modified (they ensure Azure OpenAI TTS sounds natural).

Usage:
    from acp_prompts import get_system_prompt, reload_prompt

    prompt = get_system_prompt()   # cached after first load
    reload_prompt()                 # force re-read from disk
"""

from prompt_loader import load_prompt

_CACHED_PROMPT: str | None = None


def get_system_prompt() -> str:
    """
    Return the full system prompt (user content + locked TTS rules).

    The result is cached on first call so disk I/O only happens once.
    Call reload_prompt() to force a re-read from prompt.yaml.
    """
    global _CACHED_PROMPT
    if _CACHED_PROMPT is None:
        _CACHED_PROMPT = load_prompt()
    return _CACHED_PROMPT


def reload_prompt() -> str:
    """
    Force re-read prompt.yaml from disk and update the cache.

    Returns the new prompt string.
    """
    global _CACHED_PROMPT
    _CACHED_PROMPT = load_prompt()
    return _CACHED_PROMPT