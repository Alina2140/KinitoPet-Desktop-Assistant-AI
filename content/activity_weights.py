"""Catalog of tunable spontaneous activities and their chance weights.

Each activity has a weight from 0 to 100 (percent of its built-in chance).
A weight of 0 disables the activity entirely; 100 keeps the default chance.
"""

from __future__ import annotations

# (activity id, display label)
ActivityEntry = tuple[str, str]

ACTIVITY_SECTIONS: tuple[tuple[str, tuple[ActivityEntry, ...]], ...] = (
    (
        "Idle performances",
        (
            ("idle_reading", "Reading a book"),
            ("idle_fancy", "Magic show"),
        ),
    ),
    (
        "Spontaneous speech",
        (
            ("random_speech", "Random questions & lines"),
            ("memory_question", "Questions about things you told Kinito"),
        ),
    ),
    (
        "Spontaneous actions",
        (
            ("datetime", "Tell the time"),
            ("poem", "Recite a poem"),
            ("fact", "Fun fact"),
            ("browser", "Offer a website"),
            ("music", "Offer music"),
            ("games", "Offer a game"),
            ("chat_invite", "Invite to chat"),
            ("hug_ask", "Ask for a hug"),
            ("compliment", "Ask about compliments"),
            ("nap", "Take a nap"),
            ("special_day", "Special-day comments"),
            ("countdown", "Special-day countdown"),
            ("birthday", "Birthday wishes"),
            ("anniversary", "Friendship anniversary"),
            ("missed_day", "Ask about missed special days"),
            ("friendship", "Friendship duration mentions"),
        ),
    ),
    (
        "Random events",
        (
            ("screen_glitch", "Screen glitch"),
            ("blue_screen", "Blue screen"),
            ("terminal", "Terminal window"),
            ("random_ad", "Ad popups"),
            ("ambient_reminder", "Reminders & nudges"),
            ("kinito_note", "Kinito writes a note"),
            ("screen_comment", "Screen comments"),
            ("paint_recall", "Painting popups"),
            ("paint_request", "Paint requests"),
            ("sticky_notes_recall", "Sticky note popups"),
            ("window_grab", "Window play"),
        ),
    ),
)

ACTIVITY_IDS: frozenset[str] = frozenset(
    entry_id for _section, entries in ACTIVITY_SECTIONS for entry_id, _label in entries
)

# Activity ids gated behind an existing Turn on/off setting. When the app flag
# is False the activity slider is greyed out in the settings window.
ACTIVITY_TOGGLE_ATTRS: dict[str, str] = {
    "screen_glitch": "_screen_effects_enabled",
    "blue_screen": "_screen_effects_enabled",
    "random_ad": "_ads_enabled",
    "terminal": "_terminal_enabled",
    "ambient_reminder": "_ambient_reminders_enabled",
    "kinito_note": "_kinito_notes_enabled",
    "screen_comment": "_screen_comments_enabled",
    "paint_recall": "_paint_recall_enabled",
    "paint_request": "_paint_requests_enabled",
    "sticky_notes_recall": "_sticky_notes_recall_enabled",
    "window_grab": "_window_grab_enabled",
}

ACTIVITY_WEIGHT_MIN = 0
ACTIVITY_WEIGHT_MAX = 100
ACTIVITY_WEIGHT_DEFAULT = 100


def clamp_activity_weight(value: object) -> int:
    """Clamp an activity weight to the supported 0–100 range."""
    try:
        weight = int(round(float(value)))
    except (TypeError, ValueError):
        return ACTIVITY_WEIGHT_DEFAULT
    return max(ACTIVITY_WEIGHT_MIN, min(ACTIVITY_WEIGHT_MAX, weight))


def normalize_activity_weights(raw: object) -> dict[str, int]:
    """Keep only known activity ids with clamped 0–100 weights."""
    if not isinstance(raw, dict):
        return {}
    cleaned: dict[str, int] = {}
    for key, value in raw.items():
        activity_id = str(key)
        if activity_id not in ACTIVITY_IDS:
            continue
        cleaned[activity_id] = clamp_activity_weight(value)
    return cleaned
