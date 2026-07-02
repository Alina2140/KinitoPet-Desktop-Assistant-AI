from unittest.mock import MagicMock

import pytest

from content import dialogue as dlg
from content.dialog_registry import (
    DIALOG_SPECS,
    find_dialog_spec,
    handle_dialog_response,
    menu_options_for,
)


def test_find_dialog_spec_case_insensitive():
    spec = find_dialog_spec("Hey! CAN I OPEN THE CAMERA?")
    assert spec is not None
    assert spec.marker == dlg.CAMERA_QUESTION_MARKER


def test_find_dialog_spec_unknown_text():
    assert find_dialog_spec("Hello, world!") is None


@pytest.mark.parametrize("question", dlg.CAMERA_QUESTIONS)
def test_all_camera_questions_match_registry(question):
    spec = find_dialog_spec(question)
    assert spec is not None
    assert spec.marker == dlg.CAMERA_QUESTION_MARKER
    assert spec.ui.kind == "buttons"


@pytest.mark.parametrize("question", dlg.BROWSER_QUESTIONS)
def test_all_browser_questions_match_registry(question):
    spec = find_dialog_spec(question)
    assert spec is not None
    assert spec.marker == dlg.BROWSER_QUESTION_MARKER


def test_menu_prompt_matches_registry():
    spec = find_dialog_spec(dlg.MENU_PROMPT)
    assert spec is not None
    app = MagicMock()
    app.paused = False
    app._focus_mode = False
    app._screen_effects_enabled = True
    assert dlg.BUTTON_SAY_GOODBYE in menu_options_for(app)


def test_browser_category_before_generic_browser_question():
    category_idx = next(
        i for i, s in enumerate(DIALOG_SPECS) if s.marker == dlg.BROWSER_CATEGORY_MARKER
    )
    browser_idx = next(
        i for i, s in enumerate(DIALOG_SPECS) if s.marker == dlg.BROWSER_QUESTION_MARKER
    )
    assert category_idx < browser_idx


def test_all_dialog_specs_have_unique_markers():
    markers = [spec.marker.lower() for spec in DIALOG_SPECS]
    assert len(markers) == len(set(markers))


@pytest.mark.parametrize("question", dlg.MUSIC_PLAYER_QUESTIONS)
def test_all_music_questions_match_registry(question):
    spec = find_dialog_spec(question)
    assert spec is not None
    assert spec.marker == dlg.MUSIC_PLAYER_QUESTION_MARKER


@pytest.mark.parametrize("question", dlg.HUG_QUESTIONS)
def test_all_hug_questions_match_registry(question):
    spec = find_dialog_spec(question)
    assert spec is not None
    assert spec.marker == dlg.HUG_QUESTION_MARKER


def test_handle_menu_goodbye(mock_app):
    spec = find_dialog_spec(dlg.MENU_PROMPT)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_SAY_GOODBYE)
    mock_app.say_goodbye.assert_called_once()


def test_menu_includes_chat(mock_app):
    assert dlg.BUTTON_CHAT in menu_options_for(mock_app)


def test_handle_menu_chat(mock_app):
    spec = find_dialog_spec(dlg.MENU_PROMPT)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_CHAT)
    mock_app.start_chat.assert_called_once()


def test_handle_camera_yes_schedules_open(mock_app):
    spec = find_dialog_spec(dlg.CAMERA_QUESTIONS[0])
    handle_dialog_response(mock_app, spec, dlg.BUTTON_YES)
    mock_app.root.after.assert_called()
    assert mock_app.root.after.call_args[0][1] is mock_app.open_camera


def test_handle_camera_no_speaks_declined(mock_app):
    spec = find_dialog_spec(dlg.CAMERA_QUESTIONS[0])
    handle_dialog_response(mock_app, spec, dlg.BUTTON_NO)
    mock_app.speak.assert_called_once()


def test_handle_browser_category_animals(mock_app):
    spec = find_dialog_spec(dlg.BROWSER_CATEGORY_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_CATEGORY_ANIMALS)
    mock_app.open_allowed_site.assert_called_once_with("animals")


def test_handle_reminder_passes_minutes(mock_app):
    spec = find_dialog_spec(dlg.REMINDER_MINUTES_PROMPT)
    handle_dialog_response(mock_app, spec, "15")
    mock_app.set_reminder.assert_called_once_with("15")


def test_handle_reminder_manage_cancel(mock_app):
    spec = find_dialog_spec(dlg.REMINDER_MANAGE_PROMPT)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_CANCEL_REMINDER)
    mock_app.cancel_reminder.assert_called_once()


def test_handle_reminder_manage_adjust(mock_app):
    spec = find_dialog_spec(dlg.REMINDER_MANAGE_PROMPT)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_ADJUST_REMINDER)
    mock_app.speak.assert_called_once_with(dlg.REMINDER_ADJUST_PROMPT, 45, True)


def test_handle_reminder_adjust_passes_minutes(mock_app):
    spec = find_dialog_spec(dlg.REMINDER_ADJUST_PROMPT)
    handle_dialog_response(mock_app, spec, "20")
    mock_app.adjust_reminder.assert_called_once_with("20")


@pytest.mark.parametrize("question", dlg.GAME_QUESTIONS)
def test_all_game_questions_match_registry(question):
    spec = find_dialog_spec(question)
    assert spec is not None
    assert spec.marker == dlg.GAME_QUESTION


def test_game_picker_question_matches_registry():
    spec = find_dialog_spec(dlg.GAME_PICKER_QUESTION)
    assert spec is not None
    assert spec.marker == dlg.GAME_PICKER_MARKER


def test_rps_question_matches_registry():
    spec = find_dialog_spec(dlg.RPS_QUESTION)
    assert spec is not None
    assert spec.marker == dlg.RPS_MARKER


def test_number_guess_question_matches_registry():
    spec = find_dialog_spec(dlg.NUMBER_GUESS_QUESTION)
    assert spec is not None
    assert spec.marker == dlg.NUMBER_GUESS_MARKER


def test_game_picker_before_game_question():
    picker_idx = next(i for i, s in enumerate(DIALOG_SPECS) if s.marker == dlg.GAME_PICKER_MARKER)
    game_idx = next(i for i, s in enumerate(DIALOG_SPECS) if s.marker == dlg.GAME_QUESTION)
    assert picker_idx < game_idx


@pytest.mark.parametrize(
    ("question", "expected_marker"),
    [
        (dlg.QUICK_GAMES_QUESTION, dlg.QUICK_GAMES_MARKER),
        (dlg.BOARD_GAMES_QUESTION, dlg.BOARD_GAMES_MARKER),
        (dlg.COIN_DICE_QUESTION, dlg.COIN_DICE_MARKER),
        (dlg.COIN_FLIP_QUESTION, dlg.COIN_FLIP_MARKER),
        (dlg.DICE_GUESS_QUESTION, dlg.DICE_GUESS_MARKER),
        (dlg.MAGIC_8_BALL_QUESTION, dlg.MAGIC_8_BALL_MARKER),
        (dlg.GAME_PLAY_AGAIN_SUFFIX, dlg.GAME_PLAY_AGAIN_MARKER),
    ],
)
def test_new_game_questions_match_registry(question, expected_marker):
    spec = find_dialog_spec(question)
    assert spec is not None
    assert spec.marker == expected_marker


def test_true_false_question_matches_registry():
    spec = find_dialog_spec("True or false: Honey never spoils.")
    assert spec is not None
    assert spec.marker == dlg.TRUE_FALSE_MARKER


def test_quick_games_before_game_picker():
    quick_idx = next(i for i, s in enumerate(DIALOG_SPECS) if s.marker == dlg.QUICK_GAMES_MARKER)
    picker_idx = next(i for i, s in enumerate(DIALOG_SPECS) if s.marker == dlg.GAME_PICKER_MARKER)
    assert quick_idx < picker_idx
