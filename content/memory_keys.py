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
    dlg.JOB_QUESTION: "job",
    dlg.FAVORITE_GAME_QUESTION: "favorite_game",
    dlg.BEDTIME_QUESTION: "bedtime",
    dlg.SHOW_QUESTION: "favorite_show",
    dlg.ARTIST_QUESTION: "favorite_artist",
    dlg.ANIMAL_QUESTION: "favorite_animal",
    dlg.COMFORT_FOOD_QUESTION: "comfort_food",
    dlg.DREAM_DESTINATION_QUESTION: "dream_destination",
    dlg.FAVORITE_APP_QUESTION: "favorite_app",
    dlg.MORNING_DRINK_QUESTION: "morning_drink",
    dlg.WAKE_TIME_QUESTION: "wake_time",
    dlg.CITY_QUESTION: "home_city",
    dlg.CHRONOTYPE_QUESTION: "chronotype",
    dlg.LANGUAGES_QUESTION: "languages",
    dlg.RAIN_QUESTION: "likes_rain",
    dlg.HORROR_QUESTION: "likes_horror",
    dlg.SPICY_QUESTION: "likes_spicy_food",
    dlg.LATE_NIGHT_QUESTION: "likes_staying_up_late",
    dlg.PARTNER_QUESTION: "partner_status",
    dlg.SIBLINGS_QUESTION: "siblings",
    dlg.BEST_FRIEND_QUESTION: "important_person",
    dlg.PRONOUNS_QUESTION: "pronouns",
}

# Facts that must not be overwritten by follow-up questions or chat extraction.
PROTECTED_FACT_KEYS: frozenset[str] = frozenset({"user_names", "first_met"})

# Facts that may hold multiple values (stored as str or list[str]).
MULTI_VALUE_FACT_KEYS: frozenset[str] = frozenset(
    {
        "user_names",
        "hobbies",
        "pets",
        "favorite_colors",
        "favorite_seasons",
        "favorite_snacks",
        "languages",
        "favorite_animal",
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
# Daily check-ins refresh often and are not ask-once.
EXTRA_FACT_KEYS: frozenset[str] = frozenset(
    {
        "birthday",
        "first_met",
        "mood_today",
        "energy_today",
        "focus_today",
        "plans_tonight",
    }
)

ALLOWED_FACT_KEYS: frozenset[str] = frozenset(MARKER_TO_FACT_KEY.values()) | EXTRA_FACT_KEYS

# Cooldown topic for occasional "we've known each other…" idle mentions.
FRIENDSHIP_DURATION_TOPIC = "friendship_duration"
FRIENDSHIP_DURATION_COOLDOWN_DAYS = 7

# Daily check-ins: (topic_id, cooldown_days, question marker substring).
DAILY_CHECKIN_COOLDOWNS: tuple[tuple[str, int, str], ...] = (
    ("mood_today", 1, dlg.DAY_QUESTION),
    ("energy_today", 1, dlg.ENERGY_QUESTION),
    ("focus_today", 1, dlg.FOCUS_QUESTION),
    ("plans_tonight", 1, dlg.PLANS_TONIGHT_QUESTION),
)

MOOD_TODAY_TOPIC = "mood_today"
MOOD_TODAY_COOLDOWN_DAYS = 1


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
