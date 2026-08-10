"""Every spontaneous question must resolve to a dialog spec."""

import pytest

from content import dialogue as dlg
from content.dialog_registry import DIALOG_SPECS, find_dialog_spec, menu_options_for
from content.questions import QUESTIONS


@pytest.mark.parametrize("question", QUESTIONS)
def test_every_question_matches_a_dialog_spec(question):
    spec = find_dialog_spec(question)
    assert spec is not None, f"No dialog spec for: {question!r}"


@pytest.mark.parametrize("question", QUESTIONS)
def test_question_dialog_spec_has_valid_ui(question):
    spec = find_dialog_spec(question)
    assert spec.ui.kind in ("buttons", "textbox")
    if spec.ui.kind == "buttons":
        assert len(spec.ui.buttons) >= 2
    if spec.ui.kind == "textbox":
        assert spec.ui.textbox_prompt or spec.marker


@pytest.mark.parametrize("spec", DIALOG_SPECS)
def test_dialog_spec_marker_is_findable(spec):
    assert find_dialog_spec(spec.marker) is spec


@pytest.mark.parametrize("question", dlg.STORY_QUESTIONS)
def test_story_questions_contain_marker(question):
    assert dlg.STORY_QUESTION_MARKER.lower() in question.lower()


def _menu_app(**kwargs):
    from unittest.mock import MagicMock

    app = MagicMock()
    app.paused = kwargs.get("paused", False)
    app._focus_mode = kwargs.get("focus_mode", False)
    app._screen_effects_enabled = kwargs.get("screen_effects_enabled", True)
    app._ambient_reminders_enabled = kwargs.get("ambient_reminders_enabled", True)
    app._app_awareness_enabled = kwargs.get("app_awareness_enabled", True)
    app._screen_comments_enabled = kwargs.get("screen_comments_enabled", True)
    app._paint_recall_enabled = kwargs.get("paint_recall_enabled", True)
    app._snoring_enabled = kwargs.get("snoring_enabled", True)
    app._window_grab_enabled = kwargs.get("window_grab_enabled", True)
    app._tts_enabled = kwargs.get("tts_enabled", True)
    app._special_days_enabled = kwargs.get("special_days_enabled", True)
    app._emoji_picker_enabled = kwargs.get("emoji_picker_enabled", True)
    app._hidden_menu_buttons = kwargs.get("hidden_menu_buttons", set())
    return app


def test_menu_options_default_toggle_labels():
    opts = menu_options_for(_menu_app())
    assert opts == [
        dlg.BUTTON_MODES,
        dlg.BUTTON_SETTINGS,
        dlg.BUTTON_ACTIONS,
        dlg.BUTTON_MOOD,
        dlg.BUTTON_CHAT,
        dlg.BUTTON_SAY_GOODBYE,
    ]


def test_menu_options_reflect_active_states():
    opts = menu_options_for(_menu_app(paused=True, screen_effects_enabled=False))
    assert opts == [dlg.BUTTON_WAKE_UP, dlg.BUTTON_SAY_GOODBYE]


def test_menu_options_hide_blocked_actions_when_sleeping():
    opts = menu_options_for(_menu_app(paused=True))
    assert opts == [dlg.BUTTON_WAKE_UP, dlg.BUTTON_SAY_GOODBYE]
    assert dlg.BUTTON_MODES not in opts
    assert dlg.BUTTON_SETTINGS not in opts
    assert dlg.BUTTON_ACTIONS not in opts
    assert dlg.BUTTON_CHAT not in opts


def test_menu_options_show_wake_up_and_unfocus_when_sleeping_in_focus_mode():
    opts = menu_options_for(_menu_app(paused=True, focus_mode=True))
    assert opts == [dlg.BUTTON_WAKE_UP, dlg.BUTTON_UNFOCUS, dlg.BUTTON_SAY_GOODBYE]


def test_menu_options_hide_blocked_actions_in_focus_mode():
    opts = menu_options_for(_menu_app(focus_mode=True))
    assert opts == [
        dlg.BUTTON_UNFOCUS,
        dlg.BUTTON_SET_FOCUS_TIMER,
        dlg.BUTTON_SAY_GOODBYE,
    ]
    assert dlg.BUTTON_MODES not in opts
    assert dlg.BUTTON_SETTINGS not in opts
    assert dlg.BUTTON_ACTIONS not in opts
    assert dlg.BUTTON_CHAT not in opts


def test_menu_options_include_all_top_level_actions():
    opts = menu_options_for(_menu_app())
    expected = {
        dlg.BUTTON_MODES,
        dlg.BUTTON_SETTINGS,
        dlg.BUTTON_ACTIONS,
        dlg.BUTTON_MOOD,
        dlg.BUTTON_CHAT,
        dlg.BUTTON_SAY_GOODBYE,
    }
    assert set(opts) == expected
    assert len(opts) == 6


def test_modes_options_default_and_focus_timer():
    from content.dialog_registry import modes_options_for

    assert modes_options_for(_menu_app()) == [
        dlg.BUTTON_SLEEP,
        dlg.BUTTON_FOCUS,
        dlg.BUTTON_BACK,
    ]
    assert modes_options_for(_menu_app(focus_mode=True)) == [
        dlg.BUTTON_UNFOCUS,
        dlg.BUTTON_SET_FOCUS_TIMER,
        dlg.BUTTON_BACK,
    ]
    assert modes_options_for(_menu_app(paused=True)) == [
        dlg.BUTTON_WAKE_UP,
        dlg.BUTTON_BACK,
    ]
    assert modes_options_for(_menu_app(paused=True, focus_mode=True)) == [
        dlg.BUTTON_WAKE_UP,
        dlg.BUTTON_UNFOCUS,
        dlg.BUTTON_BACK,
    ]


def test_settings_and_actions_options():
    from content.dialog_registry import actions_options_for, settings_options_for

    assert settings_options_for(_menu_app()) == [
        dlg.BUTTON_SCREEN_EFFECTS_ON,
        dlg.BUTTON_REMINDERS_ON,
        dlg.BUTTON_APP_AWARENESS_ON,
        dlg.BUTTON_SCREEN_COMMENTS_ON,
        dlg.BUTTON_PAINT_RECALL_ON,
        dlg.BUTTON_SNORING_ON,
        dlg.BUTTON_WINDOW_PLAY_ON,
        dlg.BUTTON_TTS_ON,
        dlg.BUTTON_EMOJI_ON,
        dlg.BUTTON_SPECIAL_DAYS_ON,
        dlg.BUTTON_MENU_BUTTONS,
        dlg.BUTTON_REMEMBER,
        dlg.BUTTON_FORGET,
        dlg.BUTTON_SHOW_CREDITS,
        dlg.BUTTON_BACK,
    ]
    assert settings_options_for(_menu_app(ambient_reminders_enabled=False)) == [
        dlg.BUTTON_SCREEN_EFFECTS_ON,
        dlg.BUTTON_REMINDERS_OFF,
        dlg.BUTTON_APP_AWARENESS_ON,
        dlg.BUTTON_SCREEN_COMMENTS_ON,
        dlg.BUTTON_PAINT_RECALL_ON,
        dlg.BUTTON_SNORING_ON,
        dlg.BUTTON_WINDOW_PLAY_ON,
        dlg.BUTTON_TTS_ON,
        dlg.BUTTON_EMOJI_ON,
        dlg.BUTTON_SPECIAL_DAYS_ON,
        dlg.BUTTON_MENU_BUTTONS,
        dlg.BUTTON_REMEMBER,
        dlg.BUTTON_FORGET,
        dlg.BUTTON_SHOW_CREDITS,
        dlg.BUTTON_BACK,
    ]
    assert settings_options_for(_menu_app(app_awareness_enabled=False)) == [
        dlg.BUTTON_SCREEN_EFFECTS_ON,
        dlg.BUTTON_REMINDERS_ON,
        dlg.BUTTON_APP_AWARENESS_OFF,
        dlg.BUTTON_SCREEN_COMMENTS_ON,
        dlg.BUTTON_PAINT_RECALL_ON,
        dlg.BUTTON_SNORING_ON,
        dlg.BUTTON_WINDOW_PLAY_ON,
        dlg.BUTTON_TTS_ON,
        dlg.BUTTON_EMOJI_ON,
        dlg.BUTTON_SPECIAL_DAYS_ON,
        dlg.BUTTON_MENU_BUTTONS,
        dlg.BUTTON_REMEMBER,
        dlg.BUTTON_FORGET,
        dlg.BUTTON_SHOW_CREDITS,
        dlg.BUTTON_BACK,
    ]
    assert settings_options_for(_menu_app(screen_comments_enabled=False)) == [
        dlg.BUTTON_SCREEN_EFFECTS_ON,
        dlg.BUTTON_REMINDERS_ON,
        dlg.BUTTON_APP_AWARENESS_ON,
        dlg.BUTTON_SCREEN_COMMENTS_OFF,
        dlg.BUTTON_PAINT_RECALL_ON,
        dlg.BUTTON_SNORING_ON,
        dlg.BUTTON_WINDOW_PLAY_ON,
        dlg.BUTTON_TTS_ON,
        dlg.BUTTON_EMOJI_ON,
        dlg.BUTTON_SPECIAL_DAYS_ON,
        dlg.BUTTON_MENU_BUTTONS,
        dlg.BUTTON_REMEMBER,
        dlg.BUTTON_FORGET,
        dlg.BUTTON_SHOW_CREDITS,
        dlg.BUTTON_BACK,
    ]
    assert settings_options_for(_menu_app(paint_recall_enabled=False)) == [
        dlg.BUTTON_SCREEN_EFFECTS_ON,
        dlg.BUTTON_REMINDERS_ON,
        dlg.BUTTON_APP_AWARENESS_ON,
        dlg.BUTTON_SCREEN_COMMENTS_ON,
        dlg.BUTTON_PAINT_RECALL_OFF,
        dlg.BUTTON_SNORING_ON,
        dlg.BUTTON_WINDOW_PLAY_ON,
        dlg.BUTTON_TTS_ON,
        dlg.BUTTON_EMOJI_ON,
        dlg.BUTTON_SPECIAL_DAYS_ON,
        dlg.BUTTON_MENU_BUTTONS,
        dlg.BUTTON_REMEMBER,
        dlg.BUTTON_FORGET,
        dlg.BUTTON_SHOW_CREDITS,
        dlg.BUTTON_BACK,
    ]
    assert settings_options_for(_menu_app(screen_effects_enabled=False)) == [
        dlg.BUTTON_SCREEN_EFFECTS_OFF,
        dlg.BUTTON_REMINDERS_ON,
        dlg.BUTTON_APP_AWARENESS_ON,
        dlg.BUTTON_SCREEN_COMMENTS_ON,
        dlg.BUTTON_PAINT_RECALL_ON,
        dlg.BUTTON_SNORING_ON,
        dlg.BUTTON_WINDOW_PLAY_ON,
        dlg.BUTTON_TTS_ON,
        dlg.BUTTON_EMOJI_ON,
        dlg.BUTTON_SPECIAL_DAYS_ON,
        dlg.BUTTON_MENU_BUTTONS,
        dlg.BUTTON_REMEMBER,
        dlg.BUTTON_FORGET,
        dlg.BUTTON_SHOW_CREDITS,
        dlg.BUTTON_BACK,
    ]
    assert settings_options_for(_menu_app(snoring_enabled=False)) == [
        dlg.BUTTON_SCREEN_EFFECTS_ON,
        dlg.BUTTON_REMINDERS_ON,
        dlg.BUTTON_APP_AWARENESS_ON,
        dlg.BUTTON_SCREEN_COMMENTS_ON,
        dlg.BUTTON_PAINT_RECALL_ON,
        dlg.BUTTON_SNORING_OFF,
        dlg.BUTTON_WINDOW_PLAY_ON,
        dlg.BUTTON_TTS_ON,
        dlg.BUTTON_EMOJI_ON,
        dlg.BUTTON_SPECIAL_DAYS_ON,
        dlg.BUTTON_MENU_BUTTONS,
        dlg.BUTTON_REMEMBER,
        dlg.BUTTON_FORGET,
        dlg.BUTTON_SHOW_CREDITS,
        dlg.BUTTON_BACK,
    ]
    assert settings_options_for(_menu_app(window_grab_enabled=False)) == [
        dlg.BUTTON_SCREEN_EFFECTS_ON,
        dlg.BUTTON_REMINDERS_ON,
        dlg.BUTTON_APP_AWARENESS_ON,
        dlg.BUTTON_SCREEN_COMMENTS_ON,
        dlg.BUTTON_PAINT_RECALL_ON,
        dlg.BUTTON_SNORING_ON,
        dlg.BUTTON_WINDOW_PLAY_OFF,
        dlg.BUTTON_TTS_ON,
        dlg.BUTTON_EMOJI_ON,
        dlg.BUTTON_SPECIAL_DAYS_ON,
        dlg.BUTTON_MENU_BUTTONS,
        dlg.BUTTON_REMEMBER,
        dlg.BUTTON_FORGET,
        dlg.BUTTON_SHOW_CREDITS,
        dlg.BUTTON_BACK,
    ]
    assert settings_options_for(_menu_app(tts_enabled=False)) == [
        dlg.BUTTON_SCREEN_EFFECTS_ON,
        dlg.BUTTON_REMINDERS_ON,
        dlg.BUTTON_APP_AWARENESS_ON,
        dlg.BUTTON_SCREEN_COMMENTS_ON,
        dlg.BUTTON_PAINT_RECALL_ON,
        dlg.BUTTON_SNORING_ON,
        dlg.BUTTON_WINDOW_PLAY_ON,
        dlg.BUTTON_TTS_OFF,
        dlg.BUTTON_EMOJI_ON,
        dlg.BUTTON_SPECIAL_DAYS_ON,
        dlg.BUTTON_MENU_BUTTONS,
        dlg.BUTTON_REMEMBER,
        dlg.BUTTON_FORGET,
        dlg.BUTTON_SHOW_CREDITS,
        dlg.BUTTON_BACK,
    ]

    assert settings_options_for(_menu_app(special_days_enabled=False)) == [
        dlg.BUTTON_SCREEN_EFFECTS_ON,
        dlg.BUTTON_REMINDERS_ON,
        dlg.BUTTON_APP_AWARENESS_ON,
        dlg.BUTTON_SCREEN_COMMENTS_ON,
        dlg.BUTTON_PAINT_RECALL_ON,
        dlg.BUTTON_SNORING_ON,
        dlg.BUTTON_WINDOW_PLAY_ON,
        dlg.BUTTON_TTS_ON,
        dlg.BUTTON_EMOJI_ON,
        dlg.BUTTON_SPECIAL_DAYS_OFF,
        dlg.BUTTON_MENU_BUTTONS,
        dlg.BUTTON_REMEMBER,
        dlg.BUTTON_FORGET,
        dlg.BUTTON_SHOW_CREDITS,
        dlg.BUTTON_BACK,
    ]

    assert settings_options_for(_menu_app(emoji_picker_enabled=False)) == [
        dlg.BUTTON_SCREEN_EFFECTS_ON,
        dlg.BUTTON_REMINDERS_ON,
        dlg.BUTTON_APP_AWARENESS_ON,
        dlg.BUTTON_SCREEN_COMMENTS_ON,
        dlg.BUTTON_PAINT_RECALL_ON,
        dlg.BUTTON_SNORING_ON,
        dlg.BUTTON_WINDOW_PLAY_ON,
        dlg.BUTTON_TTS_ON,
        dlg.BUTTON_EMOJI_OFF,
        dlg.BUTTON_SPECIAL_DAYS_ON,
        dlg.BUTTON_MENU_BUTTONS,
        dlg.BUTTON_REMEMBER,
        dlg.BUTTON_FORGET,
        dlg.BUTTON_SHOW_CREDITS,
        dlg.BUTTON_BACK,
    ]
    assert settings_options_for(
        _menu_app(hidden_menu_buttons={"actions.hug", "main.chat"})
    ) == [
        dlg.BUTTON_SCREEN_EFFECTS_ON,
        dlg.BUTTON_REMINDERS_ON,
        dlg.BUTTON_APP_AWARENESS_ON,
        dlg.BUTTON_SCREEN_COMMENTS_ON,
        dlg.BUTTON_PAINT_RECALL_ON,
        dlg.BUTTON_SNORING_ON,
        dlg.BUTTON_WINDOW_PLAY_ON,
        dlg.BUTTON_TTS_ON,
        dlg.BUTTON_EMOJI_ON,
        dlg.BUTTON_SPECIAL_DAYS_ON,
        dlg.BUTTON_MENU_BUTTONS,
        dlg.BUTTON_REMEMBER,
        dlg.BUTTON_FORGET,
        dlg.BUTTON_SHOW_CREDITS,
        dlg.BUTTON_BACK,
    ]
    assert dlg.BUTTON_CHAT not in menu_options_for(
        _menu_app(hidden_menu_buttons={"main.chat"})
    )
    assert actions_options_for(_menu_app(hidden_menu_buttons={"actions.hug"})) == [
        dlg.BUTTON_SET_REMINDER,
        dlg.BUTTON_TELL_TIME,
        dlg.BUTTON_SING_SONG,
        dlg.BUTTON_FUN_FACT,
        dlg.BUTTON_VISIT_WEBSITE,
        dlg.BUTTON_PLAY_MUSIC,
        dlg.BUTTON_PLAY_GAME,
        dlg.BUTTON_PAINT,
        dlg.BUTTON_BACK,
    ]
    assert actions_options_for(_menu_app()) == [
        dlg.BUTTON_SET_REMINDER,
        dlg.BUTTON_TELL_TIME,
        dlg.BUTTON_SING_SONG,
        dlg.BUTTON_FUN_FACT,
        dlg.BUTTON_VISIT_WEBSITE,
        dlg.BUTTON_PLAY_MUSIC,
        dlg.BUTTON_PLAY_GAME,
        dlg.BUTTON_PAINT,
        dlg.BUTTON_GIVE_HUG,
        dlg.BUTTON_BACK,
    ]


def test_static_questions_match_expected_markers():
    cases = [
        (dlg.DAY_QUESTION, dlg.DAY_QUESTION),
        (dlg.COLOR_QUESTION, dlg.COLOR_QUESTION),
        (dlg.GAME_QUESTION, dlg.GAME_QUESTION),
        (dlg.TRUST_QUESTION, dlg.TRUST_QUESTION),
        (dlg.JOKE_QUESTION, dlg.JOKE_QUESTION),
    ]
    for question, expected_marker in cases:
        spec = find_dialog_spec(question)
        assert spec is not None
        assert spec.marker == expected_marker
