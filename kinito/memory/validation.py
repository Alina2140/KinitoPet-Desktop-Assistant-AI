"""Heuristics for filtering low-value memory notes."""

from __future__ import annotations

import re

# Visual fluff, meta replies, or throwaway chat — not durable memories.
_REJECT_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\b(smily|smiley|emoji|emoticon|emote)\b",
        r"\b(hand next to|next to (?:its|his|her) mouth)\b",
        r"\b(facial expression|body language|gesture|pose|sprite|avatar)\b",
        r"\b(describ(es|ing|ed)|depict(s|ing|ed)|shows?|showing)\b.*\b(face|look|expression|mouth|hand|emoji|smiley)\b",
        r"^(no change needed|nothing to store|none|n/?a)\.?$",
        r"^[\W\d_]+$",
        r"^(thanks|thank you|thx|ok|okay|sure|yes|no|hi|hello|hey|cool|nice|great)\.?$",
        r"\buser (just )?said (hi|hello|hey|thanks)\b",
        r"\b(had a|having a) (good|great|nice|lovely|fine) (day|morning|evening)\b",
        r"\b(the weather is|nice weather|beautiful day)\b",
    )
)

# Durable user info, preferences, plans, people, or companion-relationship observations.
_MEMORY_HINTS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\b(user|i am|i'm|i like|i love|i enjoy|i work|i study|i live|my )\b",
        r"\b(works?|working as|studies|student|employed)\b",
        r"\b(likes?|loves?|enjoys?|prefers?|dislikes?|favorite|wants? to)\b",
        r"\b(plan|plans|friend|family|partner|pet|job|hobby|weekend|birthday)\b",
        r"\b(with [A-Z][a-z]+|named [A-Z])",
        r"\b(movie night|game night|appointment|meeting|trip|vacation)\b",
        r"^[a-z_]+:\s+\S",
        r"\b(has a|have a|owns a|got a)\b",
        r"\b(hiking|often|usually|every|tends? to|seems to)\b",
        r"\b(noticed (that )?user|observed (that )?user|user (often|usually|mentioned))\b",
        r"\b(speaks?|language|german|english|deutsch)\b",
        r"\b(kinito|assistant|enthusiastic|comfortable discussing|open about)\b",
    )
)

_MIN_NOTE_LEN = 10
_NEAR_DUPLICATE_TOKEN_OVERLAP = 0.65
_COMPARE_STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "to",
        "for",
        "with",
        "on",
        "in",
        "of",
        "and",
        "or",
        "user",
        "she",
        "he",
        "they",
        "her",
        "his",
        "their",
    }
)
_AFFECTION_WORDS = frozenset(
    {
        "love",
        "loves",
        "liked",
        "likes",
        "affection",
        "enthusiasm",
        "enthusiastic",
        "appreciates",
        "appreciate",
        "admires",
        "admire",
    }
)


def normalize_note_text(text: str) -> str:
    """Lowercase and strip punctuation for duplicate comparison."""
    lowered = text.lower()
    cleaned = re.sub(r"[^\w\s]", " ", lowered)
    return " ".join(cleaned.split())


def _note_tokens(text: str) -> set[str]:
    return {token for token in normalize_note_text(text).split() if token not in _COMPARE_STOP_WORDS}


def _same_kinito_sentiment(left: str, right: str) -> bool:
    """Return True when both notes mainly express affection toward Kinito."""
    left_tokens = _note_tokens(left)
    right_tokens = _note_tokens(right)
    if "kinito" not in left_tokens and "kinito" not in right_tokens:
        return False
    return bool(left_tokens & _AFFECTION_WORDS) and bool(right_tokens & _AFFECTION_WORDS)


def notes_are_near_duplicate(left: str, right: str) -> bool:
    """Return True when two notes say essentially the same thing."""
    normalized_left = normalize_note_text(left)
    normalized_right = normalize_note_text(right)
    if not normalized_left or not normalized_right:
        return False
    if normalized_left == normalized_right:
        return True
    if _same_kinito_sentiment(left, right):
        return True

    left_tokens = _note_tokens(left)
    right_tokens = _note_tokens(right)
    if not left_tokens or not right_tokens:
        return False
    overlap = len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
    return overlap >= _NEAR_DUPLICATE_TOKEN_OVERLAP


def is_duplicate_of_existing_note(text: str, existing_notes: list[dict[str, str]]) -> bool:
    """Return True when *text* matches or closely repeats an existing note."""
    for note in existing_notes:
        existing = note.get("text", "")
        if not isinstance(existing, str):
            continue
        if notes_are_near_duplicate(text, existing):
            return True
    return False


def is_storable_note(text: str, *, source: str = "chat") -> bool:
    """Return True if a note is worth persisting."""
    trimmed = text.strip()
    if not trimmed:
        return False

    if source == "question":
        return True

    lower = trimmed.lower()
    for pattern in _REJECT_PATTERNS:
        if pattern.search(lower):
            return False

    if len(trimmed) < _MIN_NOTE_LEN:
        return False

    return any(pattern.search(trimmed) for pattern in _MEMORY_HINTS)
