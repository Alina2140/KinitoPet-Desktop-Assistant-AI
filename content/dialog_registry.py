"""Central registry for interactive speech-bubble dialogs."""

from __future__ import annotations

import random
import webbrowser
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from content import credits, game_lines
from content import dialogue as dlg
from content.site_validator import pick_random_category
from content.trivia_questions import ROUND_SIZE, check_answer
from kinito.features.games.coin_dice import (
    HEADS,
    TAILS,
    coin_outcome,
    dice_outcome,
    flip_coin,
    roll_dice,
)
from kinito.features.games.magic_8_ball import pick_answer as pick_8ball_answer
from kinito.features.games.number_guess import (
    MAX_ATTEMPTS,
    compare_guess,
    is_valid_guess,
    parse_guess,
)
from kinito.features.games.rock_paper_scissors import MOVES, rps_winner

Handler = Callable[..., None]


@dataclass(frozen=True)
class DialogUI:
    """Describes how a dialog is presented (buttons or textbox)."""

    kind: Literal["buttons", "textbox"]
    buttons: tuple[str, ...] = ()
    textbox_prompt: str | None = None


@dataclass(frozen=True)
class DialogSpec:
    """Maps a speech-bubble marker substring to UI and a response handler."""

    marker: str
    ui: DialogUI
    handler: Handler


def find_dialog_spec(text: str) -> DialogSpec | None:
    """Return the first DialogSpec whose marker appears in *text* (case-insensitive)."""
    text_lower = text.lower()
    for spec in DIALOG_SPECS:
        if spec.marker.lower() in text_lower:
            return spec
    return None


def apply_dialog_ui(app, spec: DialogSpec) -> None:
    """Attach buttons or a textbox to the active speech bubble."""
    if spec.ui.kind == "buttons":
        buttons = menu_options_for(app) if spec.marker == dlg.MENU_PROMPT else list(spec.ui.buttons)
        app.show_response_buttons(buttons)
    elif spec.ui.kind == "textbox":
        app.show_response_textbox(spec.ui.textbox_prompt or spec.marker)


def menu_options_for(app) -> list[str]:
    """Return right-click menu labels with state-aware toggle names."""
    sleep_label = dlg.BUTTON_WAKE_UP if getattr(app, "paused", False) else dlg.BUTTON_SLEEP
    focus_label = dlg.BUTTON_UNFOCUS if getattr(app, "_focus_mode", False) else dlg.BUTTON_FOCUS
    effects_label = (
        dlg.BUTTON_SCREEN_EFFECTS_OFF
        if getattr(app, "_screen_effects_enabled", True)
        else dlg.BUTTON_SCREEN_EFFECTS_ON
    )
    options = [
        dlg.BUTTON_SET_REMINDER,
        dlg.BUTTON_TELL_TIME,
        sleep_label,
        focus_label,
        effects_label,
        dlg.BUTTON_SING_SONG,
        dlg.BUTTON_FUN_FACT,
        dlg.BUTTON_CHAT,
        dlg.BUTTON_VISIT_WEBSITE,
        dlg.BUTTON_PLAY_MUSIC,
        dlg.BUTTON_PLAY_GAME,
        dlg.BUTTON_GIVE_HUG,
        dlg.BUTTON_SHOW_CREDITS,
        dlg.BUTTON_SAY_GOODBYE,
    ]
    allowed: set[str] = set()
    if getattr(app, "paused", False):
        allowed |= _MENU_SLEEP_BUTTONS
    if getattr(app, "_focus_mode", False):
        allowed |= _MENU_FOCUS_BUTTONS
    if allowed:
        return [option for option in options if option in allowed]
    return options


_MENU_SLEEP_BUTTONS = frozenset({dlg.BUTTON_WAKE_UP})
_MENU_FOCUS_BUTTONS = frozenset({dlg.BUTTON_FOCUS, dlg.BUTTON_UNFOCUS})


def handle_dialog_response(app, spec: DialogSpec, response: str) -> None:
    """Dispatch the user's *response* to the spec's handler."""
    spec.handler(app, response)


# --- Handler factories ---


def _speak_declined(app, lines) -> None:
    """Acknowledge a declined offer with a short spoken line."""
    app.speak(dlg.pick_declined_line(lines))


def _yes_no(yes_fn: Handler, no_lines) -> Handler:
    """Build a handler that runs *yes_fn* on Yes or speaks *no_lines* on No."""

    def handler(app, response: str) -> None:
        if response == dlg.BUTTON_YES:
            yes_fn(app)
        elif response == dlg.BUTTON_NO:
            _speak_declined(app, no_lines)

    return handler


def _yes_no_lines(yes_lines, no_lines) -> Handler:
    """Build a handler that speaks variant lines for Yes/No answers."""

    def handler(app, response: str) -> None:
        if response == dlg.BUTTON_YES:
            app.speak(dlg.pick_line(yes_lines))
        elif response == dlg.BUTTON_NO:
            app.speak(dlg.pick_declined_line(no_lines))

    return handler


def _good_bad(good_lines, bad_lines) -> Handler:
    """Build a handler for Good/Bad button pairs."""

    def handler(app, response: str) -> None:
        if response == dlg.BUTTON_GOOD:
            app.speak(dlg.pick_line(good_lines))
        elif response == dlg.BUTTON_BAD:
            app.speak(dlg.pick_line(bad_lines))

    return handler


def _sure_decline(yes_fn: Handler, declined_lines) -> Handler:
    """Build a handler for Sure / Not now button pairs."""

    def handler(app, response: str) -> None:
        if response == dlg.BUTTON_SURE:
            yes_fn(app)
        elif response == dlg.BUTTON_NOT_NOW:
            _speak_declined(app, declined_lines)

    return handler


def _text_format(response_lines) -> Handler:
    """Build a handler that speaks a formatted line with the user's text answer."""

    def handler(app, response: str) -> None:
        app.speak(dlg.pick_line(response_lines).format(response=response))

    return handler


def _okay_not_now(
    yes_fn: Handler, declined_lines, *, minimize_count: int = 0, speak_pitch: int = 45
) -> Handler:
    """Build a handler for Okay / Not now; optionally minimize windows on decline."""

    def handler(app, response: str) -> None:
        if response == dlg.BUTTON_OKAY:
            yes_fn(app)
        elif response == dlg.BUTTON_NOT_NOW:
            _speak_declined(app, declined_lines)
            for _ in range(minimize_count):
                app.minimize_current_window()

    return handler


def _button_map(actions: dict[str, Handler]) -> Handler:
    """Build a handler that dispatches by exact button label."""

    def handler(app, response: str) -> None:
        action = actions.get(response)
        if action:
            action(app)

    return handler


# --- Special handlers ---


def _handle_menu(app, response: str) -> None:
    """Handle right-click menu button selections."""
    if getattr(app, "paused", False) and response not in _MENU_SLEEP_BUTTONS:
        return
    if getattr(app, "_focus_mode", False) and response not in _MENU_FOCUS_BUTTONS:
        return
    actions = {
        dlg.BUTTON_SET_REMINDER: lambda a: a.speak(dlg.REMINDER_MINUTES_PROMPT, 45, True),
        dlg.BUTTON_SLEEP: lambda a: a.toggle_pause(),
        dlg.BUTTON_WAKE_UP: lambda a: a.toggle_pause(),
        dlg.BUTTON_FOCUS: lambda a: a.toggle_focus(),
        dlg.BUTTON_UNFOCUS: lambda a: a.toggle_focus(),
        dlg.BUTTON_SCREEN_EFFECTS_ON: lambda a: a.toggle_screen_effects(),
        dlg.BUTTON_SCREEN_EFFECTS_OFF: lambda a: a.toggle_screen_effects(),
        dlg.BUTTON_SING_SONG: lambda a: a.say_random_poem(),
        dlg.BUTTON_FUN_FACT: lambda a: a.say_random_fact(),
        dlg.BUTTON_CHAT: lambda a: a.start_chat(),
        dlg.BUTTON_VISIT_WEBSITE: lambda a: a.ask_browser_category(),
        dlg.BUTTON_PLAY_MUSIC: lambda a: a.ask_music_player_pick(),
        dlg.BUTTON_PLAY_GAME: lambda a: a.offer_game_picker(),
        dlg.BUTTON_GIVE_HUG: lambda a: a.give_hug(),
        dlg.BUTTON_TELL_TIME: lambda a: a.print_current_datetime(),
        dlg.BUTTON_SHOW_CREDITS: lambda a: a.show_credits(),
        dlg.BUTTON_SAY_GOODBYE: lambda a: a.say_goodbye(),
    }
    action = actions.get(response)
    if action:
        action(app)


def _handle_credits(app, response: str) -> None:
    """Open attribution links from the credits dialog."""
    links = {
        dlg.BUTTON_CREDITS_STEAM: credits.CREDITS_URL_STEAM,
        dlg.BUTTON_CREDITS_GITHUB: credits.CREDITS_URL_GITHUB,
    }
    url = links.get(response)
    if url:
        webbrowser.open(url)


def _handle_reminder(app, response: str) -> None:
    """Parse minutes from the reminder textbox and start the timer."""
    app.set_reminder(f"{response}")


def _handle_reminder_adjust(app, response: str) -> None:
    """Parse minutes from the adjust dialog and restart the timer."""
    app.adjust_reminder(f"{response}")


def _handle_reminder_manage(app, response: str) -> None:
    """Cancel or open the adjust flow for the active reminder."""
    if response == dlg.BUTTON_CANCEL_REMINDER:
        app.cancel_reminder()
    elif response == dlg.BUTTON_ADJUST_REMINDER:
        app.speak(dlg.REMINDER_ADJUST_PROMPT, 45, True)


def _handle_story(app, response: str) -> None:
    """Accept or decline a pending short-story offer."""
    if response == dlg.BUTTON_SURE:
        app.say_pending_story()
    elif response == dlg.BUTTON_NOT_NOW:
        app._pending_story = None
        _speak_declined(app, dlg.STORY_DECLINED_LINES)


def _handle_browser_category(app, response: str) -> None:
    """Map a category button to open_allowed_site."""
    category_map = {
        dlg.BUTTON_CATEGORY_ANIMALS: "animals",
        dlg.BUTTON_CATEGORY_KNOWLEDGE: "knowledge",
        dlg.BUTTON_CATEGORY_GAMES: "games",
        dlg.BUTTON_CATEGORY_HORROR: "horror",
    }
    if response == dlg.BUTTON_CATEGORY_RANDOM:
        category = pick_random_category()
    else:
        category = category_map.get(response)
    if category:
        app.open_allowed_site(category)


def _handle_music_pick(app, response: str) -> None:
    """Open file picker or play a random MP3 based on the user's choice."""
    if response == dlg.BUTTON_NOT_NOW:
        _speak_declined(app, dlg.MUSIC_PLAYER_DECLINED_LINES)
    elif response == dlg.BUTTON_PICK_SONG:
        app.root.after(0, app.pick_and_play_mp3)
    elif response == dlg.BUTTON_CATEGORY_RANDOM:
        app.play_random_mp3()


def _handle_music_manage(app, response: str) -> None:
    """Stop or replace the song that is currently playing."""
    if response == dlg.BUTTON_STOP_MUSIC:
        app.stop_user_music()
    elif response == dlg.BUTTON_CHANGE_SONG:
        app.root.after(0, app.pick_and_play_mp3)
    elif response == dlg.BUTTON_CATEGORY_RANDOM:
        app.play_random_mp3()


def _handle_poem(app, response: str) -> None:
    """Accept a poem, or reject it (with optional window minimizing)."""
    if response == dlg.BUTTON_YES:
        app.say_random_poem()
    elif response == dlg.BUTTON_POEM_REJECT:
        _speak_declined(app, dlg.POEM_REJECT_LINES)
        for _ in range(8):
            app.minimize_current_window()


def _handle_game_picker(app, response: str) -> None:
    """Open the quick-games or board-games submenu."""
    actions = {
        dlg.BUTTON_QUICK_GAMES: lambda a: a.offer_quick_games(),
        dlg.BUTTON_BOARD_GAMES: lambda a: a.offer_board_games(),
    }
    action = actions.get(response)
    if action:
        action(app)


def _handle_quick_games(app, response: str) -> None:
    """Launch a quick mini-game or return to the top-level picker."""
    if response == dlg.BUTTON_BACK:
        app.offer_game_picker()
        return
    actions = {
        dlg.BUTTON_GAME_RPS: lambda a: a.start_rock_paper_scissors(),
        dlg.BUTTON_GAME_NUMBER_GUESS: lambda a: a.start_number_guess(),
        dlg.BUTTON_GAME_COIN_DICE: lambda a: a.start_coin_dice(),
        dlg.BUTTON_GAME_MAGIC_8_BALL: lambda a: a.start_magic_8_ball(),
        dlg.BUTTON_GAME_TRUE_FALSE: lambda a: a.start_true_false(),
    }
    action = actions.get(response)
    if action:
        action(app)


def _handle_board_games(app, response: str) -> None:
    """Launch a board mini-game or return to the top-level picker."""
    if response == dlg.BUTTON_BACK:
        app.offer_game_picker()
        return
    actions = {
        dlg.BUTTON_GAME_TIC_TAC_TOE: lambda a: a.start_tic_tac_toe(),
        dlg.BUTTON_GAME_MEMORY: lambda a: a.start_memory(),
        dlg.BUTTON_GAME_BATTLESHIPS: lambda a: a.start_battleships(),
    }
    action = actions.get(response)
    if action:
        action(app)


def _offer_play_again(app, line: str, restart_fn) -> None:
    """Speak *line* and show Play Again / Back buttons."""
    app._play_again_restart = restart_fn
    app.speak(f"{line} {dlg.GAME_PLAY_AGAIN_SUFFIX}", 45, True)


def _handle_play_again(app, response: str) -> None:
    """Restart the last quick game or return to the quick-games menu."""
    if response == dlg.BUTTON_PLAY_AGAIN:
        restart = getattr(app, "_play_again_restart", None)
        if restart:
            restart(app)
    elif response == dlg.BUTTON_BACK:
        app.offer_quick_games()


def _handle_coin_dice_mode(app, response: str) -> None:
    """Choose coin flip or dice roll."""
    if response == dlg.BUTTON_FLIP_COIN:
        app.speak(dlg.COIN_FLIP_QUESTION, 45, True)
    elif response == dlg.BUTTON_ROLL_DICE:
        app.speak(dlg.DICE_GUESS_QUESTION, 45, True)


def _handle_coin_flip(app, response: str) -> None:
    """Resolve a coin-flip guess."""
    guess_map = {
        dlg.BUTTON_HEADS: HEADS,
        dlg.BUTTON_TAILS: TAILS,
    }
    guess = guess_map.get(response)
    if guess is None:
        return
    result = flip_coin()
    fmt = {"guess": guess, "result": result}
    if coin_outcome(guess, result) == "win":
        line = dlg.pick_line(game_lines.COIN_WIN_LINES).format(**fmt)
    else:
        line = dlg.pick_line(game_lines.COIN_LOSE_LINES).format(**fmt)
    _offer_play_again(app, line, lambda a: a.start_coin_dice())


def _handle_dice_guess(app, response: str) -> None:
    """Resolve a dice-guess attempt."""
    if response not in dlg.DICE_CHOICES:
        return
    guess = int(response)
    roll = roll_dice()
    fmt = {"guess": guess, "roll": roll}
    if dice_outcome(guess, roll) == "win":
        line = dlg.pick_line(game_lines.DICE_WIN_LINES).format(**fmt)
    else:
        line = dlg.pick_line(game_lines.DICE_LOSE_LINES).format(**fmt)
    _offer_play_again(app, line, lambda a: a.start_coin_dice())


def _handle_magic_8_ball(app, response: str) -> None:
    """Answer a Magic 8-Ball question."""
    question = response.strip()
    if not question:
        app.speak(dlg.pick_line(game_lines.MAGIC_8_BALL_INVALID_LINES))
        app.speak(dlg.MAGIC_8_BALL_QUESTION, 45, True)
        return
    answer = pick_8ball_answer()
    line = dlg.pick_line(game_lines.MAGIC_8_BALL_ANSWER_LINES).format(
        question=question,
        answer=answer,
    )
    _offer_play_again(app, line, lambda a: a.start_magic_8_ball())


def _handle_true_false(app, response: str) -> None:
    """Check a true-or-false answer and continue or end the round."""
    if response not in (dlg.BUTTON_TRUE, dlg.BUTTON_FALSE):
        return
    question = getattr(app, "_trivia_current", None)
    if question is None:
        return

    player_said_true = response == dlg.BUTTON_TRUE
    correct = check_answer(question, player_said_true)
    if correct:
        app._trivia_score = getattr(app, "_trivia_score", 0) + 1
        feedback = dlg.pick_line(game_lines.TRIVIA_CORRECT_LINES)
    else:
        correct_label = "true" if question.answer else "false"
        feedback = dlg.pick_line(game_lines.TRIVIA_WRONG_LINES).format(correct=correct_label)

    app._trivia_round = getattr(app, "_trivia_round", 0) + 1
    app._trivia_current = None

    if app._trivia_round >= ROUND_SIZE:
        line = dlg.pick_line(game_lines.TRIVIA_ROUND_END_LINES).format(
            score=app._trivia_score,
            total=ROUND_SIZE,
        )
        _offer_play_again(app, line, lambda a: a.start_true_false())
        return

    app.speak(feedback, 45, False)
    app._ask_next_trivia()


def _handle_rps(app, response: str) -> None:
    """Resolve a rock-paper-scissors round."""
    if response not in MOVES:
        return
    kinito_move = random.choice(MOVES)
    outcome = rps_winner(response, kinito_move)
    fmt = {
        "player_move": response.lower(),
        "kinito_move": kinito_move.lower(),
    }
    if outcome == "player":
        line = dlg.pick_line(game_lines.RPS_WIN_LINES).format(**fmt)
    elif outcome == "kinito":
        line = dlg.pick_line(game_lines.RPS_LOSE_LINES).format(**fmt)
    else:
        line = dlg.pick_line(game_lines.RPS_DRAW_LINES).format(**fmt)
    app.speak(line)


def _handle_number_guess(app, response: str) -> None:
    """Process a number-guess attempt."""
    target = getattr(app, "_number_guess_target", None)
    if target is None:
        return

    guess = parse_guess(response)
    if guess is None or not is_valid_guess(guess):
        app.speak(dlg.pick_line(game_lines.NUMBER_GUESS_INVALID_LINES))
        app.speak(dlg.NUMBER_GUESS_QUESTION, 45, True)
        return

    app._number_guess_attempts = getattr(app, "_number_guess_attempts", 0) + 1
    result = compare_guess(guess, target)

    if result == "correct":
        attempts = app._number_guess_attempts
        app._number_guess_target = None
        line = dlg.pick_line(game_lines.NUMBER_GUESS_WIN_LINES).format(
            answer=target,
            attempts=attempts,
        )
        app.speak(line)
        return

    if app._number_guess_attempts >= MAX_ATTEMPTS:
        app._number_guess_target = None
        line = dlg.pick_line(game_lines.NUMBER_GUESS_GIVE_UP_LINES).format(answer=target)
        app.speak(line)
        return

    if result == "higher":
        hint = dlg.pick_line(game_lines.NUMBER_GUESS_HIGHER_LINES)
    else:
        hint = dlg.pick_line(game_lines.NUMBER_GUESS_LOWER_LINES)
    app.speak(hint, 45, True)


# --- Registry (order matters: more specific markers first) ---

DIALOG_SPECS: tuple[DialogSpec, ...] = (
    DialogSpec(
        dlg.MENU_PROMPT,
        DialogUI("buttons"),
        _handle_menu,
    ),
    DialogSpec(
        credits.CREDITS_MARKER,
        DialogUI(
            "buttons",
            buttons=(
                dlg.BUTTON_CREDITS_STEAM,
                dlg.BUTTON_CREDITS_GITHUB,
            ),
        ),
        _handle_credits,
    ),
    DialogSpec(
        dlg.QUICK_GAMES_MARKER,
        DialogUI(
            "buttons",
            buttons=(
                dlg.BUTTON_GAME_RPS,
                dlg.BUTTON_GAME_NUMBER_GUESS,
                dlg.BUTTON_GAME_COIN_DICE,
                dlg.BUTTON_GAME_MAGIC_8_BALL,
                dlg.BUTTON_GAME_TRUE_FALSE,
                dlg.BUTTON_BACK,
            ),
        ),
        _handle_quick_games,
    ),
    DialogSpec(
        dlg.BOARD_GAMES_MARKER,
        DialogUI(
            "buttons",
            buttons=(
                dlg.BUTTON_GAME_TIC_TAC_TOE,
                dlg.BUTTON_GAME_MEMORY,
                dlg.BUTTON_GAME_BATTLESHIPS,
                dlg.BUTTON_BACK,
            ),
        ),
        _handle_board_games,
    ),
    DialogSpec(
        dlg.GAME_PLAY_AGAIN_MARKER,
        DialogUI(
            "buttons",
            buttons=(dlg.BUTTON_PLAY_AGAIN, dlg.BUTTON_BACK),
        ),
        _handle_play_again,
    ),
    DialogSpec(
        dlg.COIN_DICE_MARKER,
        DialogUI(
            "buttons",
            buttons=(dlg.BUTTON_FLIP_COIN, dlg.BUTTON_ROLL_DICE),
        ),
        _handle_coin_dice_mode,
    ),
    DialogSpec(
        dlg.COIN_FLIP_MARKER,
        DialogUI(
            "buttons",
            buttons=(dlg.BUTTON_HEADS, dlg.BUTTON_TAILS),
        ),
        _handle_coin_flip,
    ),
    DialogSpec(
        dlg.DICE_GUESS_MARKER,
        DialogUI(
            "buttons",
            buttons=dlg.DICE_CHOICES,
        ),
        _handle_dice_guess,
    ),
    DialogSpec(
        dlg.MAGIC_8_BALL_MARKER,
        DialogUI("textbox", textbox_prompt=dlg.MAGIC_8_BALL_QUESTION),
        _handle_magic_8_ball,
    ),
    DialogSpec(
        dlg.TRUE_FALSE_MARKER,
        DialogUI(
            "buttons",
            buttons=(dlg.BUTTON_TRUE, dlg.BUTTON_FALSE),
        ),
        _handle_true_false,
    ),
    DialogSpec(
        dlg.GAME_PICKER_MARKER,
        DialogUI(
            "buttons",
            buttons=(
                dlg.BUTTON_QUICK_GAMES,
                dlg.BUTTON_BOARD_GAMES,
            ),
        ),
        _handle_game_picker,
    ),
    DialogSpec(
        dlg.RPS_MARKER,
        DialogUI(
            "buttons",
            buttons=(dlg.BUTTON_ROCK, dlg.BUTTON_PAPER, dlg.BUTTON_SCISSORS),
        ),
        _handle_rps,
    ),
    DialogSpec(
        dlg.NUMBER_GUESS_MARKER,
        DialogUI("textbox", textbox_prompt=dlg.NUMBER_GUESS_QUESTION),
        _handle_number_guess,
    ),
    DialogSpec(
        dlg.REMINDER_MINUTES_PROMPT,
        DialogUI("textbox", textbox_prompt=dlg.REMINDER_MINUTES_PROMPT),
        _handle_reminder,
    ),
    DialogSpec(
        dlg.REMINDER_MANAGE_PROMPT,
        DialogUI(
            "buttons",
            buttons=(dlg.BUTTON_ADJUST_REMINDER, dlg.BUTTON_CANCEL_REMINDER),
        ),
        _handle_reminder_manage,
    ),
    DialogSpec(
        dlg.REMINDER_ADJUST_PROMPT,
        DialogUI("textbox", textbox_prompt=dlg.REMINDER_ADJUST_PROMPT),
        _handle_reminder_adjust,
    ),
    # Browser category before browser question (both use distinct markers)
    DialogSpec(
        dlg.BROWSER_CATEGORY_MARKER,
        DialogUI(
            "buttons",
            buttons=(
                dlg.BUTTON_CATEGORY_ANIMALS,
                dlg.BUTTON_CATEGORY_KNOWLEDGE,
                dlg.BUTTON_CATEGORY_GAMES,
                dlg.BUTTON_CATEGORY_HORROR,
                dlg.BUTTON_CATEGORY_RANDOM,
            ),
        ),
        _handle_browser_category,
    ),
    DialogSpec(
        dlg.MUSIC_PLAYER_PICK_MARKER,
        DialogUI(
            "buttons",
            buttons=(dlg.BUTTON_PICK_SONG, dlg.BUTTON_CATEGORY_RANDOM, dlg.BUTTON_NOT_NOW),
        ),
        _handle_music_pick,
    ),
    DialogSpec(
        dlg.MUSIC_MANAGE_PROMPT,
        DialogUI(
            "buttons",
            buttons=(
                dlg.BUTTON_STOP_MUSIC,
                dlg.BUTTON_CHANGE_SONG,
                dlg.BUTTON_CATEGORY_RANDOM,
            ),
        ),
        _handle_music_manage,
    ),
    DialogSpec(
        dlg.STORY_QUESTION_MARKER,
        DialogUI("buttons", buttons=(dlg.BUTTON_SURE, dlg.BUTTON_NOT_NOW)),
        _handle_story,
    ),
    DialogSpec(
        dlg.DAY_QUESTION,
        DialogUI("buttons", buttons=(dlg.BUTTON_GOOD, dlg.BUTTON_BAD)),
        _good_bad(dlg.DAY_GOOD_LINES, dlg.DAY_BAD_LINES),
    ),
    DialogSpec(
        dlg.COLOR_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.COLOR_QUESTION),
        _text_format(dlg.COLOR_RESPONSES),
    ),
    DialogSpec(
        dlg.PROGRAMMING_QUESTION,
        DialogUI("buttons", buttons=(dlg.BUTTON_YES, dlg.BUTTON_NO)),
        _yes_no_lines(dlg.PROGRAMMING_YES_LINES, dlg.PROGRAMMING_NO_LINES),
    ),
    DialogSpec(
        dlg.HOBBY_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.HOBBY_QUESTION),
        _text_format(dlg.HOBBY_RESPONSES),
    ),
    DialogSpec(
        dlg.GAME_QUESTION,
        DialogUI("buttons", buttons=(dlg.BUTTON_OKAY, dlg.BUTTON_NOT_NOW)),
        _okay_not_now(lambda a: a.offer_game_picker(), dlg.GAME_DECLINED_LINES),
    ),
    DialogSpec(
        dlg.IMAGE_QUESTION,
        DialogUI("buttons", buttons=(dlg.BUTTON_OKAY, dlg.BUTTON_NOT_NOW)),
        _okay_not_now(
            lambda a: a.show_image(),
            dlg.IMAGE_BUSY_LINES,
            minimize_count=8,
            speak_pitch=20,
        ),
    ),
    DialogSpec(
        dlg.FOOD_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.FOOD_QUESTION),
        _text_format(dlg.FOOD_RESPONSES),
    ),
    DialogSpec(
        dlg.POEM_QUESTION,
        DialogUI("buttons", buttons=(dlg.BUTTON_YES, dlg.BUTTON_POEM_REJECT)),
        _handle_poem,
    ),
    DialogSpec(
        dlg.FUN_FACT_QUESTION,
        DialogUI("buttons", buttons=(dlg.BUTTON_SURE, dlg.BUTTON_NOT_NOW)),
        _sure_decline(lambda a: a.say_random_fact(), dlg.FACT_DECLINED_LINES),
    ),
    DialogSpec(
        dlg.CAMERA_QUESTION_MARKER,
        DialogUI("buttons", buttons=(dlg.BUTTON_YES, dlg.BUTTON_NO)),
        _yes_no(lambda a: a.root.after(0, a.open_camera), dlg.CAMERA_DECLINED_LINES),
    ),
    DialogSpec(
        dlg.BROWSER_QUESTION_MARKER,
        DialogUI("buttons", buttons=(dlg.BUTTON_YES, dlg.BUTTON_NO)),
        _yes_no(lambda a: a.ask_browser_category(), dlg.BROWSER_DECLINED_LINES),
    ),
    DialogSpec(
        dlg.MUSIC_PLAYER_QUESTION_MARKER,
        DialogUI("buttons", buttons=(dlg.BUTTON_YES, dlg.BUTTON_NO)),
        _yes_no(lambda a: a.ask_music_player_pick(), dlg.MUSIC_PLAYER_DECLINED_LINES),
    ),
    DialogSpec(
        dlg.HUG_QUESTION_MARKER,
        DialogUI("buttons", buttons=(dlg.BUTTON_YES, dlg.BUTTON_NO)),
        _yes_no(lambda a: a.give_hug(), dlg.HUG_DECLINED_LINES),
    ),
    DialogSpec(
        dlg.TRUST_QUESTION,
        DialogUI("buttons", buttons=(dlg.BUTTON_YES, dlg.BUTTON_NO)),
        _yes_no_lines(dlg.TRUST_YES_LINES, dlg.TRUST_NO_LINES),
    ),
    DialogSpec(
        dlg.SEASON_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.SEASON_QUESTION),
        _text_format(dlg.SEASON_RESPONSES),
    ),
    DialogSpec(
        dlg.PET_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.PET_QUESTION),
        _text_format(dlg.PET_RESPONSES),
    ),
    DialogSpec(
        dlg.SLEEP_QUESTION,
        DialogUI("buttons", buttons=(dlg.BUTTON_YES, dlg.BUTTON_NO)),
        _yes_no_lines(dlg.SLEEP_YES_LINES, dlg.SLEEP_NO_LINES),
    ),
    DialogSpec(
        dlg.NAME_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.NAME_QUESTION),
        _text_format(dlg.NAME_RESPONSES),
    ),
    DialogSpec(
        dlg.BORED_QUESTION,
        DialogUI("buttons", buttons=(dlg.BUTTON_YES, dlg.BUTTON_NO)),
        _yes_no_lines(dlg.BORED_YES_LINES, dlg.BORED_NO_LINES),
    ),
    DialogSpec(
        dlg.MUSIC_QUESTION,
        DialogUI("buttons", buttons=(dlg.BUTTON_YES, dlg.BUTTON_NO)),
        _yes_no_lines(dlg.MUSIC_YES_LINES, dlg.MUSIC_NO_LINES),
    ),
    DialogSpec(
        dlg.BOOK_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.BOOK_QUESTION),
        _text_format(dlg.BOOK_RESPONSES),
    ),
    DialogSpec(
        dlg.COFFEE_QUESTION,
        DialogUI("buttons", buttons=(dlg.BUTTON_YES, dlg.BUTTON_NO)),
        _yes_no_lines(dlg.COFFEE_YES_LINES, dlg.COFFEE_NO_LINES),
    ),
    DialogSpec(
        dlg.DRINK_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.DRINK_QUESTION),
        _text_format(dlg.DRINK_RESPONSES),
    ),
    DialogSpec(
        dlg.JOKE_QUESTION,
        DialogUI("buttons", buttons=(dlg.BUTTON_SURE, dlg.BUTTON_NOT_NOW)),
        _sure_decline(lambda a: a.say_random_joke(), dlg.JOKE_DECLINED_LINES),
    ),
    DialogSpec(
        dlg.MOVIE_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.MOVIE_QUESTION),
        _text_format(dlg.MOVIE_RESPONSES),
    ),
    DialogSpec(
        dlg.SNACK_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.SNACK_QUESTION),
        _text_format(dlg.SNACK_RESPONSES),
    ),
    DialogSpec(
        dlg.WEATHER_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.WEATHER_QUESTION),
        _text_format(dlg.WEATHER_RESPONSES),
    ),
    DialogSpec(
        dlg.COMPLIMENT_QUESTION,
        DialogUI("buttons", buttons=(dlg.BUTTON_SURE, dlg.BUTTON_NOT_NOW)),
        _sure_decline(lambda a: a.say_random_compliment(), dlg.COMPLIMENT_DECLINED_LINES),
    ),
    DialogSpec(
        dlg.LONELY_QUESTION,
        DialogUI("buttons", buttons=(dlg.BUTTON_YES, dlg.BUTTON_NO)),
        _yes_no_lines(dlg.LONELY_YES_LINES, dlg.LONELY_NO_LINES),
    ),
)
