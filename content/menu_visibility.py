"""Catalog and helpers for which menu buttons are visible."""

from __future__ import annotations

from content import dialogue as dlg

# Runtime labels that must always remain clickable for recovery/navigation.
ALWAYS_VISIBLE_LABELS = frozenset(
    {
        dlg.BUTTON_BACK,
        dlg.BUTTON_SETTINGS,
        dlg.BUTTON_MENU_BUTTONS,
        dlg.BUTTON_WAKE_UP,
        dlg.BUTTON_UNFOCUS,
    }
)

# Stable ids that cannot be unchecked in the visibility editor.
LOCKED_MENU_BUTTON_IDS = frozenset(
    {
        "main.settings",
        "settings.menu_buttons",
        "settings.back",
        "modes.back",
        "actions.back",
        "modes.wake",
        "modes.unfocus",
    }
)


# (id, display label, frozenset of runtime button labels that this entry controls)
MenuEntry = tuple[str, str, frozenset[str]]

MENU_VISIBILITY_SECTIONS: tuple[tuple[str, tuple[MenuEntry, ...]], ...] = (
    (
        "Main",
        (
            ("main.modes", "Modes", frozenset({dlg.BUTTON_MODES})),
            ("main.settings", "Settings", frozenset({dlg.BUTTON_SETTINGS})),
            ("main.actions", "Actions", frozenset({dlg.BUTTON_ACTIONS})),
            ("main.chat", "Chat", frozenset({dlg.BUTTON_CHAT})),
            ("main.goodbye", "Goodbye", frozenset({dlg.BUTTON_SAY_GOODBYE})),
        ),
    ),
    (
        "Modes",
        (
            ("modes.sleep", "Sleep", frozenset({dlg.BUTTON_SLEEP})),
            ("modes.wake", "Wake up", frozenset({dlg.BUTTON_WAKE_UP})),
            ("modes.focus", "Focus", frozenset({dlg.BUTTON_FOCUS})),
            ("modes.unfocus", "Unfocus", frozenset({dlg.BUTTON_UNFOCUS})),
            (
                "modes.focus_timer",
                "Focus Timer",
                frozenset({dlg.BUTTON_SET_FOCUS_TIMER}),
            ),
            ("modes.back", "Back", frozenset({dlg.BUTTON_BACK})),
        ),
    ),
    (
        "Settings",
        (
            (
                "settings.screen_effects",
                "Screen Effects",
                frozenset(
                    {
                        dlg.BUTTON_SCREEN_EFFECTS,
                        dlg.BUTTON_SCREEN_EFFECTS_ON,
                        dlg.BUTTON_SCREEN_EFFECTS_OFF,
                    }
                ),
            ),
            (
                "settings.reminders",
                "Reminders",
                frozenset(
                    {
                        dlg.BUTTON_REMINDERS,
                        dlg.BUTTON_REMINDERS_ON,
                        dlg.BUTTON_REMINDERS_OFF,
                    }
                ),
            ),
            (
                "settings.app_awareness",
                "App Awareness",
                frozenset(
                    {
                        dlg.BUTTON_APP_AWARENESS,
                        dlg.BUTTON_APP_AWARENESS_ON,
                        dlg.BUTTON_APP_AWARENESS_OFF,
                    }
                ),
            ),
            (
                "settings.screen_comments",
                "Screen Comments",
                frozenset(
                    {
                        dlg.BUTTON_SCREEN_COMMENTS,
                        dlg.BUTTON_SCREEN_COMMENTS_ON,
                        dlg.BUTTON_SCREEN_COMMENTS_OFF,
                    }
                ),
            ),
            (
                "settings.paint_recall",
                "Painting Popups",
                frozenset(
                    {
                        dlg.BUTTON_PAINT_RECALL,
                        dlg.BUTTON_PAINT_RECALL_ON,
                        dlg.BUTTON_PAINT_RECALL_OFF,
                    }
                ),
            ),
            (
                "settings.snoring",
                "Snoring",
                frozenset(
                    {dlg.BUTTON_SNORING, dlg.BUTTON_SNORING_ON, dlg.BUTTON_SNORING_OFF}
                ),
            ),
            (
                "settings.window_play",
                "Window Play",
                frozenset(
                    {
                        dlg.BUTTON_WINDOW_PLAY,
                        dlg.BUTTON_WINDOW_PLAY_ON,
                        dlg.BUTTON_WINDOW_PLAY_OFF,
                    }
                ),
            ),
            (
                "settings.tts",
                "Speech (TTS)",
                frozenset({dlg.BUTTON_TTS, dlg.BUTTON_TTS_ON, dlg.BUTTON_TTS_OFF}),
            ),
            (
                "settings.emojis",
                "Emojis",
                frozenset({dlg.BUTTON_EMOJI, dlg.BUTTON_EMOJI_ON, dlg.BUTTON_EMOJI_OFF}),
            ),
            (
                "settings.special_days",
                "Special Days",
                frozenset(
                    {
                        dlg.BUTTON_SPECIAL_DAYS,
                        dlg.BUTTON_SPECIAL_DAYS_ON,
                        dlg.BUTTON_SPECIAL_DAYS_OFF,
                    }
                ),
            ),
            (
                "settings.menu_buttons",
                "Menu Buttons",
                frozenset({dlg.BUTTON_MENU_BUTTONS}),
            ),
            ("settings.memories", "Memories", frozenset({dlg.BUTTON_REMEMBER})),
            ("settings.forget", "Forget", frozenset({dlg.BUTTON_FORGET})),
            ("settings.credits", "Credits", frozenset({dlg.BUTTON_SHOW_CREDITS})),
            ("settings.back", "Back", frozenset({dlg.BUTTON_BACK})),
        ),
    ),
    (
        "Actions",
        (
            (
                "actions.reminder",
                "Set Reminder",
                frozenset({dlg.BUTTON_SET_REMINDER}),
            ),
            ("actions.time", "Tell Time", frozenset({dlg.BUTTON_TELL_TIME})),
            ("actions.sing", "Sing", frozenset({dlg.BUTTON_SING_SONG})),
            ("actions.fact", "Fun Fact", frozenset({dlg.BUTTON_FUN_FACT})),
            (
                "actions.website",
                "Visit Website",
                frozenset({dlg.BUTTON_VISIT_WEBSITE}),
            ),
            ("actions.music", "Play Music", frozenset({dlg.BUTTON_PLAY_MUSIC})),
            ("actions.game", "Play Game", frozenset({dlg.BUTTON_PLAY_GAME})),
            ("actions.paint", "Paint", frozenset({dlg.BUTTON_PAINT})),
            ("actions.hug", "Hug", frozenset({dlg.BUTTON_GIVE_HUG})),
            ("actions.back", "Back", frozenset({dlg.BUTTON_BACK})),
        ),
    ),
)


def _label_to_id_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for _section, entries in MENU_VISIBILITY_SECTIONS:
        for entry_id, _label, aliases in entries:
            for alias in aliases:
                # First claim wins so Main/Modes-specific wake entries stay distinct
                # where labels don't overlap; overlapping labels like Back share an id
                # intentionally via settings.back / modes.back last-write — prefer first.
                mapping.setdefault(alias, entry_id)
    return mapping


_LABEL_TO_ID = _label_to_id_map()


def menu_button_id_for_label(label: str) -> str | None:
    """Return the stable visibility id for a runtime button label, if known."""
    return _LABEL_TO_ID.get(label)


def filter_visible_menu_buttons(buttons: list[str], hidden_ids: set[str]) -> list[str]:
    """Drop buttons whose visibility id is hidden (locked labels always stay)."""
    visible: list[str] = []
    for label in buttons:
        if label in ALWAYS_VISIBLE_LABELS:
            visible.append(label)
            continue
        button_id = menu_button_id_for_label(label)
        if button_id is None:
            visible.append(label)
            continue
        if button_id in LOCKED_MENU_BUTTON_IDS:
            visible.append(label)
            continue
        if button_id in hidden_ids:
            continue
        visible.append(label)
    return visible


def all_menu_button_ids() -> frozenset[str]:
    """Return every catalogued menu button id."""
    ids: set[str] = set()
    for _section, entries in MENU_VISIBILITY_SECTIONS:
        for entry_id, _label, _aliases in entries:
            ids.add(entry_id)
    return frozenset(ids)
