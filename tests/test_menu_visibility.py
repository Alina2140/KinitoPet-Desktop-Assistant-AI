"""Tests for menu button visibility catalog."""

from content import dialogue as dlg
from content.menu_visibility import (
    ALWAYS_VISIBLE_LABELS,
    filter_visible_menu_buttons,
    menu_button_id_for_label,
)


def test_menu_button_id_for_known_labels():
    assert menu_button_id_for_label(dlg.BUTTON_CHAT) == "main.chat"
    assert menu_button_id_for_label(dlg.BUTTON_GIVE_HUG) == "actions.hug"
    assert menu_button_id_for_label(dlg.BUTTON_PAINT) == "actions.paint"
    assert menu_button_id_for_label(dlg.BUTTON_TTS_ON) == "settings.tts"
    assert menu_button_id_for_label(dlg.BUTTON_SPECIAL_DAYS_OFF) == "settings.special_days"


def test_filter_hides_optional_keeps_locked():
    buttons = [
        dlg.BUTTON_MODES,
        dlg.BUTTON_SETTINGS,
        dlg.BUTTON_CHAT,
        dlg.BUTTON_SAY_GOODBYE,
    ]
    visible = filter_visible_menu_buttons(
        buttons, {"main.chat", "main.modes", "main.settings"}
    )
    assert dlg.BUTTON_SETTINGS in visible  # locked via ALWAYS_VISIBLE
    assert dlg.BUTTON_CHAT not in visible
    assert dlg.BUTTON_MODES not in visible
    assert dlg.BUTTON_SAY_GOODBYE in visible


def test_always_visible_labels_include_recovery():
    assert dlg.BUTTON_BACK in ALWAYS_VISIBLE_LABELS
    assert dlg.BUTTON_MENU_BUTTONS in ALWAYS_VISIBLE_LABELS
    assert dlg.BUTTON_WAKE_UP in ALWAYS_VISIBLE_LABELS
