"""Shared fixtures and configuration for agent tests."""

from pathlib import Path

import pytest


@pytest.fixture
def sample_prompt_yaml(tmp_path: Path) -> Path:
    """Create a temporary prompt.yaml for testing."""
    content = """
prompt: |
  You are a compassionate Advanced Care Planning assistant.
  Speak calmly and with empathy.
"""
    yaml_path = tmp_path / "prompt.yaml"
    yaml_path.write_text(content)
    return yaml_path


@pytest.fixture
def sample_transcript_entries() -> list[dict]:
    """Return sample transcript entries for testing."""
    return [
        {"role": "agent", "text": "Hello, how can I help you today?", "timestamp": 1000.0},
        {"role": "user", "text": "I want to talk about my healthcare wishes.", "timestamp": 1001.0},
        {"role": "agent", "text": "That's wonderful. What matters most to you?", "timestamp": 1002.0},
    ]


@pytest.fixture
def sample_preferences() -> dict:
    """Return sample extracted preferences for testing."""
    return {
        "substitute_decision_maker": {
            "name": "Jane Doe",
            "relationship": "Daughter",
            "discussed": True,
            "notes": "Trusts her to make decisions",
        },
        "quality_of_life": {
            "values": ["Independence", "Time with family"],
            "fears": ["Being a burden"],
            "discussed": True,
            "notes": "",
        },
        "treatment_preferences": {
            "life_support": None,
            "cpr": None,
            "feeding_tubes": None,
            "pain_management": None,
            "discussed": False,
            "notes": "",
        },
        "personal_beliefs": {
            "faith_role": None,
            "cultural_values": [],
            "discussed": False,
            "notes": "",
        },
        "specific_scenarios": {
            "dementia": None,
            "coma": None,
            "terminal_illness": None,
            "discussed": False,
            "notes": "",
        },
        "dignity_and_values": {
            "meaning_of_life": [],
            "dignity_definition": None,
            "discussed": False,
            "notes": "",
        },
    }