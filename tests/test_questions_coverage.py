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
    return app


def test_menu_options_default_toggle_labels():
    opts = menu_options_for(_menu_app())
    assert dlg.BUTTON_SLEEP in opts
    assert dlg.BUTTON_WAKE_UP not in opts
    assert dlg.BUTTON_FOCUS in opts
    assert dlg.BUTTON_UNFOCUS not in opts
    assert dlg.BUTTON_SCREEN_EFFECTS_OFF in opts
    assert dlg.BUTTON_SCREEN_EFFECTS_ON not in opts


def test_menu_options_reflect_active_states():
    opts = menu_options_for(_menu_app(paused=True, screen_effects_enabled=False))
    assert dlg.BUTTON_WAKE_UP in opts
    assert dlg.BUTTON_SLEEP not in opts
    assert dlg.BUTTON_FOCUS in opts
    assert dlg.BUTTON_UNFOCUS not in opts
    assert dlg.BUTTON_SCREEN_EFFECTS_ON in opts
    assert dlg.BUTTON_SCREEN_EFFECTS_OFF not in opts


def test_menu_options_hide_blocked_actions_in_focus_mode():
    opts = menu_options_for(_menu_app(focus_mode=True))
    assert opts == [dlg.BUTTON_UNFOCUS]
    assert dlg.BUTTON_SET_REMINDER not in opts
    assert dlg.BUTTON_SING_SONG not in opts


def test_menu_options_include_all_actions():
    opts = menu_options_for(_menu_app())
    expected = {
        dlg.BUTTON_SET_REMINDER,
        dlg.BUTTON_TELL_TIME,
        dlg.BUTTON_SING_SONG,
        dlg.BUTTON_FUN_FACT,
        dlg.BUTTON_VISIT_WEBSITE,
        dlg.BUTTON_PLAY_MUSIC,
        dlg.BUTTON_PLAY_GAME,
        dlg.BUTTON_GIVE_HUG,
        dlg.BUTTON_SHOW_CREDITS,
        dlg.BUTTON_SAY_GOODBYE,
    }
    assert expected.issubset(set(opts))
    assert len(opts) == 13


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
