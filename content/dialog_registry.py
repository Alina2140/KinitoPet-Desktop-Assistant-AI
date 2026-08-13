"""Central registry for interactive speech-bubble dialogs."""

from __future__ import annotations

import random
import webbrowser
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from content import credits, game_lines
from content import dialogue as dlg
from content.menu_visibility import filter_visible_menu_buttons
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
        if spec.marker == dlg.MENU_PROMPT:
            buttons = menu_options_for(app)
        elif spec.marker == dlg.MODES_MENU_MARKER:
            buttons = modes_options_for(app)
        elif spec.marker == dlg.SETTINGS_MENU_MARKER:
            buttons = settings_options_for(app)
        elif spec.marker == dlg.SETTINGS_TOGGLES_MARKER:
            buttons = settings_toggles_options_for(app)
        elif spec.marker == dlg.ACTIONS_MENU_MARKER:
            buttons = actions_options_for(app)
        else:
            buttons = list(spec.ui.buttons)
        app.show_response_buttons(buttons)
    elif spec.ui.kind == "textbox":
        app.show_response_textbox(spec.ui.textbox_prompt or spec.marker)


def _visible_menu_buttons(app, buttons: list[str]) -> list[str]:
    """Apply the user's menu-button visibility preferences."""
    hidden = getattr(app, "_hidden_menu_buttons", set()) or set()
    return filter_visible_menu_buttons(list(buttons), set(hidden))


def menu_options_for(app) -> list[str]:
    """Return top-level right-click menu labels."""
    paused = getattr(app, "paused", False)
    focus_mode = getattr(app, "_focus_mode", False)
    if paused or focus_mode:
        options: list[str] = []
        if paused:
            options.append(dlg.BUTTON_WAKE_UP)
        if focus_mode:
            options.append(dlg.BUTTON_UNFOCUS)
            if not paused:
                options.append(dlg.BUTTON_SET_FOCUS_TIMER)
        options.append(dlg.BUTTON_SAY_GOODBYE)
        return _visible_menu_buttons(app, options)

    return _visible_menu_buttons(
        app,
        [
            dlg.BUTTON_MODES,
            dlg.BUTTON_SETTINGS,
            dlg.BUTTON_ACTIONS,
            dlg.BUTTON_MOOD,
            dlg.BUTTON_CHAT,
            dlg.BUTTON_SAY_GOODBYE,
        ],
    )


def modes_options_for(app) -> list[str]:
    """Return Modes submenu labels with sleep/focus toggle names."""
    sleep_label = dlg.BUTTON_WAKE_UP if getattr(app, "paused", False) else dlg.BUTTON_SLEEP
    focus_label = dlg.BUTTON_UNFOCUS if getattr(app, "_focus_mode", False) else dlg.BUTTON_FOCUS
    options = [sleep_label, focus_label]
    if getattr(app, "_focus_mode", False) and not getattr(app, "paused", False):
        options.append(dlg.BUTTON_SET_FOCUS_TIMER)
    options.append(dlg.BUTTON_BACK)

    allowed: set[str] = set()
    if getattr(app, "paused", False):
        allowed |= _MODES_SLEEP_BUTTONS
    if getattr(app, "_focus_mode", False):
        allowed |= _MODES_FOCUS_BUTTONS
    if allowed:
        options = [option for option in options if option in allowed]
    return _visible_menu_buttons(app, options)


def settings_options_for(app) -> list[str]:
    """Return top-level Settings submenu labels."""
    return _visible_menu_buttons(
        app,
        [
            dlg.BUTTON_TURN_ON_OFF,
            dlg.BUTTON_TTS_VOLUME,
            dlg.BUTTON_MUSIC_FOLDER,
            dlg.BUTTON_RESET_MOOD,
            dlg.BUTTON_MENU_BUTTONS,
            dlg.BUTTON_REMEMBER,
            dlg.BUTTON_FORGET,
            dlg.BUTTON_SHOW_CREDITS,
            dlg.BUTTON_BACK,
        ],
    )


def settings_toggles_options_for(app) -> list[str]:
    """Return Settings on/off toggle labels showing each feature's current state."""
    screen_effects_label = (
        dlg.BUTTON_SCREEN_EFFECTS_ON
        if getattr(app, "_screen_effects_enabled", True)
        else dlg.BUTTON_SCREEN_EFFECTS_OFF
    )
    reminders_label = (
        dlg.BUTTON_REMINDERS_ON
        if getattr(app, "_ambient_reminders_enabled", True)
        else dlg.BUTTON_REMINDERS_OFF
    )
    app_awareness_label = (
        dlg.BUTTON_APP_AWARENESS_ON
        if getattr(app, "_app_awareness_enabled", True)
        else dlg.BUTTON_APP_AWARENESS_OFF
    )
    screen_comments_label = (
        dlg.BUTTON_SCREEN_COMMENTS_ON
        if getattr(app, "_screen_comments_enabled", True)
        else dlg.BUTTON_SCREEN_COMMENTS_OFF
    )
    paint_recall_label = (
        dlg.BUTTON_PAINT_RECALL_ON
        if getattr(app, "_paint_recall_enabled", True)
        else dlg.BUTTON_PAINT_RECALL_OFF
    )
    snoring_label = (
        dlg.BUTTON_SNORING_ON
        if getattr(app, "_snoring_enabled", True)
        else dlg.BUTTON_SNORING_OFF
    )
    window_play_label = (
        dlg.BUTTON_WINDOW_PLAY_ON
        if getattr(app, "_window_grab_enabled", True)
        else dlg.BUTTON_WINDOW_PLAY_OFF
    )
    tts_label = (
        dlg.BUTTON_TTS_ON
        if getattr(app, "_tts_enabled", True)
        else dlg.BUTTON_TTS_OFF
    )
    emoji_label = (
        dlg.BUTTON_EMOJI_ON
        if getattr(app, "_emoji_picker_enabled", True)
        else dlg.BUTTON_EMOJI_OFF
    )
    special_days_label = (
        dlg.BUTTON_SPECIAL_DAYS_ON
        if getattr(app, "_special_days_enabled", True)
        else dlg.BUTTON_SPECIAL_DAYS_OFF
    )
    mood_system_label = (
        dlg.BUTTON_MOOD_SYSTEM_ON
        if getattr(app, "_mood_system_enabled", True)
        else dlg.BUTTON_MOOD_SYSTEM_OFF
    )
    return _visible_menu_buttons(
        app,
        [
            screen_effects_label,
            reminders_label,
            app_awareness_label,
            screen_comments_label,
            paint_recall_label,
            snoring_label,
            window_play_label,
            tts_label,
            emoji_label,
            special_days_label,
            mood_system_label,
            dlg.BUTTON_BACK,
        ],
    )


def actions_options_for(app) -> list[str]:
    """Return Actions submenu labels."""
    return _visible_menu_buttons(
        app,
        [
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
        ],
    )


_MENU_SLEEP_BUTTONS = frozenset(
    {dlg.BUTTON_WAKE_UP, dlg.BUTTON_UNFOCUS, dlg.BUTTON_SAY_GOODBYE}
)
_MENU_FOCUS_BUTTONS = frozenset(
    {
        dlg.BUTTON_WAKE_UP,
        dlg.BUTTON_UNFOCUS,
        dlg.BUTTON_SET_FOCUS_TIMER,
        dlg.BUTTON_SAY_GOODBYE,
    }
)
_MODES_SLEEP_BUTTONS = frozenset(
    {dlg.BUTTON_WAKE_UP, dlg.BUTTON_UNFOCUS, dlg.BUTTON_BACK}
)
_MODES_FOCUS_BUTTONS = frozenset(
    {
        dlg.BUTTON_WAKE_UP,
        dlg.BUTTON_UNFOCUS,
        dlg.BUTTON_SET_FOCUS_TIMER,
        dlg.BUTTON_BACK,
    }
)


def _open_main_menu(app) -> None:
    """Re-open the top-level right-click menu."""
    app.speak(dlg.MENU_PROMPT, 45, True, allow_in_focus=True)


def _open_modes_menu(app) -> None:
    """Open the Modes submenu."""
    app.speak(dlg.MODES_MENU_QUESTION, 45, True, allow_in_focus=True)


def _open_settings_menu(app) -> None:
    """Open the Settings submenu."""
    app.speak(dlg.SETTINGS_MENU_QUESTION, 45, True)


def _open_settings_toggles_menu(app) -> None:
    """Open the Settings on/off toggles submenu."""
    app.speak(dlg.SETTINGS_TOGGLES_QUESTION, 45, True)


def _open_actions_menu(app) -> None:
    """Open the Actions submenu."""
    app.speak(dlg.ACTIONS_MENU_QUESTION, 45, True)


def handle_dialog_response(app, spec: DialogSpec, response: str) -> None:
    """Dispatch the user's *response* to the spec's handler."""
    if hasattr(app, "note_user_attention"):
        app.note_user_attention()
    spec.handler(app, response)


def _report_game_outcome(app, result: str) -> None:
    """Notify the mood system about a mini-game result when available."""
    if hasattr(app, "on_game_outcome"):
        app.on_game_outcome(result)


# --- Handler factories ---


def _speak_declined(app, lines) -> None:
    """Acknowledge a declined offer with a short spoken line."""
    mood = app.get_mood() if hasattr(app, "get_mood") else None
    intensity = app.get_mood_intensity() if hasattr(app, "get_mood_intensity") else 0.0
    app.speak(dlg.pick_declined_line(lines, mood=mood, intensity=intensity))


def _yes_no(yes_fn: Handler, no_lines) -> Handler:
    """Build a handler that runs *yes_fn* on Yes or speaks *no_lines* on No."""

    def handler(app, response: str) -> None:
        if response == dlg.BUTTON_YES:
            yes_fn(app)
        elif response == dlg.BUTTON_NO:
            _speak_declined(app, no_lines)

    return handler


def _hug_yes_no() -> Handler:
    """Yes/No handler for hug asks; decline can sour Kinito's mood."""

    def handler(app, response: str) -> None:
        if response == dlg.BUTTON_YES:
            app.give_hug()
        elif response == dlg.BUTTON_NO:
            if hasattr(app, "on_hug_declined"):
                app.on_hug_declined()
            _speak_declined(app, dlg.HUG_DECLINED_LINES)

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


def _good_bad_with_mood_memory(good_lines, bad_lines) -> Handler:
    """Like _good_bad, but store mood_today without ask-once (daily cooldown)."""
    return _two_button_with_daily_fact(
        fact_key="mood_today",
        topic="mood_today",
        button_a=dlg.BUTTON_GOOD,
        value_a="good",
        lines_a=good_lines,
        button_b=dlg.BUTTON_BAD,
        value_b="bad",
        lines_b=bad_lines,
    )


def _two_button_with_daily_fact(
    *,
    fact_key: str,
    topic: str,
    button_a: str,
    value_a: str,
    lines_a,
    button_b: str,
    value_b: str,
    lines_b,
) -> Handler:
    """Persist a daily fact from a two-button answer without ask-once."""

    def handler(app, response: str) -> None:
        memory = getattr(app, "_memory", None)
        if response == button_a:
            if memory is not None:
                memory.set_fact(fact_key, value_a)
                memory.mark_topic_asked(topic)
            app.speak(dlg.pick_line(lines_a))
        elif response == button_b:
            if memory is not None:
                memory.set_fact(fact_key, value_b)
                memory.mark_topic_asked(topic)
            app.speak(dlg.pick_line(lines_b))

    return handler


def _text_format_with_daily_memory(
    fact_key: str, topic: str, response_lines
) -> Handler:
    """Persist a daily text answer without ask-once marking."""

    def handler(app, response: str) -> None:
        memory = getattr(app, "_memory", None)
        trimmed = response.strip()
        if memory is not None and trimmed:
            memory.set_fact(fact_key, trimmed)
            memory.mark_topic_asked(topic)
        app.speak(dlg.pick_line(response_lines).format(response=response))

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


def _persist_dialog_answer(app, marker: str, fact_key: str, value: str) -> None:
    """Save a dialog answer to the user's memory store."""
    memory = getattr(app, "_memory", None)
    if memory is None:
        return
    trimmed = value.strip()
    if trimmed:
        memory.set_fact(fact_key, trimmed)
    memory.mark_answered(marker)


def _text_format_with_memory(marker: str, fact_key: str, response_lines) -> Handler:
    """Like _text_format, but persist the user's text answer first."""

    def handler(app, response: str) -> None:
        _persist_dialog_answer(app, marker, fact_key, response)
        app.speak(dlg.pick_line(response_lines).format(response=response))

    return handler


def _yes_no_lines_with_memory(marker: str, fact_key: str, yes_lines, no_lines) -> Handler:
    """Like _yes_no_lines, but persist yes/no as a fact."""

    def handler(app, response: str) -> None:
        if response == dlg.BUTTON_YES:
            _persist_dialog_answer(app, marker, fact_key, "yes")
            app.speak(dlg.pick_line(yes_lines))
        elif response == dlg.BUTTON_NO:
            _persist_dialog_answer(app, marker, fact_key, "no")
            app.speak(dlg.pick_declined_line(no_lines))

    return handler


def _handle_birthday_consent(app, response: str) -> None:
    """Ask for consent first; on yes open the date prompt, on no store decline."""
    from content.birthday import BIRTHDAY_DECLINED

    memory = getattr(app, "_memory", None)
    if response == dlg.BUTTON_NO:
        if memory is not None:
            memory.set_fact("birthday", BIRTHDAY_DECLINED)
            memory.mark_answered(dlg.BIRTHDAY_CONSENT_QUESTION)
        app.speak(dlg.pick_declined_line(dlg.BIRTHDAY_CONSENT_NO_LINES))
        return
    if response == dlg.BUTTON_YES:
        if memory is not None:
            memory.mark_answered(dlg.BIRTHDAY_CONSENT_QUESTION)
        app.speak(dlg.BIRTHDAY_DATE_QUESTION, 45, True)


def _handle_birthday_date(app, response: str) -> None:
    """Parse and store a birthday date, or re-prompt on invalid input."""
    from content.birthday import format_birthday_display, parse_birthday

    parsed = parse_birthday(response)
    if not parsed:
        app.speak(dlg.BIRTHDAY_DATE_RETRY, 45, True)
        return

    memory = getattr(app, "_memory", None)
    if memory is not None:
        memory.set_fact("birthday", parsed)
        memory.mark_answered(dlg.BIRTHDAY_CONSENT_QUESTION)
        memory.mark_answered(dlg.BIRTHDAY_DATE_MARKER)

    display = format_birthday_display(parsed) or response.strip() or parsed
    app.speak(dlg.pick_line(dlg.BIRTHDAY_SAVED_LINES).format(response=display))


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
        dlg.BUTTON_MODES: _open_modes_menu,
        dlg.BUTTON_SETTINGS: _open_settings_menu,
        dlg.BUTTON_ACTIONS: _open_actions_menu,
        dlg.BUTTON_MOOD: lambda a: a.speak_current_mood(),
        dlg.BUTTON_CHAT: lambda a: a.start_chat(),
        dlg.BUTTON_WAKE_UP: lambda a: a.toggle_pause(),
        dlg.BUTTON_UNFOCUS: lambda a: a.toggle_focus(),
        dlg.BUTTON_SET_FOCUS_TIMER: lambda a: a.open_focus_timer_controls(),
        dlg.BUTTON_SAY_GOODBYE: lambda a: a.say_goodbye(),
    }
    action = actions.get(response)
    if action:
        action(app)


def _menu_action_handlers() -> dict[str, Handler]:
    """Shared action map for top-level leftovers and submenu items."""
    return {
        dlg.BUTTON_SET_REMINDER: lambda a: a.speak(dlg.REMINDER_MINUTES_PROMPT, 45, True),
        dlg.BUTTON_SLEEP: lambda a: a.toggle_pause(),
        dlg.BUTTON_WAKE_UP: lambda a: a.toggle_pause(),
        dlg.BUTTON_FOCUS: lambda a: a.toggle_focus(),
        dlg.BUTTON_UNFOCUS: lambda a: a.toggle_focus(),
        dlg.BUTTON_SET_FOCUS_TIMER: lambda a: a.open_focus_timer_controls(),
        dlg.BUTTON_SCREEN_EFFECTS: lambda a: a.toggle_screen_effects(),
        dlg.BUTTON_SCREEN_EFFECTS_ON: lambda a: a.toggle_screen_effects(),
        dlg.BUTTON_SCREEN_EFFECTS_OFF: lambda a: a.toggle_screen_effects(),
        dlg.BUTTON_REMINDERS: lambda a: a.toggle_ambient_reminders(),
        dlg.BUTTON_REMINDERS_ON: lambda a: a.toggle_ambient_reminders(),
        dlg.BUTTON_REMINDERS_OFF: lambda a: a.toggle_ambient_reminders(),
        dlg.BUTTON_APP_AWARENESS: lambda a: a.toggle_app_awareness(),
        dlg.BUTTON_APP_AWARENESS_ON: lambda a: a.toggle_app_awareness(),
        dlg.BUTTON_APP_AWARENESS_OFF: lambda a: a.toggle_app_awareness(),
        dlg.BUTTON_SCREEN_COMMENTS: lambda a: a.toggle_screen_comments(),
        dlg.BUTTON_SCREEN_COMMENTS_ON: lambda a: a.toggle_screen_comments(),
        dlg.BUTTON_SCREEN_COMMENTS_OFF: lambda a: a.toggle_screen_comments(),
        dlg.BUTTON_PAINT_RECALL: lambda a: a.toggle_paint_recall(),
        dlg.BUTTON_PAINT_RECALL_ON: lambda a: a.toggle_paint_recall(),
        dlg.BUTTON_PAINT_RECALL_OFF: lambda a: a.toggle_paint_recall(),
        dlg.BUTTON_SNORING: lambda a: a.toggle_snoring(),
        dlg.BUTTON_SNORING_ON: lambda a: a.toggle_snoring(),
        dlg.BUTTON_SNORING_OFF: lambda a: a.toggle_snoring(),
        dlg.BUTTON_WINDOW_PLAY: lambda a: a.toggle_window_grab(),
        dlg.BUTTON_WINDOW_PLAY_ON: lambda a: a.toggle_window_grab(),
        dlg.BUTTON_WINDOW_PLAY_OFF: lambda a: a.toggle_window_grab(),
        dlg.BUTTON_TTS: lambda a: a.toggle_tts(),
        dlg.BUTTON_TTS_ON: lambda a: a.toggle_tts(),
        dlg.BUTTON_TTS_OFF: lambda a: a.toggle_tts(),
        dlg.BUTTON_TTS_VOLUME: lambda a: a.offer_tts_volume_picker(),
        dlg.BUTTON_MUSIC_FOLDER: lambda a: a.root.after(0, a.choose_music_folder),
        dlg.BUTTON_EMOJI: lambda a: a.toggle_emoji_picker_setting(),
        dlg.BUTTON_EMOJI_ON: lambda a: a.toggle_emoji_picker_setting(),
        dlg.BUTTON_EMOJI_OFF: lambda a: a.toggle_emoji_picker_setting(),
        dlg.BUTTON_SPECIAL_DAYS: lambda a: a.toggle_special_days(),
        dlg.BUTTON_SPECIAL_DAYS_ON: lambda a: a.toggle_special_days(),
        dlg.BUTTON_SPECIAL_DAYS_OFF: lambda a: a.toggle_special_days(),
        dlg.BUTTON_MOOD_SYSTEM: lambda a: a.toggle_mood_system(),
        dlg.BUTTON_MOOD_SYSTEM_ON: lambda a: a.toggle_mood_system(),
        dlg.BUTTON_MOOD_SYSTEM_OFF: lambda a: a.toggle_mood_system(),
        dlg.BUTTON_RESET_MOOD: lambda a: a.reset_mood(),
        dlg.BUTTON_MENU_BUTTONS: lambda a: a.open_menu_button_settings(),
        dlg.BUTTON_TURN_ON_OFF: _open_settings_toggles_menu,
        dlg.BUTTON_SING_SONG: lambda a: a.say_random_poem(),
        dlg.BUTTON_FUN_FACT: lambda a: a.say_random_fact(),
        dlg.BUTTON_REMEMBER: lambda a: a.show_memory_summary(),
        dlg.BUTTON_FORGET: lambda a: a.forget_memory(),
        dlg.BUTTON_VISIT_WEBSITE: lambda a: a.ask_browser_category(),
        dlg.BUTTON_PLAY_MUSIC: lambda a: a.open_music_player(),
        dlg.BUTTON_PLAY_GAME: lambda a: a.offer_game_picker(),
        dlg.BUTTON_PAINT: lambda a: a.offer_paint_picker(),
        dlg.BUTTON_GIVE_HUG: lambda a: a.give_hug(),
        dlg.BUTTON_TELL_TIME: lambda a: a.print_current_datetime(),
        dlg.BUTTON_SHOW_CREDITS: lambda a: a.show_credits(),
        dlg.BUTTON_BACK: _open_main_menu,
    }


def _handle_modes_menu(app, response: str) -> None:
    """Handle Modes submenu selections."""
    if getattr(app, "paused", False) and response not in _MODES_SLEEP_BUTTONS:
        return
    if getattr(app, "_focus_mode", False) and response not in _MODES_FOCUS_BUTTONS:
        return
    action = _menu_action_handlers().get(response)
    if action:
        action(app)


def _handle_settings_menu(app, response: str) -> None:
    """Handle Settings submenu selections."""
    if getattr(app, "paused", False) or getattr(app, "_focus_mode", False):
        return
    action = _menu_action_handlers().get(response)
    if action:
        action(app)


def _handle_settings_toggles_menu(app, response: str) -> None:
    """Handle Settings on/off toggle selections."""
    if getattr(app, "paused", False) or getattr(app, "_focus_mode", False):
        return
    if response == dlg.BUTTON_BACK:
        _open_settings_menu(app)
        return
    action = _menu_action_handlers().get(response)
    if action:
        action(app)


def _handle_actions_menu(app, response: str) -> None:
    """Handle Actions submenu selections."""
    if getattr(app, "paused", False) or getattr(app, "_focus_mode", False):
        return
    action = _menu_action_handlers().get(response)
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


def _handle_focus_timer(app, response: str) -> None:
    """Parse minutes from the focus-timer textbox and start the countdown."""
    app.set_focus_timer(f"{response}")


def _handle_focus_timer_adjust(app, response: str) -> None:
    """Parse minutes from the adjust dialog and restart the focus timer."""
    app.adjust_focus_timer(f"{response}")


def _handle_focus_timer_manage(app, response: str) -> None:
    """Cancel or open the adjust flow for the active focus timer."""
    if response == dlg.BUTTON_CANCEL_FOCUS_TIMER:
        app.cancel_focus_timer()
    elif response == dlg.BUTTON_ADJUST_FOCUS_TIMER:
        app.speak(dlg.FOCUS_TIMER_ADJUST_PROMPT, 45, True, allow_in_focus=True)


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


def _handle_paint_picker(app, response: str) -> None:
    """Open Paint canvas or gallery, or return to Actions."""
    if response == dlg.BUTTON_PAINT_DRAW:
        app.open_paint()
    elif response == dlg.BUTTON_PAINT_GALLERY:
        app.open_paint_gallery()
    elif response == dlg.BUTTON_BACK:
        _open_actions_menu(app)


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


def _handle_trivia_pack(app, response: str) -> None:
    """Start a true-or-false round for the chosen pack, or return to quick games."""
    if response == dlg.BUTTON_BACK:
        app.offer_quick_games()
        return
    from content.trivia_questions import (
        PACK_ANIMALS,
        PACK_KINITO,
        PACK_MIXED,
        PACK_SEASONAL,
        PACK_SPOOKY,
        PACK_TECH,
    )

    pack_map = {
        dlg.BUTTON_TRIVIA_MIXED: PACK_MIXED,
        dlg.BUTTON_TRIVIA_ANIMALS: PACK_ANIMALS,
        dlg.BUTTON_TRIVIA_TECH: PACK_TECH,
        dlg.BUTTON_TRIVIA_SPOOKY: PACK_SPOOKY,
        dlg.BUTTON_TRIVIA_KINITO: PACK_KINITO,
        dlg.BUTTON_TRIVIA_SEASONAL: PACK_SEASONAL,
    }
    pack = pack_map.get(response)
    if pack is not None:
        app.start_true_false_pack(pack)


def _handle_board_games(app, response: str) -> None:
    """Launch a board mini-game or return to the top-level picker."""
    if response == dlg.BUTTON_BACK:
        app.offer_game_picker()
        return
    actions = {
        dlg.BUTTON_GAME_TIC_TAC_TOE: lambda a: a.start_tic_tac_toe(),
        dlg.BUTTON_GAME_MEMORY: lambda a: a.start_memory(),
        dlg.BUTTON_GAME_BATTLESHIPS: lambda a: a.start_battleships(),
        dlg.BUTTON_GAME_SNAKE: lambda a: a.start_snake(),
        dlg.BUTTON_GAME_CONNECT_FOUR: lambda a: a.start_connect_four(),
        dlg.BUTTON_GAME_HANGMAN: lambda a: a.start_hangman(),
        dlg.BUTTON_GAME_MINESWEEPER: lambda a: a.start_minesweeper(),
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


def _handle_tts_volume(app, response: str) -> None:
    """Apply a TTS volume preset from the picker."""
    volume_map = {
        dlg.BUTTON_TTS_VOLUME_SOFT: dlg.TTS_VOLUME_SOFT,
        dlg.BUTTON_TTS_VOLUME_NORMAL: dlg.TTS_VOLUME_NORMAL,
        dlg.BUTTON_TTS_VOLUME_LOUD: dlg.TTS_VOLUME_LOUD,
    }
    if response == dlg.BUTTON_BACK:
        _open_settings_menu(app)
        return
    volume = volume_map.get(response)
    if volume is not None and hasattr(app, "set_tts_volume"):
        app.set_tts_volume(volume)


def _handle_coin_dice_mode(app, response: str) -> None:
    """Choose coin flip or dice roll."""
    if response == dlg.BUTTON_FLIP_COIN:
        app.speak(dlg.COIN_FLIP_QUESTION, 45, True)
    elif response == dlg.BUTTON_ROLL_DICE:
        app.speak(dlg.DICE_GUESS_QUESTION, 45, True)


def _handle_coin_flip(app, response: str) -> None:
    """Resolve a coin-flip guess."""
    from kinito.features.mood import GAME_KINITO_WIN, GAME_PLAYER_WIN

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
        _report_game_outcome(app, GAME_PLAYER_WIN)
    else:
        line = dlg.pick_line(game_lines.COIN_LOSE_LINES).format(**fmt)
        _report_game_outcome(app, GAME_KINITO_WIN)
    _offer_play_again(app, line, lambda a: a.start_coin_dice())


def _handle_dice_guess(app, response: str) -> None:
    """Resolve a dice-guess attempt."""
    from kinito.features.mood import GAME_KINITO_WIN, GAME_PLAYER_WIN

    if response not in dlg.DICE_CHOICES:
        return
    guess = int(response)
    roll = roll_dice()
    fmt = {"guess": guess, "roll": roll}
    if dice_outcome(guess, roll) == "win":
        line = dlg.pick_line(game_lines.DICE_WIN_LINES).format(**fmt)
        _report_game_outcome(app, GAME_PLAYER_WIN)
    else:
        line = dlg.pick_line(game_lines.DICE_LOSE_LINES).format(**fmt)
        _report_game_outcome(app, GAME_KINITO_WIN)
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
    from kinito.features.mood import GAME_KINITO_WIN, GAME_PLAYER_WIN

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
        score = app._trivia_score
        total = ROUND_SIZE
        summary: dict = {"best": score, "streak": 0, "new_best": False}
        scores_fn = getattr(app, "game_scores", None)
        if callable(scores_fn):
            store = scores_fn()
            record = getattr(store, "record_trivia_score", None)
            if callable(record):
                recorded = record(score, total=total)
                if isinstance(recorded, dict):
                    summary = recorded
        fmt = {
            "score": score,
            "total": total,
            "best": summary.get("best", score),
            "streak": summary.get("streak", 0),
        }
        pool = (
            game_lines.TRIVIA_NEW_BEST_LINES
            if summary.get("new_best")
            else game_lines.TRIVIA_ROUND_END_LINES
        )
        line = dlg.pick_line(pool).format(**fmt)
        outcome = GAME_PLAYER_WIN if score >= 3 else GAME_KINITO_WIN
        _report_game_outcome(app, outcome)
        pack = getattr(app, "_trivia_pack", None)
        _offer_play_again(app, line, lambda a, p=pack: a.start_true_false_pack(p))
        return

    app.speak(feedback, 45, False, skip_ai=True)
    app._ask_next_trivia()


def _handle_rps(app, response: str) -> None:
    """Resolve a rock-paper-scissors round."""
    from kinito.features.mood import GAME_DRAW, GAME_KINITO_WIN, GAME_PLAYER_WIN

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
        _report_game_outcome(app, GAME_PLAYER_WIN)
    elif outcome == "kinito":
        line = dlg.pick_line(game_lines.RPS_LOSE_LINES).format(**fmt)
        _report_game_outcome(app, GAME_KINITO_WIN)
    else:
        line = dlg.pick_line(game_lines.RPS_DRAW_LINES).format(**fmt)
        _report_game_outcome(app, GAME_DRAW)
    app.speak(line)


def _handle_number_guess(app, response: str) -> None:
    """Process a number-guess attempt."""
    from kinito.features.mood import GAME_KINITO_WIN, GAME_PLAYER_WIN

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
        is_new_best = False
        best = attempts
        scores_fn = getattr(app, "game_scores", None)
        if callable(scores_fn):
            store = scores_fn()
            record = getattr(store, "record_number_guess_attempts", None)
            get_best = getattr(store, "number_guess_best_attempts", None)
            if callable(record):
                is_new_best = bool(record(attempts))
            if callable(get_best):
                recorded_best = get_best()
                if isinstance(recorded_best, int):
                    best = recorded_best
        fmt = {"answer": target, "attempts": attempts, "best": best}
        pool = (
            game_lines.NUMBER_GUESS_NEW_BEST_LINES
            if is_new_best
            else game_lines.NUMBER_GUESS_WIN_LINES
        )
        line = dlg.pick_line(pool).format(**fmt)
        _report_game_outcome(app, GAME_PLAYER_WIN)
        app.speak(line)
        return

    if app._number_guess_attempts >= MAX_ATTEMPTS:
        app._number_guess_target = None
        line = dlg.pick_line(game_lines.NUMBER_GUESS_GIVE_UP_LINES).format(answer=target)
        _report_game_outcome(app, GAME_KINITO_WIN)
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
        dlg.MODES_MENU_MARKER,
        DialogUI("buttons"),
        _handle_modes_menu,
    ),
    DialogSpec(
        dlg.SETTINGS_MENU_MARKER,
        DialogUI("buttons"),
        _handle_settings_menu,
    ),
    DialogSpec(
        dlg.SETTINGS_TOGGLES_MARKER,
        DialogUI("buttons"),
        _handle_settings_toggles_menu,
    ),
    DialogSpec(
        dlg.TTS_VOLUME_MARKER,
        DialogUI(
            "buttons",
            buttons=(
                dlg.BUTTON_TTS_VOLUME_SOFT,
                dlg.BUTTON_TTS_VOLUME_NORMAL,
                dlg.BUTTON_TTS_VOLUME_LOUD,
                dlg.BUTTON_BACK,
            ),
        ),
        _handle_tts_volume,
    ),
    DialogSpec(
        dlg.ACTIONS_MENU_MARKER,
        DialogUI("buttons"),
        _handle_actions_menu,
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
                dlg.BUTTON_GAME_SNAKE,
                dlg.BUTTON_GAME_CONNECT_FOUR,
                dlg.BUTTON_GAME_HANGMAN,
                dlg.BUTTON_GAME_MINESWEEPER,
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
        dlg.TRIVIA_PACK_MARKER,
        DialogUI(
            "buttons",
            buttons=(
                dlg.BUTTON_TRIVIA_MIXED,
                dlg.BUTTON_TRIVIA_ANIMALS,
                dlg.BUTTON_TRIVIA_TECH,
                dlg.BUTTON_TRIVIA_SPOOKY,
                dlg.BUTTON_TRIVIA_KINITO,
                dlg.BUTTON_TRIVIA_SEASONAL,
                dlg.BUTTON_BACK,
            ),
        ),
        _handle_trivia_pack,
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
        dlg.PAINT_PICKER_MARKER,
        DialogUI(
            "buttons",
            buttons=(
                dlg.BUTTON_PAINT_DRAW,
                dlg.BUTTON_PAINT_GALLERY,
                dlg.BUTTON_BACK,
            ),
        ),
        _handle_paint_picker,
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
        dlg.FOCUS_TIMER_MINUTES_PROMPT,
        DialogUI("textbox", textbox_prompt=dlg.FOCUS_TIMER_MINUTES_PROMPT),
        _handle_focus_timer,
    ),
    DialogSpec(
        dlg.FOCUS_TIMER_MANAGE_PROMPT,
        DialogUI(
            "buttons",
            buttons=(dlg.BUTTON_ADJUST_FOCUS_TIMER, dlg.BUTTON_CANCEL_FOCUS_TIMER),
        ),
        _handle_focus_timer_manage,
    ),
    DialogSpec(
        dlg.FOCUS_TIMER_ADJUST_PROMPT,
        DialogUI("textbox", textbox_prompt=dlg.FOCUS_TIMER_ADJUST_PROMPT),
        _handle_focus_timer_adjust,
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
        dlg.STORY_QUESTION_MARKER,
        DialogUI("buttons", buttons=(dlg.BUTTON_SURE, dlg.BUTTON_NOT_NOW)),
        _handle_story,
    ),
    DialogSpec(
        dlg.DAY_QUESTION,
        DialogUI("buttons", buttons=(dlg.BUTTON_GOOD, dlg.BUTTON_BAD)),
        _good_bad_with_mood_memory(dlg.DAY_GOOD_LINES, dlg.DAY_BAD_LINES),
    ),
    DialogSpec(
        dlg.ENERGY_QUESTION,
        DialogUI("buttons", buttons=(dlg.BUTTON_ENERGETIC, dlg.BUTTON_TIRED)),
        _two_button_with_daily_fact(
            fact_key="energy_today",
            topic="energy_today",
            button_a=dlg.BUTTON_ENERGETIC,
            value_a="high",
            lines_a=dlg.ENERGY_HIGH_LINES,
            button_b=dlg.BUTTON_TIRED,
            value_b="low",
            lines_b=dlg.ENERGY_LOW_LINES,
        ),
    ),
    DialogSpec(
        dlg.FOCUS_QUESTION,
        DialogUI("buttons", buttons=(dlg.BUTTON_BUSY, dlg.BUTTON_CHILL)),
        _two_button_with_daily_fact(
            fact_key="focus_today",
            topic="focus_today",
            button_a=dlg.BUTTON_BUSY,
            value_a="busy",
            lines_a=dlg.FOCUS_BUSY_LINES,
            button_b=dlg.BUTTON_CHILL,
            value_b="chill",
            lines_b=dlg.FOCUS_CHILL_LINES,
        ),
    ),
    DialogSpec(
        dlg.PLANS_TONIGHT_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.PLANS_TONIGHT_QUESTION),
        _text_format_with_daily_memory(
            "plans_tonight", "plans_tonight", dlg.PLANS_TONIGHT_RESPONSES
        ),
    ),
    DialogSpec(
        dlg.COLOR_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.COLOR_QUESTION),
        _text_format_with_memory(dlg.COLOR_QUESTION, "favorite_colors", dlg.COLOR_RESPONSES),
    ),
    DialogSpec(
        dlg.PROGRAMMING_QUESTION,
        DialogUI("buttons", buttons=(dlg.BUTTON_YES, dlg.BUTTON_NO)),
        _yes_no_lines_with_memory(
            dlg.PROGRAMMING_QUESTION,
            "likes_programming",
            dlg.PROGRAMMING_YES_LINES,
            dlg.PROGRAMMING_NO_LINES,
        ),
    ),
    DialogSpec(
        dlg.HOBBY_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.HOBBY_QUESTION),
        _text_format_with_memory(dlg.HOBBY_QUESTION, "hobbies", dlg.HOBBY_RESPONSES),
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
        _text_format_with_memory(dlg.FOOD_QUESTION, "favorite_food", dlg.FOOD_RESPONSES),
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
        _yes_no(lambda a: a.open_music_player(), dlg.MUSIC_PLAYER_DECLINED_LINES),
    ),
    DialogSpec(
        dlg.HUG_QUESTION_MARKER,
        DialogUI("buttons", buttons=(dlg.BUTTON_YES, dlg.BUTTON_NO)),
        _hug_yes_no(),
    ),
    DialogSpec(
        dlg.TRUST_QUESTION,
        DialogUI("buttons", buttons=(dlg.BUTTON_YES, dlg.BUTTON_NO)),
        _yes_no_lines(dlg.TRUST_YES_LINES, dlg.TRUST_NO_LINES),
    ),
    DialogSpec(
        dlg.SEASON_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.SEASON_QUESTION),
        _text_format_with_memory(dlg.SEASON_QUESTION, "favorite_seasons", dlg.SEASON_RESPONSES),
    ),
    DialogSpec(
        dlg.PET_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.PET_QUESTION),
        _text_format_with_memory(dlg.PET_QUESTION, "pets", dlg.PET_RESPONSES),
    ),
    DialogSpec(
        dlg.SLEEP_QUESTION,
        DialogUI("buttons", buttons=(dlg.BUTTON_YES, dlg.BUTTON_NO)),
        _yes_no_lines(dlg.SLEEP_YES_LINES, dlg.SLEEP_NO_LINES),
    ),
    DialogSpec(
        dlg.NAME_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.NAME_QUESTION),
        _text_format_with_memory(dlg.NAME_QUESTION, "user_names", dlg.NAME_RESPONSES),
    ),
    DialogSpec(
        dlg.BORED_QUESTION,
        DialogUI("buttons", buttons=(dlg.BUTTON_YES, dlg.BUTTON_NO)),
        _yes_no_lines(dlg.BORED_YES_LINES, dlg.BORED_NO_LINES),
    ),
    DialogSpec(
        dlg.MUSIC_QUESTION,
        DialogUI("buttons", buttons=(dlg.BUTTON_YES, dlg.BUTTON_NO)),
        _yes_no_lines_with_memory(
            dlg.MUSIC_QUESTION,
            "likes_music",
            dlg.MUSIC_YES_LINES,
            dlg.MUSIC_NO_LINES,
        ),
    ),
    DialogSpec(
        dlg.BOOK_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.BOOK_QUESTION),
        _text_format_with_memory(dlg.BOOK_QUESTION, "favorite_book", dlg.BOOK_RESPONSES),
    ),
    DialogSpec(
        dlg.COFFEE_QUESTION,
        DialogUI("buttons", buttons=(dlg.BUTTON_YES, dlg.BUTTON_NO)),
        _yes_no_lines_with_memory(
            dlg.COFFEE_QUESTION,
            "likes_coffee",
            dlg.COFFEE_YES_LINES,
            dlg.COFFEE_NO_LINES,
        ),
    ),
    DialogSpec(
        dlg.BIRTHDAY_CONSENT_QUESTION,
        DialogUI("buttons", buttons=(dlg.BUTTON_YES, dlg.BUTTON_NO)),
        _handle_birthday_consent,
    ),
    DialogSpec(
        dlg.BIRTHDAY_DATE_MARKER,
        DialogUI("textbox", textbox_prompt=dlg.BIRTHDAY_DATE_QUESTION),
        _handle_birthday_date,
    ),
    DialogSpec(
        dlg.DRINK_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.DRINK_QUESTION),
        _text_format_with_memory(dlg.DRINK_QUESTION, "favorite_drink", dlg.DRINK_RESPONSES),
    ),
    DialogSpec(
        dlg.JOKE_QUESTION,
        DialogUI("buttons", buttons=(dlg.BUTTON_SURE, dlg.BUTTON_NOT_NOW)),
        _sure_decline(lambda a: a.say_random_joke(), dlg.JOKE_DECLINED_LINES),
    ),
    DialogSpec(
        dlg.MOVIE_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.MOVIE_QUESTION),
        _text_format_with_memory(dlg.MOVIE_QUESTION, "favorite_movie", dlg.MOVIE_RESPONSES),
    ),
    DialogSpec(
        dlg.JOB_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.JOB_QUESTION),
        _text_format_with_memory(dlg.JOB_QUESTION, "job", dlg.JOB_RESPONSES),
    ),
    DialogSpec(
        dlg.FAVORITE_GAME_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.FAVORITE_GAME_QUESTION),
        _text_format_with_memory(
            dlg.FAVORITE_GAME_QUESTION, "favorite_game", dlg.FAVORITE_GAME_RESPONSES
        ),
    ),
    DialogSpec(
        dlg.BEDTIME_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.BEDTIME_QUESTION),
        _text_format_with_memory(dlg.BEDTIME_QUESTION, "bedtime", dlg.BEDTIME_RESPONSES),
    ),
    DialogSpec(
        dlg.SHOW_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.SHOW_QUESTION),
        _text_format_with_memory(dlg.SHOW_QUESTION, "favorite_show", dlg.SHOW_RESPONSES),
    ),
    DialogSpec(
        dlg.ARTIST_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.ARTIST_QUESTION),
        _text_format_with_memory(dlg.ARTIST_QUESTION, "favorite_artist", dlg.ARTIST_RESPONSES),
    ),
    DialogSpec(
        dlg.ANIMAL_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.ANIMAL_QUESTION),
        _text_format_with_memory(dlg.ANIMAL_QUESTION, "favorite_animal", dlg.ANIMAL_RESPONSES),
    ),
    DialogSpec(
        dlg.COMFORT_FOOD_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.COMFORT_FOOD_QUESTION),
        _text_format_with_memory(
            dlg.COMFORT_FOOD_QUESTION, "comfort_food", dlg.COMFORT_FOOD_RESPONSES
        ),
    ),
    DialogSpec(
        dlg.DREAM_DESTINATION_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.DREAM_DESTINATION_QUESTION),
        _text_format_with_memory(
            dlg.DREAM_DESTINATION_QUESTION,
            "dream_destination",
            dlg.DREAM_DESTINATION_RESPONSES,
        ),
    ),
    DialogSpec(
        dlg.FAVORITE_APP_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.FAVORITE_APP_QUESTION),
        _text_format_with_memory(
            dlg.FAVORITE_APP_QUESTION, "favorite_app", dlg.FAVORITE_APP_RESPONSES
        ),
    ),
    DialogSpec(
        dlg.MORNING_DRINK_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.MORNING_DRINK_QUESTION),
        _text_format_with_memory(
            dlg.MORNING_DRINK_QUESTION, "morning_drink", dlg.MORNING_DRINK_RESPONSES
        ),
    ),
    DialogSpec(
        dlg.WAKE_TIME_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.WAKE_TIME_QUESTION),
        _text_format_with_memory(dlg.WAKE_TIME_QUESTION, "wake_time", dlg.WAKE_TIME_RESPONSES),
    ),
    DialogSpec(
        dlg.CITY_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.CITY_QUESTION),
        _text_format_with_memory(dlg.CITY_QUESTION, "home_city", dlg.CITY_RESPONSES),
    ),
    DialogSpec(
        dlg.CHRONOTYPE_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.CHRONOTYPE_QUESTION),
        _text_format_with_memory(
            dlg.CHRONOTYPE_QUESTION, "chronotype", dlg.CHRONOTYPE_RESPONSES
        ),
    ),
    DialogSpec(
        dlg.LANGUAGES_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.LANGUAGES_QUESTION),
        _text_format_with_memory(dlg.LANGUAGES_QUESTION, "languages", dlg.LANGUAGES_RESPONSES),
    ),
    DialogSpec(
        dlg.RAIN_QUESTION,
        DialogUI("buttons", buttons=(dlg.BUTTON_YES, dlg.BUTTON_NO)),
        _yes_no_lines_with_memory(
            dlg.RAIN_QUESTION,
            "likes_rain",
            dlg.RAIN_YES_LINES,
            dlg.RAIN_NO_LINES,
        ),
    ),
    DialogSpec(
        dlg.HORROR_QUESTION,
        DialogUI("buttons", buttons=(dlg.BUTTON_YES, dlg.BUTTON_NO)),
        _yes_no_lines_with_memory(
            dlg.HORROR_QUESTION,
            "likes_horror",
            dlg.HORROR_YES_LINES,
            dlg.HORROR_NO_LINES,
        ),
    ),
    DialogSpec(
        dlg.SPICY_QUESTION,
        DialogUI("buttons", buttons=(dlg.BUTTON_YES, dlg.BUTTON_NO)),
        _yes_no_lines_with_memory(
            dlg.SPICY_QUESTION,
            "likes_spicy_food",
            dlg.SPICY_YES_LINES,
            dlg.SPICY_NO_LINES,
        ),
    ),
    DialogSpec(
        dlg.LATE_NIGHT_QUESTION,
        DialogUI("buttons", buttons=(dlg.BUTTON_YES, dlg.BUTTON_NO)),
        _yes_no_lines_with_memory(
            dlg.LATE_NIGHT_QUESTION,
            "likes_staying_up_late",
            dlg.LATE_NIGHT_YES_LINES,
            dlg.LATE_NIGHT_NO_LINES,
        ),
    ),
    DialogSpec(
        dlg.PARTNER_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.PARTNER_QUESTION),
        _text_format_with_memory(dlg.PARTNER_QUESTION, "partner_status", dlg.PARTNER_RESPONSES),
    ),
    DialogSpec(
        dlg.SIBLINGS_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.SIBLINGS_QUESTION),
        _text_format_with_memory(dlg.SIBLINGS_QUESTION, "siblings", dlg.SIBLINGS_RESPONSES),
    ),
    DialogSpec(
        dlg.BEST_FRIEND_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.BEST_FRIEND_QUESTION),
        _text_format_with_memory(
            dlg.BEST_FRIEND_QUESTION, "important_person", dlg.BEST_FRIEND_RESPONSES
        ),
    ),
    DialogSpec(
        dlg.PRONOUNS_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.PRONOUNS_QUESTION),
        _text_format_with_memory(dlg.PRONOUNS_QUESTION, "pronouns", dlg.PRONOUNS_RESPONSES),
    ),
    DialogSpec(
        dlg.SNACK_QUESTION,
        DialogUI("textbox", textbox_prompt=dlg.SNACK_QUESTION),
        _text_format_with_memory(dlg.SNACK_QUESTION, "favorite_snacks", dlg.SNACK_RESPONSES),
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
