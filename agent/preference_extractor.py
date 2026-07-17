"""
Live preference extraction from ACP conversation transcripts.

After each user turn, calls the LLM to extract structured preferences
from the latest exchange. Runs asynchronously so it doesn't block
the conversation flow.

The extracted preferences are deep-merged into Redis and used to
generate a rich plan summary when the user requests it.
"""

import json
import logging
import re
from typing import Any

from livekit.agents import llm

logger = logging.getLogger("acp-agent.preferences")

# ---------------------------------------------------------------------------
# Preference schema — the full structure we build up over the conversation
# ---------------------------------------------------------------------------

EMPTY_PREFERENCES: dict[str, Any] = {
    "substitute_decision_maker": {
        "name": None,
        "relationship": None,
        "discussed": False,
        "notes": "",
    },
    "quality_of_life": {
        "values": [],
        "fears": [],
        "discussed": False,
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

# ---------------------------------------------------------------------------
# Extraction prompt
# ---------------------------------------------------------------------------

EXTRACTION_SYSTEM_PROMPT = """You are a preference extraction system for an Advanced Care Planning conversation. Your job is to carefully read the latest exchange between the user and the assistant, then update the preference JSON accordingly.

Rules:
1. Only set fields that the user has explicitly or implicitly expressed. Leave everything else as null or false.
2. For "values" and "fears" arrays, append new items — never remove existing ones.
3. Set "discussed" to true for any category that was touched in this exchange.
4. Use the user's own words in "notes" where possible.
5. If the user is unsure or hasn't decided yet, note that in "notes" rather than leaving it blank.
6. Return ONLY valid JSON. No markdown, no explanation, no surrounding text.
7. The JSON must match the schema exactly — include all top-level keys, even if unchanged.

Current preferences: {existing_prefs}

Latest exchange:
{exchange}

Return the complete updated preferences JSON:"""


async def extract_preferences(
    llm_instance: llm.LLM,
    exchange: str,
    existing_prefs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Extract structured preferences from a conversation exchange.

    Args:
        llm_instance: The LLM instance to use for extraction.
        exchange: The latest user+agent exchange as plain text.
        existing_prefs: Current preferences to merge into (or None for fresh).

    Returns:
        Updated preferences dict with any new information extracted.
    """
    if existing_prefs is None:
        existing_prefs = EMPTY_PREFERENCES

    # Merge existing prefs with empty schema to ensure all keys exist
    merged = _ensure_schema(existing_prefs)

    prompt = EXTRACTION_SYSTEM_PROMPT.format(
        existing_prefs=json.dumps(merged, indent=2),
        exchange=exchange,
    )

    try:
        chat_ctx = llm.ChatContext(
            items=[
                llm.ChatMessage(
                    role="system",
                    content=[prompt],
                ),
            ]
        )

        stream = llm_instance.chat(chat_ctx=chat_ctx)
        # Collect all chunks from the stream
        text_parts: list[str] = []
        async for chunk in stream:
            if chunk.delta and chunk.delta.content:
                text_parts.append(chunk.delta.content)
        text = "".join(text_parts)

        # Parse the JSON response
        parsed = _parse_json_response(text) if text else None
        if parsed:
            merged = _deep_merge(merged, parsed)
            logger.debug("Extracted preferences: %s", json.dumps(parsed, default=str))
        else:
            logger.warning("Failed to parse extraction response: %s", text[:200])

    except Exception as e:
        logger.error("Preference extraction failed: %s", e)

    return merged


def _ensure_schema(prefs: dict[str, Any]) -> dict[str, Any]:
    """Ensure all schema keys exist, filling in defaults for missing ones."""
    merged = {}
    for key, default in EMPTY_PREFERENCES.items():
        if key in prefs and isinstance(prefs[key], dict) and isinstance(default, dict):
            # Merge nested dicts
            merged[key] = {**default, **prefs[key]}
        else:
            merged[key] = prefs.get(key, default)
    return merged


def _parse_json_response(text: str) -> dict[str, Any] | None:
    """Parse JSON from LLM response, handling markdown code blocks."""
    # Strip markdown code fences if present
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find a JSON object in the text
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return None


def _canonical_key(item: Any) -> Any:
    """Return a hashable, canonical representation of a potentially nested dict/list/set."""
    if isinstance(item, dict):
        return tuple((k, _canonical_key(item[k])) for k in sorted(item.keys()))
    elif isinstance(item, list):
        return tuple(_canonical_key(x) for x in item)
    elif isinstance(item, set):
        return tuple(_canonical_key(x) for x in sorted(list(item), key=str))
    return item


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep-merge two dicts. Lists are appended, scalars are overwritten."""
    result = {}
    all_keys = set(base.keys()) | set(override.keys())
    for key in all_keys:
        if key in base and key in override:
            b, o = base[key], override[key]
            if isinstance(b, dict) and isinstance(o, dict):
                result[key] = _deep_merge(b, o)
            elif isinstance(b, list) and isinstance(o, list):
                # Append new items, avoid duplicates (independent of key order in dicts)
                seen = set()
                merged = []
                for item in b + o:
                    k = _canonical_key(item)
                    if k not in seen:
                        seen.add(k)
                        merged.append(item)
                result[key] = merged
            else:
                result[key] = o if o is not None else b
        elif key in override:
            result[key] = override[key]
        else:
            result[key] = base[key]
    return result


def to_fhir_questionnaire_response(
    preferences: dict[str, Any], patient_name: str = ""
) -> dict[str, Any]:
    """Convert extracted preferences to a standard FHIR QuestionnaireResponse resource."""
    import datetime

    # Base structure
    fhir_response = {
        "resourceType": "QuestionnaireResponse",
        "status": "completed",
        "authored": datetime.datetime.utcnow().isoformat() + "Z",
        "subject": {"display": patient_name or "Anonymous Patient"},
        "item": [],
    }

    # 1. Substitute Decision Maker
    sdm = preferences.get("substitute_decision_maker", {})
    if sdm.get("discussed"):
        fhir_response["item"].append(
            {
                "linkId": "substitute_decision_maker",
                "text": "Substitute Decision-Maker",
                "item": [
                    {
                        "linkId": "sdm_name",
                        "text": "Name",
                        "answer": [{"valueString": sdm.get("name") or "Not provided"}],
                    },
                    {
                        "linkId": "sdm_relationship",
                        "text": "Relationship",
                        "answer": [
                            {
                                "valueString": sdm.get("relationship")
                                or "Not provided"
                            }
                        ],
                    },
                    {
                        "linkId": "sdm_notes",
                        "text": "Notes",
                        "answer": [{"valueString": sdm.get("notes") or ""}],
                    },
                ],
            }
        )

    # 2. Quality of Life
    qol = preferences.get("quality_of_life", {})
    if qol.get("discussed"):
        qol_item = {
            "linkId": "quality_of_life",
            "text": "Quality of Life",
            "item": [
                {
                    "linkId": "qol_values",
                    "text": "Core Values",
                    "answer": [
                        {"valueString": val} for val in qol.get("values", []) if val
                    ],
                },
                {
                    "linkId": "qol_fears",
                    "text": "Fears & Concerns",
                    "answer": [
                        {"valueString": fear} for fear in qol.get("fears", []) if fear
                    ],
                },
                {
                    "linkId": "qol_notes",
                    "text": "Notes",
                    "answer": [{"valueString": qol.get("notes") or ""}],
                },
            ],
        }
        fhir_response["item"].append(qol_item)

    # 3. Treatment Preferences
    tx = preferences.get("treatment_preferences", {})
    if tx.get("discussed"):
        fhir_response["item"].append(
            {
                "linkId": "treatment_preferences",
                "text": "Treatment Preferences",
                "item": [
                    {
                        "linkId": "tx_life_support",
                        "text": "Life Support",
                        "answer": [
                            {
                                "valueString": str(
                                    tx.get("life_support") or "Not discussed"
                                )
                            }
                        ],
                    },
                    {
                        "linkId": "tx_cpr",
                        "text": "CPR",
                        "answer": [
                            {"valueString": str(tx.get("cpr") or "Not discussed")}
                        ],
                    },
                    {
                        "linkId": "tx_feeding_tubes",
                        "text": "Feeding Tubes",
                        "answer": [
                            {
                                "valueString": str(
                                    tx.get("feeding_tubes") or "Not discussed"
                                )
                            }
                        ],
                    },
                    {
                        "linkId": "tx_pain_management",
                        "text": "Pain Management",
                        "answer": [
                            {
                                "valueString": str(
                                    tx.get("pain_management") or "Not discussed"
                                )
                            }
                        ],
                    },
                    {
                        "linkId": "tx_notes",
                        "text": "Notes",
                        "answer": [{"valueString": tx.get("notes") or ""}],
                    },
                ],
            }
        )

    # 4. Values & Beliefs
    pb = preferences.get("personal_beliefs", {})
    if pb.get("discussed"):
        fhir_response["item"].append(
            {
                "linkId": "personal_beliefs",
                "text": "Values & Beliefs",
                "item": [
                    {
                        "linkId": "pb_faith_role",
                        "text": "Role of Faith/Spirituality",
                        "answer": [
                            {
                                "valueString": pb.get("faith_role") or "Not discussed"
                            }
                        ],
                    },
                    {
                        "linkId": "pb_cultural_values",
                        "text": "Cultural Values",
                        "answer": [
                            {
                                "valueString": val}
                            for val in pb.get("cultural_values", [])
                            if val
                        ],
                    },
                    {
                        "linkId": "pb_notes",
                        "text": "Notes",
                        "answer": [{"valueString": pb.get("notes") or ""}],
                    },
                ],
            }
        )

    # 5. Specific Scenarios
    ss = preferences.get("specific_scenarios", {})
    if ss.get("discussed"):
        fhir_response["item"].append(
            {
                "linkId": "specific_scenarios",
                "text": "Specific Scenarios",
                "item": [
                    {
                        "linkId": "ss_dementia",
                        "text": "Dementia Scenario",
                        "answer": [
                            {"valueString": ss.get("dementia") or "Not discussed"}
                        ],
                    },
                    {
                        "linkId": "ss_coma",
                        "text": "Permanent Coma Scenario",
                        "answer": [{"valueString": ss.get("coma") or "Not discussed"}],
                    },
                    {
                        "linkId": "ss_terminal_illness",
                        "text": "Terminal Illness Scenario",
                        "answer": [
                            {
                                "valueString": ss.get("terminal_illness")
                                or "Not discussed"
                            }
                        ],
                    },
                    {
                        "linkId": "ss_notes",
                        "text": "Notes",
                        "answer": [{"valueString": ss.get("notes") or ""}],
                    },
                ],
            }
        )

    # 6. Dignity & Values
    dv = preferences.get("dignity_and_values", {})
    if dv.get("discussed"):
        fhir_response["item"].append(
            {
                "linkId": "dignity_and_values",
                "text": "Dignity & Values",
                "item": [
                    {
                        "linkId": "dv_meaning_of_life",
                        "text": "What Gives Life Meaning",
                        "answer": [
                            {
                                "valueString": val}
                            for val in dv.get("meaning_of_life", [])
                            if val
                        ],
                    },
                    {
                        "linkId": "dv_dignity_definition",
                        "text": "Definition of Dignity",
                        "answer": [
                            {
                                "valueString": dv.get("dignity_definition")
                                or "Not discussed"
                            }
                        ],
                    },
                    {
                        "linkId": "dv_notes",
                        "text": "Notes",
                        "answer": [{"valueString": dv.get("notes") or ""}],
                    },
                ],
            }
        )

    return fhir_response

