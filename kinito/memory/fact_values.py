"""Split and format multi-value memory facts (hobbies, pets, …)."""

from __future__ import annotations

import re

MAX_FACT_VALUES = 8
MAX_FACT_ITEM_LEN = 40

_COMMA_SPLIT_RE = re.compile(r"[,;]")
_AND_SPLIT_RE = re.compile(r"\s+(?:and|&|\+)\s+", re.IGNORECASE)
_LEADING_AND_RE = re.compile(r"^(?:and|&)\s+", re.IGNORECASE)


def split_fact_values(text: str, *, max_items: int = MAX_FACT_VALUES) -> list[str]:
    """Split a free-text answer into distinct fact values.

    Prefers comma/semicolon lists; otherwise splits on "and" / "&" / "+".
    """
    trimmed = text.strip()
    if not trimmed:
        return []

    if "," in trimmed or ";" in trimmed:
        raw_parts = _COMMA_SPLIT_RE.split(trimmed)
    else:
        raw_parts = _AND_SPLIT_RE.split(trimmed)

    values: list[str] = []
    seen: set[str] = set()
    for part in raw_parts:
        cleaned = _LEADING_AND_RE.sub("", part.strip()).strip()
        cleaned = cleaned[:MAX_FACT_ITEM_LEN].strip()
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        values.append(cleaned)
        if len(values) >= max_items:
            break
    return values


def normalize_fact_value_list(
    raw: str | list | tuple,
    *,
    max_items: int = MAX_FACT_VALUES,
) -> list[str]:
    """Normalize a string or list from JSON/extraction into trimmed values."""
    if isinstance(raw, str):
        return split_fact_values(raw, max_items=max_items)
    if not isinstance(raw, (list, tuple)):
        return []

    values: list[str] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, str):
            continue
        for part in split_fact_values(item, max_items=max_items):
            key = part.casefold()
            if key in seen:
                continue
            seen.add(key)
            values.append(part)
            if len(values) >= max_items:
                return values
    return values


def format_fact_values(values: list[str]) -> str:
    """Join values for display and template formatting."""
    cleaned = [value.strip() for value in values if isinstance(value, str) and value.strip()]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    if len(cleaned) == 2:
        return f"{cleaned[0]} and {cleaned[1]}"
    return f"{', '.join(cleaned[:-1])}, and {cleaned[-1]}"


def compact_fact_storage(values: list[str]) -> str | list[str] | None:
    """Store one value as a string; two or more as a list."""
    cleaned = [value.strip() for value in values if isinstance(value, str) and value.strip()]
    if not cleaned:
        return None
    if len(cleaned) == 1:
        return cleaned[0]
    return cleaned


# Answers that usually mean "decline / no update" rather than a real fact value.
_PLACEHOLDER_FACT_ANSWERS = frozenset(
    {
        "no",
        "yes",
        "n",
        "y",
        "none",
        "nothing",
        "n/a",
        "na",
        "idk",
        "dunno",
        "nope",
        "nah",
        "skip",
        "pass",
        "-",
        ".",
        "?",
        "private",
    }
)

# Fact keys where "yes"/"no" (or similar) is a meaningful stored value.
_FACT_KEYS_ALLOWING_PLACEHOLDERS = frozenset(
    {
        "likes_programming",
        "likes_music",
        "likes_coffee",
        "likes_rain",
        "likes_horror",
        "likes_spicy_food",
        "likes_staying_up_late",
        "plans_tonight",
        "partner_status",
        "birthday",
    }
)


def is_placeholder_fact_answer(text: str) -> bool:
    """Return True for short decline-style answers that should not overwrite facts."""
    return text.strip().casefold() in _PLACEHOLDER_FACT_ANSWERS


def should_reject_fact_value(key: str, value: str) -> bool:
    """Return True when *value* must not be written to *key*."""
    if key.startswith("likes_") or key in _FACT_KEYS_ALLOWING_PLACEHOLDERS:
        return False
    return is_placeholder_fact_answer(value)
