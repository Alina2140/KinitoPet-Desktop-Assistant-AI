"""Extract durable memory updates from chat turns via Ollama."""

from __future__ import annotations

import json
import re
from typing import Any

from content import llm_prompts as prompts
from content.memory_keys import ALLOWED_FACT_KEYS, LEGACY_FACT_KEY_ALIASES, MULTI_VALUE_FACT_KEYS
from kinito.llm.ollama_client import OllamaClient, OllamaUnavailableError
from kinito.memory.fact_values import normalize_fact_value_list, split_fact_values
from kinito.memory.store import MAX_NEW_NOTES_PER_TURN, MemoryStore
from kinito.memory.validation import is_storable_note, should_skip_note_against_existing

_JSON_BLOCK_RE = re.compile(r"\{[\s\S]*\}")
_WORD_RE = re.compile(r"[^\W_]+", re.UNICODE)
_VALID_INTENTS = frozenset({"add", "replace", "remove"})
_EXTRACT_MAX_TOKENS = 480
_EXTRACT_TURN_WINDOW = 4  # user/assistant messages to include

# Topic stems for likes_* yes/no facts (value need not appear literally).
_LIKES_TOPIC_STEMS: dict[str, tuple[str, ...]] = {
    "likes_programming": ("programming", "coding", "code"),
    "likes_music": ("music",),
    "likes_coffee": ("coffee",),
    "likes_rain": ("rain",),
    "likes_horror": ("horror",),
    "likes_spicy_food": ("spicy",),
    "likes_staying_up_late": ("late", "night owl", "stay up"),
}

# Keys that must not be filled from casual mentions (reading X ≠ favorite_book).
_EXPLICIT_PREFERENCE_KEYS = frozenset(
    {
        "favorite_book",
        "favorite_movie",
        "favorite_show",
        "favorite_food",
        "favorite_drink",
        "favorite_game",
        "favorite_artist",
        "favorite_app",
        "favorite_animal",
        "favorite_colors",
        "favorite_snacks",
        "favorite_seasons",
        "comfort_food",
        "dream_destination",
        "morning_drink",
    }
)

_EXPLICIT_PREFERENCE_RE = re.compile(
    r"\b("
    r"favorite|favourite|prefer|preferred|prefers|"
    r"go[\s-]?to|my\s+fav(?:ou?rite)?|"
    r"fav(?:ou?rite)?\s+(?:book|movie|show|food|drink|game|color|colour|snack|season|artist|app|animal)"
    r")\b",
    re.IGNORECASE,
)

_PREFERENCE_CORRECTION_RE = re.compile(
    r"\b("
    r"don'?t like|do not like|no longer|not anymore|anymore|used to like|hate"
    r")\b",
    re.IGNORECASE,
)

_PREFERENCE_QUESTION_RE = re.compile(
    r"\b("
    r"favorite|favourite|prefer|hobby|hobbies|"
    r"what(?:'s| is) your|call you|name|"
    r"drink|food|color|colour|snack|pet|job|work|birthday|pronoun"
    r")\b",
    re.IGNORECASE,
)

# Topic hints so "What's your favorite book?" unlocks favorite_book answers only.
_KEY_QUESTION_HINTS: dict[str, tuple[str, ...]] = {
    "favorite_book": ("book", "novel", "read"),
    "favorite_movie": ("movie", "film"),
    "favorite_show": ("show", "series", "tv"),
    "favorite_food": ("food", "eat", "dish"),
    "favorite_drink": ("drink", "beverage"),
    "favorite_game": ("game", "play"),
    "favorite_artist": ("artist", "band", "musician", "singer"),
    "favorite_app": ("app", "application"),
    "favorite_animal": ("animal", "pet"),
    "favorite_colors": ("color", "colour"),
    "favorite_snacks": ("snack",),
    "favorite_seasons": ("season",),
    "comfort_food": ("comfort food", "comfort"),
    "dream_destination": ("travel", "destination", "trip", "visit"),
    "morning_drink": ("morning", "drink"),
}

_GAME_CHAT_RE = re.compile(
    r"\b("
    r"hangman|word\s*chain|wordchain|trivia|riddle|guess the|"
    r"tic[\s-]?tac[\s-]?toe|minesweeper|battleship|connect\s*four|"
    r"letter\b"
    r")\b",
    re.IGNORECASE,
)


def parse_extraction_response(raw: str) -> dict[str, Any]:
    """Parse JSON from an Ollama extraction reply."""
    text = raw.strip()
    if not text:
        return {}
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    match = _JSON_BLOCK_RE.search(text)
    if not match:
        return {}
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def format_chat_transcript(messages: list[dict[str, str]]) -> str:
    """Format role/content messages for the extract prompt."""
    lines: list[str] = []
    for message in messages:
        role = message.get("role", "")
        content = (message.get("content") or "").strip()
        if not content:
            continue
        label = "User" if role == "user" else "Assistant" if role == "assistant" else role.title()
        lines.append(f"{label}: {content}")
    return "\n".join(lines) if lines else "(empty)"


def collect_user_text(messages: list[dict[str, str]]) -> str:
    """Concatenate user message contents for gate checks."""
    parts = [
        (message.get("content") or "").strip()
        for message in messages
        if message.get("role") == "user" and (message.get("content") or "").strip()
    ]
    return "\n".join(parts)


def _normalize_haystack(text: str) -> str:
    return " ".join(_WORD_RE.findall(text.casefold()))


def value_mentioned_in_text(value: str, user_text: str) -> bool:
    """Return True when *value* (or its significant tokens) appear in *user_text*."""
    needle = value.strip()
    if not needle or not user_text.strip():
        return False
    hay_raw = user_text.casefold()
    if needle.casefold() in hay_raw:
        return True
    tokens = [token for token in _WORD_RE.findall(needle.casefold()) if len(token) > 2]
    if not tokens:
        return needle.casefold() in hay_raw
    hay = _normalize_haystack(user_text)
    return all(token in hay.split() or token in hay for token in tokens)


def _likes_topic_supported(key: str, user_text: str) -> bool:
    stems = _LIKES_TOPIC_STEMS.get(key)
    if not stems:
        return False
    hay = user_text.casefold()
    return any(stem in hay for stem in stems)


def _items_from_claim_value(value: Any) -> list[str]:
    if isinstance(value, list):
        return normalize_fact_value_list(value)
    if isinstance(value, str):
        return split_fact_values(value) if ("," in value or ";" in value or " and " in value.casefold()) else (
            [value.strip()] if value.strip() else []
        )
    return []


def _default_intent(key: str, value: Any, *, had_explicit_list: bool) -> str:
    if key in MULTI_VALUE_FACT_KEYS:
        if had_explicit_list:
            return "replace"
        return "add"
    return "replace"


def _parse_claim(key: str, raw: Any) -> dict[str, Any] | None:
    """Normalize one update_facts entry into {{value, intent}} or None."""
    if isinstance(raw, dict):
        intent_raw = raw.get("intent")
        intent = intent_raw.strip().casefold() if isinstance(intent_raw, str) else ""
        if intent not in _VALID_INTENTS:
            return None
        value = raw.get("value")
        if key in MULTI_VALUE_FACT_KEYS:
            if isinstance(value, list):
                items = normalize_fact_value_list(value)
            elif isinstance(value, str):
                items = _items_from_claim_value(value)
            else:
                return None
            if not items:
                return None
            stored: str | list[str] = items if len(items) > 1 or intent == "replace" else items[0]
            if intent == "replace":
                stored = items
            elif len(items) == 1:
                stored = items[0]
            else:
                stored = items
            return {"value": stored, "intent": intent}
        if isinstance(value, list):
            items = normalize_fact_value_list(value)
            if not items:
                return None
            return {"value": items[0], "intent": intent}
        if isinstance(value, str) and value.strip():
            return {"value": value.strip(), "intent": intent}
        return None

    if key in MULTI_VALUE_FACT_KEYS:
        if isinstance(raw, list):
            items = normalize_fact_value_list(raw)
            if not items:
                return None
            return {"value": items, "intent": _default_intent(key, raw, had_explicit_list=True)}
        if isinstance(raw, str) and raw.strip():
            return {
                "value": raw.strip(),
                "intent": _default_intent(key, raw, had_explicit_list=False),
            }
        return None

    if isinstance(raw, str) and raw.strip():
        return {"value": raw.strip(), "intent": _default_intent(key, raw, had_explicit_list=False)}
    return None


def _claim_items_supported(key: str, items: list[str], intent: str, user_text: str) -> bool:
    if not items:
        return False
    if key.startswith("likes_") and len(items) == 1 and items[0].casefold() in {"yes", "no"}:
        return _likes_topic_supported(key, user_text)

    mentioned = [item for item in items if value_mentioned_in_text(item, user_text)]
    if intent == "replace" and key in MULTI_VALUE_FACT_KEYS and len(items) > 1:
        return len(mentioned) * 2 >= len(items)  # >= 50%
    if intent in {"add", "remove", "replace"}:
        return len(mentioned) == len(items)
    return False


def _is_bare_word_turn(text: str) -> bool:
    tokens = _WORD_RE.findall(text.strip())
    return 1 <= len(tokens) <= 2 and len(text.strip()) <= 40


def _assistant_message_before_latest_user(messages: list[dict[str, str]]) -> str:
    last_user_index = None
    for index in range(len(messages) - 1, -1, -1):
        if messages[index].get("role") == "user":
            last_user_index = index
            break
    if last_user_index is None:
        return ""
    for index in range(last_user_index - 1, -1, -1):
        if messages[index].get("role") == "assistant":
            return messages[index].get("content") or ""
    return ""


def _prior_assistant_asks_preference(messages: list[dict[str, str]]) -> bool:
    """Return True if the assistant message before the latest user ask looks personal."""
    content = _assistant_message_before_latest_user(messages)
    return bool(content and _PREFERENCE_QUESTION_RE.search(content))


def _assistant_asked_about_key(messages: list[dict[str, str]], key: str) -> bool:
    """Return True when the prior assistant question targets *key*'s topic."""
    content = _assistant_message_before_latest_user(messages).casefold()
    if not content or not _PREFERENCE_QUESTION_RE.search(content):
        return False
    hints = _KEY_QUESTION_HINTS.get(key)
    if not hints:
        return key.startswith("favorite_") and "favorite" in content
    return any(hint in content for hint in hints)


def _has_explicit_preference_claim(
    key: str,
    user_text: str,
    messages: list[dict[str, str]],
    *,
    intent: str = "replace",
) -> bool:
    """Favorite-like keys need explicit preference wording or a matching question."""
    if key not in _EXPLICIT_PREFERENCE_KEYS:
        return True
    if _EXPLICIT_PREFERENCE_RE.search(user_text):
        return True
    if intent == "remove" and _PREFERENCE_CORRECTION_RE.search(user_text):
        return True
    return _assistant_asked_about_key(messages, key)


def should_block_fact_updates(user_text: str, messages: list[dict[str, str]]) -> bool:
    """Return True when fact updates from this turn should be ignored."""
    latest_user = ""
    for message in reversed(messages):
        if message.get("role") == "user":
            latest_user = (message.get("content") or "").strip()
            break
    if not latest_user:
        latest_user = user_text.strip()

    if _GAME_CHAT_RE.search(latest_user):
        return True
    return _is_bare_word_turn(latest_user) and not _prior_assistant_asks_preference(messages)


def normalize_extraction(
    payload: dict[str, Any],
    *,
    user_text: str = "",
    messages: list[dict[str, str]] | None = None,
    existing_notes: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Validate and trim extractor JSON before applying to the store."""
    result: dict[str, Any] = {
        "add_notes": [],
        "remove_notes": [],
        "update_facts": {},
    }
    messages = messages or []
    existing_notes = existing_notes or []
    gate_user_text = user_text.strip() or collect_user_text(messages)

    add_notes = payload.get("add_notes")
    if isinstance(add_notes, list):
        for item in add_notes[:MAX_NEW_NOTES_PER_TURN]:
            if isinstance(item, str):
                trimmed = item.strip()
                if not trimmed or not is_storable_note(trimmed, source="chat"):
                    continue
                pending = [{"text": note} for note in result["add_notes"]]
                if should_skip_note_against_existing(trimmed, existing_notes + pending):
                    continue
                result["add_notes"].append(trimmed)

    remove_notes = payload.get("remove_notes")
    if isinstance(remove_notes, list):
        for item in remove_notes:
            if isinstance(item, str) and item.strip():
                result["remove_notes"].append(item.strip())

    block_facts = should_block_fact_updates(gate_user_text, messages)
    update_facts = payload.get("update_facts")
    if isinstance(update_facts, dict) and not block_facts:
        for key, raw in update_facts.items():
            if not isinstance(key, str):
                continue
            key = LEGACY_FACT_KEY_ALIASES.get(key, key)
            if key not in ALLOWED_FACT_KEYS:
                continue
            claim = _parse_claim(key, raw)
            if claim is None:
                continue
            items = _items_from_claim_value(claim["value"])
            if not items:
                continue
            if not _claim_items_supported(key, items, claim["intent"], gate_user_text):
                continue
            if not _has_explicit_preference_claim(
                key,
                gate_user_text,
                messages,
                intent=claim["intent"],
            ):
                continue
            result["update_facts"][key] = claim

    return result


class MemoryExtractor:
    """Ask Ollama what to remember from recent chat turns."""

    def __init__(self, client: OllamaClient, store: MemoryStore) -> None:
        self._client = client
        self._store = store

    def extract_from_turn(self, user_text: str, assistant_text: str) -> None:
        """Backward-compatible single-turn extraction."""
        messages = [
            {"role": "user", "content": user_text.strip()},
            {"role": "assistant", "content": assistant_text.strip()},
        ]
        self.extract_from_messages(messages)

    def extract_from_messages(self, messages: list[dict[str, str]]) -> None:
        """Run extraction over recent chat *messages* and apply validated updates."""
        window = [m for m in messages if m.get("content") and m.get("role") in {"user", "assistant"}]
        if len(window) > _EXTRACT_TURN_WINDOW:
            window = window[-_EXTRACT_TURN_WINDOW:]
        if not any(m.get("role") == "user" for m in window):
            return

        prompt = prompts.MEMORY_EXTRACT_PROMPT.format(
            chat_transcript=format_chat_transcript(window),
            known_facts=self._store.as_prompt_block() or "(none yet)",
        )
        try:
            raw = self._client.generate(
                prompt,
                system=prompts.MEMORY_EXTRACT_SYSTEM,
                max_tokens=_EXTRACT_MAX_TOKENS,
            )
        except OllamaUnavailableError:
            return

        payload = normalize_extraction(
            parse_extraction_response(raw),
            user_text=collect_user_text(window),
            messages=window,
            existing_notes=self._store.notes_list(),
        )
        if not any(payload[key] for key in ("add_notes", "remove_notes", "update_facts")):
            return
        self._store.apply_extraction(
            add_notes=payload["add_notes"],
            remove_notes=payload["remove_notes"],
            update_facts=payload["update_facts"],
            allowed_fact_keys=ALLOWED_FACT_KEYS,
        )
