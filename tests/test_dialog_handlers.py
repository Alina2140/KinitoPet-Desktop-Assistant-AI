"""Integration-style tests for dialog handlers beyond the happy path."""

from content import dialogue as dlg
from content.dialog_registry import find_dialog_spec, handle_dialog_response


def test_handle_story_declined_clears_pending(mock_app):
    mock_app._pending_story = "A tale"
    spec = find_dialog_spec(dlg.STORY_QUESTIONS[0])
    handle_dialog_response(mock_app, spec, dlg.BUTTON_NOT_NOW)
    assert mock_app._pending_story is None
    mock_app.speak.assert_called_once()


def test_handle_story_accepted(mock_app):
    spec = find_dialog_spec(dlg.STORY_QUESTIONS[0])
    handle_dialog_response(mock_app, spec, dlg.BUTTON_SURE)
    mock_app.say_pending_story.assert_called_once()


def test_handle_browser_yes_opens_category_picker(mock_app):
    spec = find_dialog_spec(dlg.BROWSER_QUESTIONS[0])
    handle_dialog_response(mock_app, spec, dlg.BUTTON_YES)
    mock_app.ask_browser_category.assert_called_once()


def test_handle_browser_no_declines(mock_app):
    spec = find_dialog_spec(dlg.BROWSER_QUESTIONS[0])
    handle_dialog_response(mock_app, spec, dlg.BUTTON_NO)
    mock_app.speak.assert_called_once()


def test_handle_hug_yes(mock_app):
    spec = find_dialog_spec(dlg.HUG_QUESTIONS[0])
    handle_dialog_response(mock_app, spec, dlg.BUTTON_YES)
    mock_app.give_hug.assert_called_once()


def test_handle_music_player_yes(mock_app):
    spec = find_dialog_spec(dlg.MUSIC_PLAYER_QUESTIONS[0])
    handle_dialog_response(mock_app, spec, dlg.BUTTON_YES)
    mock_app.open_music_player.assert_called_once()


def test_handle_color_text_response(mock_app):
    spec = find_dialog_spec(dlg.COLOR_QUESTION)
    handle_dialog_response(mock_app, spec, "blue")
    mock_app.speak.assert_called_once()
    assert "blue" in mock_app.speak.call_args[0][0]


def test_handle_game_okay_opens_game_picker(mock_app):
    spec = find_dialog_spec(dlg.GAME_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_OKAY)
    mock_app.offer_game_picker.assert_called_once()


def test_handle_menu_play_game(mock_app):
    spec = find_dialog_spec(dlg.ACTIONS_MENU_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_PLAY_GAME)
    mock_app.offer_game_picker.assert_called_once()


def test_handle_menu_opens_modes_submenu(mock_app):
    spec = find_dialog_spec(dlg.MENU_PROMPT)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_MODES)
    mock_app.speak.assert_called_once_with(
        dlg.MODES_MENU_QUESTION, 45, True, allow_in_focus=True
    )


def test_handle_menu_opens_settings_submenu(mock_app):
    spec = find_dialog_spec(dlg.MENU_PROMPT)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_SETTINGS)
    mock_app.speak.assert_called_once_with(dlg.SETTINGS_MENU_QUESTION, 45, True)


def test_handle_menu_opens_actions_submenu(mock_app):
    spec = find_dialog_spec(dlg.MENU_PROMPT)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_ACTIONS)
    mock_app.speak.assert_called_once_with(dlg.ACTIONS_MENU_QUESTION, 45, True)


def test_handle_menu_speaks_current_mood(mock_app):
    spec = find_dialog_spec(dlg.MENU_PROMPT)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_MOOD)
    mock_app.speak_current_mood.assert_called_once()


def test_handle_game_picker_opens_quick_games(mock_app):
    spec = find_dialog_spec(dlg.GAME_PICKER_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_QUICK_GAMES)
    mock_app.offer_quick_games.assert_called_once()


def test_handle_game_picker_opens_board_games(mock_app):
    spec = find_dialog_spec(dlg.GAME_PICKER_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_BOARD_GAMES)
    mock_app.offer_board_games.assert_called_once()


def test_handle_board_games_tic_tac_toe(mock_app):
    spec = find_dialog_spec(dlg.BOARD_GAMES_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_GAME_TIC_TAC_TOE)
    mock_app.start_tic_tac_toe.assert_called_once()


def test_handle_board_games_snake(mock_app):
    spec = find_dialog_spec(dlg.BOARD_GAMES_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_GAME_SNAKE)
    mock_app.start_snake.assert_called_once()


def test_handle_board_games_tetris(mock_app):
    spec = find_dialog_spec(dlg.BOARD_GAMES_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_GAME_TETRIS)
    mock_app.start_tetris.assert_called_once()


def test_handle_board_games_connect_four(mock_app):
    spec = find_dialog_spec(dlg.BOARD_GAMES_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_GAME_CONNECT_FOUR)
    mock_app.start_connect_four.assert_called_once()


def test_handle_board_games_hangman(mock_app):
    spec = find_dialog_spec(dlg.BOARD_GAMES_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_GAME_HANGMAN)
    mock_app.start_hangman.assert_called_once()


def test_handle_board_games_minesweeper(mock_app):
    spec = find_dialog_spec(dlg.BOARD_GAMES_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_GAME_MINESWEEPER)
    mock_app.start_minesweeper.assert_called_once()


def test_handle_board_games_back(mock_app):
    spec = find_dialog_spec(dlg.BOARD_GAMES_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_BACK)
    mock_app.offer_game_picker.assert_called_once()


def test_handle_quick_games_coin_dice(mock_app):
    spec = find_dialog_spec(dlg.QUICK_GAMES_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_GAME_COIN_DICE)
    mock_app.start_coin_dice.assert_called_once()


def test_handle_coin_flip_offers_play_again(mock_app):
    spec = find_dialog_spec(dlg.COIN_FLIP_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_HEADS)
    mock_app.speak.assert_called_once()
    spoken = mock_app.speak.call_args[0][0]
    assert dlg.GAME_PLAY_AGAIN_MARKER.lower() in spoken.lower()


def test_handle_play_again_restarts_coin_dice(mock_app):
    mock_app._play_again_restart = lambda a: a.start_coin_dice()
    spec = find_dialog_spec(dlg.GAME_PLAY_AGAIN_SUFFIX)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_PLAY_AGAIN)
    mock_app.start_coin_dice.assert_called_once()


def test_handle_play_again_back_opens_quick_games(mock_app):
    spec = find_dialog_spec(dlg.GAME_PLAY_AGAIN_SUFFIX)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_BACK)
    mock_app.offer_quick_games.assert_called_once()


def test_handle_magic_8_ball_empty_reprompts(mock_app):
    spec = find_dialog_spec(dlg.MAGIC_8_BALL_QUESTION)
    handle_dialog_response(mock_app, spec, "   ")
    assert mock_app.speak.call_count == 2


def test_handle_magic_8_ball_answer(mock_app):
    spec = find_dialog_spec(dlg.MAGIC_8_BALL_QUESTION)
    handle_dialog_response(mock_app, spec, "Will I win?")
    mock_app.speak.assert_called_once()
    spoken = mock_app.speak.call_args[0][0]
    assert "Will I win?" in spoken
    assert dlg.GAME_PLAY_AGAIN_MARKER.lower() in spoken.lower()


def test_handle_true_false_correct_advances(mock_app):
    from content.trivia_questions import TriviaQuestion

    mock_app._trivia_current = TriviaQuestion("The sky is blue.", True)
    mock_app._trivia_score = 0
    mock_app._trivia_round = 0
    spec = find_dialog_spec("True or false: The sky is blue.")
    handle_dialog_response(mock_app, spec, dlg.BUTTON_TRUE)
    assert mock_app._trivia_score == 1
    feedback_call = mock_app.speak.call_args_list[0]
    assert feedback_call.kwargs.get("skip_ai") is True
    mock_app._ask_next_trivia.assert_called_once()


def test_handle_true_false_round_end_offers_play_again(mock_app):
    from content.trivia_questions import ROUND_SIZE, TriviaQuestion

    mock_app._trivia_current = TriviaQuestion("The sky is blue.", True)
    mock_app._trivia_score = ROUND_SIZE - 1
    mock_app._trivia_round = ROUND_SIZE - 1
    mock_app._trivia_pack = "animals"
    spec = find_dialog_spec("True or false: The sky is blue.")
    handle_dialog_response(mock_app, spec, dlg.BUTTON_TRUE)
    spoken = mock_app.speak.call_args[0][0]
    assert dlg.GAME_PLAY_AGAIN_MARKER.lower() in spoken.lower()
    assert mock_app._play_again_restart is not None
    mock_app._play_again_restart(mock_app)
    mock_app.start_true_false_pack.assert_called_once_with("animals")


def test_handle_trivia_pack_animals(mock_app):
    from content.trivia_questions import PACK_ANIMALS

    spec = find_dialog_spec(dlg.TRIVIA_PACK_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_TRIVIA_ANIMALS)
    mock_app.start_true_false_pack.assert_called_once_with(PACK_ANIMALS)


def test_handle_trivia_pack_back_opens_quick_games(mock_app):
    spec = find_dialog_spec(dlg.TRIVIA_PACK_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_BACK)
    mock_app.offer_quick_games.assert_called_once()


def test_handle_quick_games_true_false_opens_pack_picker(mock_app):
    spec = find_dialog_spec(dlg.QUICK_GAMES_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_GAME_TRUE_FALSE)
    mock_app.start_true_false.assert_called_once()


def test_handle_tts_volume_soft(mock_app):
    question = dlg.TTS_VOLUME_QUESTION.format(volume=100)
    spec = find_dialog_spec(question)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_TTS_VOLUME_SOFT)
    mock_app.set_tts_volume.assert_called_once_with(dlg.TTS_VOLUME_SOFT)


def test_handle_tts_volume_back_opens_settings(mock_app):
    question = dlg.TTS_VOLUME_QUESTION.format(volume=70)
    spec = find_dialog_spec(question)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_BACK)
    mock_app.speak.assert_called()
    spoken = mock_app.speak.call_args[0][0]
    assert dlg.SETTINGS_MENU_MARKER.lower() in spoken.lower()


def test_handle_settings_turn_on_off_opens_toggles(mock_app):
    spec = find_dialog_spec(dlg.SETTINGS_MENU_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_TURN_ON_OFF)
    spoken = mock_app.speak.call_args[0][0]
    assert dlg.SETTINGS_TOGGLES_MARKER.lower() in spoken.lower()


def test_handle_settings_toggles_back_opens_settings(mock_app):
    spec = find_dialog_spec(dlg.SETTINGS_TOGGLES_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_BACK)
    spoken = mock_app.speak.call_args[0][0]
    assert dlg.SETTINGS_MENU_MARKER.lower() in spoken.lower()


def test_game_picker_buttons_exclude_not_now():
    spec = find_dialog_spec(dlg.GAME_PICKER_QUESTION)
    assert dlg.BUTTON_NOT_NOW not in spec.ui.buttons


def test_handle_rps_rock(mock_app):
    spec = find_dialog_spec(dlg.RPS_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_ROCK)
    mock_app.speak.assert_called_once()


def test_handle_number_guess_higher_reprompts(mock_app):
    mock_app._number_guess_target = 50
    mock_app._number_guess_attempts = 0
    spec = find_dialog_spec(dlg.NUMBER_GUESS_QUESTION)
    handle_dialog_response(mock_app, spec, "10")
    mock_app.speak.assert_called_once()
    spoken = mock_app.speak.call_args[0][0]
    assert dlg.NUMBER_GUESS_MARKER.lower() in spoken.lower()


def test_handle_number_guess_correct(mock_app):
    mock_app._number_guess_target = 50
    mock_app._number_guess_attempts = 0
    spec = find_dialog_spec(dlg.NUMBER_GUESS_QUESTION)
    handle_dialog_response(mock_app, spec, "50")
    mock_app.speak.assert_called_once()
    assert mock_app._number_guess_target is None


def test_handle_joke_sure(mock_app):
    spec = find_dialog_spec(dlg.JOKE_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_SURE)
    mock_app.say_random_joke.assert_called_once()


def test_handle_menu_tell_time(mock_app):
    spec = find_dialog_spec(dlg.ACTIONS_MENU_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_TELL_TIME)
    mock_app.print_current_datetime.assert_called_once()


def test_handle_menu_toggle_screen_effects(mock_app):
    spec = find_dialog_spec(dlg.SETTINGS_MENU_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_SCREEN_EFFECTS_ON)
    mock_app.toggle_screen_effects.assert_called_once()


def test_handle_menu_toggle_ambient_reminders(mock_app):
    spec = find_dialog_spec(dlg.SETTINGS_MENU_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_REMINDERS_ON)
    mock_app.toggle_ambient_reminders.assert_called_once()


def test_handle_menu_toggle_app_awareness(mock_app):
    spec = find_dialog_spec(dlg.SETTINGS_MENU_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_APP_AWARENESS_ON)
    mock_app.toggle_app_awareness.assert_called_once()


def test_handle_menu_toggle_screen_comments(mock_app):
    spec = find_dialog_spec(dlg.SETTINGS_MENU_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_SCREEN_COMMENTS_ON)
    mock_app.toggle_screen_comments.assert_called_once()


def test_handle_menu_toggle_paint_recall(mock_app):
    spec = find_dialog_spec(dlg.SETTINGS_MENU_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_PAINT_RECALL_ON)
    mock_app.toggle_paint_recall.assert_called_once()


def test_handle_menu_toggle_snoring(mock_app):
    spec = find_dialog_spec(dlg.SETTINGS_MENU_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_SNORING_ON)
    mock_app.toggle_snoring.assert_called_once()


def test_handle_menu_toggle_window_play(mock_app):
    spec = find_dialog_spec(dlg.SETTINGS_MENU_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_WINDOW_PLAY_ON)
    mock_app.toggle_window_grab.assert_called_once()


def test_handle_menu_toggle_tts(mock_app):
    spec = find_dialog_spec(dlg.SETTINGS_MENU_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_TTS_ON)
    mock_app.toggle_tts.assert_called_once()


def test_handle_menu_toggle_player_focus(mock_app):
    spec = find_dialog_spec(dlg.SETTINGS_MENU_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_PLAYER_FOCUS_ON)
    mock_app.toggle_player_focus.assert_called_once()


def test_handle_menu_toggle_emoji_picker(mock_app):
    spec = find_dialog_spec(dlg.SETTINGS_MENU_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_EMOJI_ON)
    mock_app.toggle_emoji_picker_setting.assert_called_once()


def test_handle_menu_toggle_special_days(mock_app):
    spec = find_dialog_spec(dlg.SETTINGS_MENU_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_SPECIAL_DAYS_ON)
    mock_app.toggle_special_days.assert_called_once()


def test_handle_menu_open_menu_buttons(mock_app):
    spec = find_dialog_spec(dlg.SETTINGS_MENU_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_MENU_BUTTONS)
    mock_app.open_menu_button_settings.assert_called_once()


def test_handle_menu_toggle_focus(mock_app):
    spec = find_dialog_spec(dlg.MODES_MENU_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_FOCUS)
    mock_app.toggle_focus.assert_called_once()


def test_handle_menu_wake_up(mock_app):
    spec = find_dialog_spec(dlg.MODES_MENU_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_WAKE_UP)
    mock_app.toggle_pause.assert_called_once()


def test_handle_menu_wake_up_allowed_during_sleep(mock_app):
    mock_app.paused = True
    spec = find_dialog_spec(dlg.MENU_PROMPT)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_WAKE_UP)
    mock_app.toggle_pause.assert_called_once()


def test_handle_menu_unfocus(mock_app):
    spec = find_dialog_spec(dlg.MODES_MENU_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_UNFOCUS)
    mock_app.toggle_focus.assert_called_once()


def test_handle_menu_blocked_during_focus_mode(mock_app):
    mock_app._focus_mode = True
    spec = find_dialog_spec(dlg.MENU_PROMPT)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_ACTIONS)
    mock_app.speak.assert_not_called()


def test_handle_menu_blocked_during_sleep(mock_app):
    mock_app.paused = True
    spec = find_dialog_spec(dlg.MENU_PROMPT)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_SETTINGS)
    mock_app.speak.assert_not_called()


def test_handle_menu_unfocus_allowed_during_focus_mode(mock_app):
    mock_app._focus_mode = True
    spec = find_dialog_spec(dlg.MENU_PROMPT)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_UNFOCUS)
    mock_app.toggle_focus.assert_called_once()


def test_handle_menu_goodbye_allowed_during_focus_mode(mock_app):
    mock_app._focus_mode = True
    spec = find_dialog_spec(dlg.MENU_PROMPT)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_SAY_GOODBYE)
    mock_app.say_goodbye.assert_called_once()


def test_handle_menu_goodbye_allowed_during_sleep(mock_app):
    mock_app.paused = True
    spec = find_dialog_spec(dlg.MENU_PROMPT)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_SAY_GOODBYE)
    mock_app.say_goodbye.assert_called_once()


def test_handle_menu_focus_timer_allowed_during_focus_mode(mock_app):
    mock_app._focus_mode = True
    spec = find_dialog_spec(dlg.MENU_PROMPT)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_SET_FOCUS_TIMER)
    mock_app.open_focus_timer_controls.assert_called_once()


def test_handle_submenu_back_reopens_main_menu(mock_app):
    spec = find_dialog_spec(dlg.SETTINGS_MENU_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_BACK)
    mock_app.speak.assert_called_once_with(
        dlg.MENU_PROMPT, 45, True, allow_in_focus=True
    )
