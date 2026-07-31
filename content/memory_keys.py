"""Mapping from dialog markers to persistent memory fact keys."""

from __future__ import annotations

from content import dialogue as dlg

# Marker substring -> fact key for personal questions (ask once).
MARKER_TO_FACT_KEY: dict[str, str] = {
    dlg.NAME_QUESTION: "user_names",
    dlg.COLOR_QUESTION: "favorite_colors",
    dlg.FOOD_QUESTION: "favorite_food",
    dlg.HOBBY_QUESTION: "hobbies",
    dlg.PET_QUESTION: "pets",
    dlg.BOOK_QUESTION: "favorite_book",
    dlg.DRINK_QUESTION: "favorite_drink",
    dlg.MOVIE_QUESTION: "favorite_movie",
    dlg.SNACK_QUESTION: "favorite_snacks",
    dlg.SEASON_QUESTION: "favorite_seasons",
    dlg.PROGRAMMING_QUESTION: "likes_programming",
    dlg.MUSIC_QUESTION: "likes_music",
    dlg.COFFEE_QUESTION: "likes_coffee",
}

# Facts that must not be overwritten by follow-up questions or chat extraction.
PROTECTED_FACT_KEYS: frozenset[str] = frozenset({"user_names"})

# Facts that may hold multiple values (stored as str or list[str]).
MULTI_VALUE_FACT_KEYS: frozenset[str] = frozenset(
    {
        "user_names",
        "hobbies",
        "pets",
        "favorite_colors",
        "favorite_seasons",
        "favorite_snacks",
    }
)

# Legacy singular keys -> current keys (migrated on load).
LEGACY_FACT_KEY_ALIASES: dict[str, str] = {
    "user_name": "user_names",
    "hobby": "hobbies",
    "pet": "pets",
    "favorite_color": "favorite_colors",
    "favorite_season": "favorite_seasons",
    "favorite_snack": "favorite_snacks",
}

ASK_ONCE_MARKERS: frozenset[str] = frozenset(MARKER_TO_FACT_KEY) | frozenset(
    {dlg.BIRTHDAY_CONSENT_QUESTION}
)

# Extra structured facts not tied to a simple ask-once marker mapping.
EXTRA_FACT_KEYS: frozenset[str] = frozenset({"birthday"})

ALLOWED_FACT_KEYS: frozenset[str] = frozenset(MARKER_TO_FACT_KEY.values()) | EXTRA_FACT_KEYS


def fact_key_for_marker(marker: str) -> str | None:
    """Return the memory fact key for a dialog marker, if any."""
    return MARKER_TO_FACT_KEY.get(marker)


def marker_for_question_text(question_text: str) -> str | None:
    """Return the first ask-once marker found in *question_text*."""
    lower = question_text.lower()
    for marker in MARKER_TO_FACT_KEY:
        if marker.lower() in lower:
            return marker
    return None
