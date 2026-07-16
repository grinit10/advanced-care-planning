"""Tests for prompt_loader.py."""

from pathlib import Path

import pytest
import yaml
from prompt_loader import TTS_FORMATTING_RULES, load_prompt


def test_load_prompt_from_yaml(sample_prompt_yaml: Path):
    """Test that load_prompt reads a YAML file and appends TTS rules."""
    result = load_prompt(str(sample_prompt_yaml))
    assert "Advanced Care Planning" in result
    assert TTS_FORMATTING_RULES.strip() in result
    assert "---" in result  # separator between user prompt and TTS rules


def test_load_prompt_missing_file(tmp_path: Path):
    """Test fallback to built-in prompt when prompt.yaml is missing."""
    result = load_prompt(str(tmp_path / "nonexistent_prompt.yaml"))
    assert "You are a compassionate Advanced Care Planning" in result
    assert TTS_FORMATTING_RULES.strip() in result


def test_load_prompt_empty_yaml(tmp_path: Path):
    """Test fallback when YAML has no 'prompt' key."""
    yaml_path = tmp_path / "prompt.yaml"
    yaml_path.write_text("other_key: hello\n")
    result = load_prompt(str(yaml_path))
    assert "You are a compassionate" in result
    assert TTS_FORMATTING_RULES.strip() in result


def test_load_prompt_caches_across_calls(sample_prompt_yaml: Path):
    """Test that repeated calls return the same content."""
    result1 = load_prompt(str(sample_prompt_yaml))
    result2 = load_prompt(str(sample_prompt_yaml))
    assert result1 == result2


def test_tts_formatting_rules_contain_critical_sections():
    """Verify that the TTS formatting rules include expected sections."""
    assert "Deepgram TTS Delivery Rules" in TTS_FORMATTING_RULES
    assert "Punctuation Creates Natural Pacing" in TTS_FORMATTING_RULES
    assert "Writing Questions That Sound Like Questions" in TTS_FORMATTING_RULES
    assert "Use Filler Words for Natural Speech" in TTS_FORMATTING_RULES
    assert "The Deepgram Formatting Checklist" in TTS_FORMATTING_RULES


def test_user_prompt_comes_before_tts_rules(sample_prompt_yaml: Path):
    """Test that the user prompt appears before the TTS rules."""
    result = load_prompt(str(sample_prompt_yaml))
    user_idx = result.index("Advanced Care Planning")
    tts_idx = result.index("Deepgram TTS Delivery Rules")
    assert user_idx < tts_idx, "User prompt should appear before TTS rules"


def test_load_prompt_with_invalid_yaml(tmp_path: Path):
    """Test that invalid YAML raises an error."""
    yaml_path = tmp_path / "prompt.yaml"
    yaml_path.write_text(": : invalid yaml : :\n")
    with pytest.raises(yaml.YAMLError):
        load_prompt(str(yaml_path))

