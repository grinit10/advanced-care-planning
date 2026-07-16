"""Tests for preference_extractor.py."""

import json

from preference_extractor import (
    EMPTY_PREFERENCES,
    _deep_merge,
    _ensure_schema,
    _parse_json_response,
)


class TestEnsureSchema:
    def test_returns_empty_preferences_for_empty_dict(self):
        result = _ensure_schema({})
        assert result == EMPTY_PREFERENCES

    def test_preserves_existing_values(self):
        existing = {"substitute_decision_maker": {"name": "Jane", "discussed": True}}
        result = _ensure_schema(existing)
        assert result["substitute_decision_maker"]["name"] == "Jane"
        assert result["substitute_decision_maker"]["discussed"] is True
        # Should still have all keys
        assert result["substitute_decision_maker"]["relationship"] is None

    def test_merges_nested_dicts(self):
        existing = {"quality_of_life": {"values": ["Independence"]}}
        result = _ensure_schema(existing)
        assert result["quality_of_life"]["values"] == ["Independence"]
        assert result["quality_of_life"]["fears"] == []


class TestParseJsonResponse:
    def test_parses_plain_json(self):
        text = '{"key": "value", "num": 42}'
        result = _parse_json_response(text)
        assert result == {"key": "value", "num": 42}

    def test_parses_json_in_code_block(self):
        text = '```json\n{"key": "value"}\n```'
        result = _parse_json_response(text)
        assert result == {"key": "value"}

    def test_parses_json_in_code_block_without_lang(self):
        text = '```\n{"key": "value"}\n```'
        result = _parse_json_response(text)
        assert result == {"key": "value"}

    def test_returns_none_for_invalid_json(self):
        text = "This is not JSON at all"
        result = _parse_json_response(text)
        assert result is None

    def test_extracts_json_from_surrounding_text(self):
        text = "Here is the result: {\"key\": \"value\"}. Hope that helps."
        result = _parse_json_response(text)
        assert result == {"key": "value"}

    def test_handles_empty_string(self):
        result = _parse_json_response("")
        assert result is None

    def test_handles_nested_json(self):
        text = '{"a": {"b": ["c", "d"]}}'
        result = _parse_json_response(text)
        assert result == {"a": {"b": ["c", "d"]}}


class TestDeepMerge:
    def test_scalar_overwrites(self):
        base = {"a": 1, "b": 2}
        override = {"b": 3}
        result = _deep_merge(base, override)
        assert result == {"a": 1, "b": 3}

    def test_dicts_merge_recursively(self):
        base = {"a": {"x": 1, "y": 2}}
        override = {"a": {"y": 3, "z": 4}}
        result = _deep_merge(base, override)
        assert result == {"a": {"x": 1, "y": 3, "z": 4}}

    def test_lists_append_without_duplicates(self):
        base = {"items": ["a", "b"]}
        override = {"items": ["b", "c"]}
        result = _deep_merge(base, override)
        assert result == {"items": ["a", "b", "c"]}

    def test_new_keys_added(self):
        base = {"a": 1}
        override = {"b": 2}
        result = _deep_merge(base, override)
        assert result == {"a": 1, "b": 2}

    def test_override_none_keeps_base(self):
        base = {"a": 1}
        override = {"a": None}
        result = _deep_merge(base, override)
        assert result == {"a": 1}

    def test_empty_dicts(self):
        result = _deep_merge({}, {})
        assert result == {}

    def test_mixed_types(self):
        base = {"config": {"port": 8080, "host": "localhost"}}
        override = {"config": {"port": 9090}}
        result = _deep_merge(base, override)
        assert result == {"config": {"port": 9090, "host": "localhost"}}


class TestEmptyPreferences:
    def test_has_all_required_sections(self):
        required = [
            "substitute_decision_maker",
            "quality_of_life",
            "treatment_preferences",
            "personal_beliefs",
            "specific_scenarios",
            "dignity_and_values",
        ]
        for section in required:
            assert section in EMPTY_PREFERENCES, f"Missing section: {section}"

    def test_all_sections_have_discussed_field(self):
        for section, config in EMPTY_PREFERENCES.items():
            if isinstance(config, dict):
                assert "discussed" in config, f"Missing 'discussed' in {section}"
                assert config["discussed"] is False, f"'discussed' should be False in {section}"

    def test_can_be_serialized_to_json(self):
        json_str = json.dumps(EMPTY_PREFERENCES)
        parsed = json.loads(json_str)
        assert parsed.keys() == EMPTY_PREFERENCES.keys()
