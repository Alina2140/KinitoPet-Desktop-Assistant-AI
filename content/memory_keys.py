"""Mapping from dialog markers to persistent memory fact keys."""

from __future__ import annotations

from content import dialogue as dlg

# Marker substring -> fact key for personal questions (ask once).
MARKER_TO_FACT_KEY: dict[str, str] = {
    dlg.NAME_QUESTION: "user_name",
    dlg.COLOR_QUESTION: "favorite_color",
    dlg.FOOD_QUESTION: "favorite_food",
    dlg.HOBBY_QUESTION: "hobby",
    dlg.PET_QUESTION: "pet",
    dlg.BOOK_QUESTION: "favorite_book",
    dlg.DRINK_QUESTION: "favorite_drink",
    dlg.MOVIE_QUESTION: "favorite_movie",
    dlg.SNACK_QUESTION: "favorite_snack",
    dlg.SEASON_QUESTION: "favorite_season",
    dlg.PROGRAMMING_QUESTION: "likes_programming",
    dlg.MUSIC_QUESTION: "likes_music",
    dlg.COFFEE_QUESTION: "likes_coffee",
}

# Facts that must not be overwritten by follow-up questions or chat extraction.
PROTECTED_FACT_KEYS: frozenset[str] = frozenset({"user_name"})

ASK_ONCE_MARKERS: frozenset[str] = frozenset(MARKER_TO_FACT_KEY)

ALLOWED_FACT_KEYS: frozenset[str] = frozenset(MARKER_TO_FACT_KEY.values())


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
