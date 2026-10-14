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

# Pure chat-meta noise (media topics like "reading Dracula" are allowed once).
_EPHEMERAL_NOTE_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\btalking about\b",
        r"\bin (this|the) chat\b",
        r"\b(this|that) conversation\b",
    )
)

# Prefer replacing a near-duplicate only when the new text is clearly richer.
MIN_RICHER_NOTE_CHARS = 12

# Assistant / companion voice — not durable user facts from chat extraction.
_ASSISTANT_SPAM_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"^(you |you'?re |you are )\b",
        r"^(i'?m |i am |i leave |i do |i'?ve )\b",
        r"\byouthful energy\b",
        r"\bi'?m a bit\b",
        r"\bour little hangman\b",
        r"\byou often get creative\b",
        r"\brelax and enjoy\b",
        r"\bthe user is thinking\b",
        r"\bdon'?t you\??$",
    )
)

# Durable user info, preferences, plans, people (not companion self-talk).
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
        r"\b(speaks?|language|german|english)\b",
        r"\b(reading|rereading|watching|playing|listening to)\b",
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
        "but",
        "little",
        "again",
        "currently",
        "now",
    }
)
_MEDIA_ACTIVITY_WORDS = frozenset(
    {
        "reading",
        "rereading",
        "watching",
        "playing",
        "listening",
        "started",
        "starting",
        "considering",
        "thinking",
        "finds",
        "found",
        "finding",
        "boring",
        "classic",
        "classics",
        "books",
        "book",
        "movie",
        "show",
        "game",
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


def _stem_token(token: str) -> str:
    """Light English plural stem so night/nights and weekend/weekends match."""
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def _note_tokens(text: str) -> set[str]:
    return {
        _stem_token(token)
        for token in normalize_note_text(text).split()
        if token not in _COMPARE_STOP_WORDS
    }


def _content_tokens(text: str) -> set[str]:
    """Tokens minus stop words and generic media-activity words."""
    return {token for token in _note_tokens(text) if token not in _MEDIA_ACTIVITY_WORDS}


def _same_kinito_sentiment(left: str, right: str) -> bool:
    """Return True when both notes mainly express affection toward Kinito."""
    left_tokens = _note_tokens(left)
    right_tokens = _note_tokens(right)
    if "kinito" not in left_tokens and "kinito" not in right_tokens:
        return False
    return bool(left_tokens & _AFFECTION_WORDS) and bool(right_tokens & _AFFECTION_WORDS)


def _token_containment_duplicate(left_tokens: set[str], right_tokens: set[str]) -> bool:
    if not left_tokens or not right_tokens:
        return False
    smaller, larger = (
        (left_tokens, right_tokens)
        if len(left_tokens) <= len(right_tokens)
        else (right_tokens, left_tokens)
    )
    if len(smaller) < 2:
        return False
    return smaller <= larger


def _same_media_topic(left: str, right: str) -> bool:
    """Return True when both notes are media-activity chatter about the same title."""
    left_lower = left.casefold()
    right_lower = right.casefold()
    media_hit = any(
        word in left_lower and word in right_lower
        for word in ("read", "watch", "play", "listen", "boring", "considering")
    )
    if not media_hit:
        return False
    shared = _content_tokens(left) & _content_tokens(right)
    return any(len(token) >= 5 for token in shared)


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
    if _same_media_topic(left, right):
        return True

    left_tokens = _note_tokens(left)
    right_tokens = _note_tokens(right)
    if not left_tokens or not right_tokens:
        return False
    if _token_containment_duplicate(left_tokens, right_tokens):
        return True
    overlap = len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
    return overlap >= _NEAR_DUPLICATE_TOKEN_OVERLAP


def is_duplicate_of_existing_note(text: str, existing_notes: list[dict[str, str]]) -> bool:
    """Return True when *text* matches or closely repeats an existing note."""
    return find_near_duplicate_note_index(text, existing_notes) is not None


def find_near_duplicate_note_index(text: str, existing_notes: list[dict[str, str]]) -> int | None:
    """Return index of the first near-duplicate note, or None."""
    for index, note in enumerate(existing_notes):
        existing = note.get("text", "")
        if not isinstance(existing, str):
            continue
        if notes_are_near_duplicate(text, existing):
            return index
    return None


def is_meaningfully_richer_note(new_text: str, existing_text: str) -> bool:
    """Return True when *new_text* adds enough detail to replace *existing_text*."""
    return len(new_text.strip()) >= len(existing_text.strip()) + MIN_RICHER_NOTE_CHARS


def should_skip_note_against_existing(
    text: str,
    existing_notes: list[dict[str, str]],
) -> bool:
    """Return True when *text* should not be stored as a new/additional note."""
    index = find_near_duplicate_note_index(text, existing_notes)
    if index is None:
        return False
    existing = existing_notes[index].get("text", "")
    if not isinstance(existing, str):
        return True
    # Allow through so the store can upgrade a thinner note.
    return not is_meaningfully_richer_note(text, existing)


def is_assistant_spam_note(text: str) -> bool:
    """Return True when *text* looks like assistant chat, not a user memory."""
    trimmed = text.strip()
    if not trimmed:
        return False
    return any(pattern.search(trimmed) for pattern in _ASSISTANT_SPAM_PATTERNS)


def is_ephemeral_note(text: str) -> bool:
    """Return True for fleeting activity / chat-topic notes that should not persist."""
    trimmed = text.strip()
    if not trimmed:
        return False
    return any(pattern.search(trimmed) for pattern in _EPHEMERAL_NOTE_PATTERNS)


def is_storable_note(text: str, *, source: str = "chat") -> bool:
    """Return True if a note is worth persisting."""
    trimmed = text.strip()
    if not trimmed:
        return False

    if source == "question":
        return True

    if source == "editor":
        return len(trimmed) >= 1

    lower = trimmed.lower()
    for pattern in _REJECT_PATTERNS:
        if pattern.search(lower):
            return False

    if is_assistant_spam_note(trimmed):
        return False

    if is_ephemeral_note(trimmed):
        return False

    if len(trimmed) < _MIN_NOTE_LEN:
        return False

    return any(pattern.search(trimmed) for pattern in _MEMORY_HINTS)


def dedupe_note_entries(notes: list[dict[str, str]]) -> list[dict[str, str]]:
    """Keep the richest note from each near-duplicate cluster (stable order)."""
    kept: list[dict[str, str]] = []
    for note in notes:
        text = note.get("text", "")
        if not isinstance(text, str) or not text.strip():
            continue
        replaced = False
        for index, existing in enumerate(kept):
            existing_text = existing.get("text", "")
            if not isinstance(existing_text, str):
                continue
            if not notes_are_near_duplicate(text, existing_text):
                continue
            # Prefer the longer / more specific wording.
            if len(text.strip()) > len(existing_text.strip()):
                kept[index] = note
            replaced = True
            break
        if not replaced:
            kept.append(note)
    return kept
