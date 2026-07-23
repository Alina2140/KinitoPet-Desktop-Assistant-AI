from unittest.mock import MagicMock, patch

import pytest

from content import dialogue as dlg
from kinito.speech import SpeechMixin
from kinito.tts_text import normalize_text_for_tts


class SpeechStub(SpeechMixin):
    def __init__(self):
        self._speech_epoch = 0
        self._awaiting_response = False


@pytest.fixture
def speech():
    return SpeechStub()


@pytest.mark.parametrize(
    "text,expected",
    [
        ("", 1500),
        ("x" * 10, 1500),
        ("x" * 100, 1500),
    ],
)
def test_bubble_close_delay_short(speech, text, expected):
    assert speech._bubble_close_delay_after_tts(text) == expected


def test_bubble_style_uses_game_colors(speech):
    assert speech.BUBBLE_BG == "#FFF8E7"
    assert speech.BUBBLE_BORDER == "#000000"


def test_update_bubble_tail_redraws_shell(speech):
    speech.speech_bubble = MagicMock()
    speech.speech_bubble.winfo_exists.return_value = True
    speech.speech_bubble.winfo_rootx.return_value = 100
    speech.root = MagicMock()
    speech.root.winfo_rootx.return_value = 180
    speech.root.winfo_rooty.return_value = 400
    speech.root.winfo_width.return_value = 120
    speech._speech_bubble_body = MagicMock()
    speech._speech_bubble_body.winfo_reqwidth.return_value = 120
    speech._speech_bubble_body.winfo_reqheight.return_value = 40
    speech._speech_bubble_canvas = MagicMock()
    speech._speech_bubble_body_window = 1
    speech._redraw_bubble_shell = MagicMock()

    speech._update_bubble_tail()

    speech._redraw_bubble_shell.assert_called_once()


def test_bubble_button_style_matches_bubble_palette(speech):
    options = speech._bubble_button_options()
    assert options["bg"] == speech.BUBBLE_BTN_BG
    assert options["fg"] == speech.BUBBLE_FG
    assert options["chamfer"] == speech.BUBBLE_BTN_CHAMFER
    assert speech.BUBBLE_BTN_BG != speech.BUBBLE_BG
    assert speech.BUBBLE_ENTRY_BG.lower() != speech.BUBBLE_TRANSPARENT_BG.lower()


def test_show_response_textbox_uses_bubble_body(speech):
    from unittest.mock import MagicMock

    speech._has_active_speech_bubble = MagicMock(return_value=True)
    speech._speech_bubble_body = MagicMock()
    speech._speech_bubble_body.winfo_exists.return_value = True
    speech._add_textbox_row = MagicMock()
    speech._fit_speech_bubble_to_content = MagicMock()
    speech._schedule_speech_bubble_position = MagicMock()
    speech._speech_bubble_reveal_delay_ms = MagicMock(return_value=0)
    speech.root = MagicMock()

    speech.show_response_textbox("Answer:")

    speech._add_textbox_row.assert_called_once_with(speech._speech_bubble_body, "Answer:")
    speech.root.after.assert_called_once()


def test_bubble_tail_aims_at_kinito_when_bubble_is_offset(speech):
    speech.speech_bubble = MagicMock()
    speech.speech_bubble.winfo_exists.return_value = True
    speech.speech_bubble.winfo_rootx.return_value = 0
    speech.root = MagicMock()
    speech.root.winfo_rootx.return_value = 300
    speech.root.winfo_rooty.return_value = 400
    speech.root.winfo_width.return_value = 100
    speech.img_normal = MagicMock(width=100)

    center_x = speech._bubble_tail_center_x(200)

    assert center_x == 188


def test_position_speech_bubble_uses_tracked_kinito_coords_while_dragging(speech):
    speech.is_dragging = True
    speech.root = MagicMock()
    speech.root.winfo_rootx.return_value = 50
    speech.root.winfo_rooty.return_value = 60
    speech.x = 500
    speech.y = 300
    speech.speech_bubble = MagicMock()
    speech.speech_bubble.winfo_exists.return_value = True
    speech.speech_bubble.winfo_width.return_value = 120
    speech.speech_bubble.winfo_height.return_value = 80
    speech.speech_bubble.winfo_reqwidth.return_value = 120
    speech.speech_bubble.winfo_reqheight.return_value = 80
    speech.root.winfo_width.return_value = 100
    speech.img_normal = MagicMock(width=100)
    speech.get_screen_bounds = MagicMock(return_value=(0, 0, 2000, 2000))
    speech._update_bubble_tail = MagicMock()

    speech.position_speech_bubble()

    speech.speech_bubble.geometry.assert_called_once_with("120x80+490+190")


def test_position_speech_bubble_prefers_live_window_coords(speech):
    speech.is_dragging = False
    speech.moving = False
    speech.root = MagicMock()
    speech.root.winfo_rootx.return_value = 800
    speech.root.winfo_rooty.return_value = 400
    speech.x = 100
    speech.y = 100
    speech.speech_bubble = MagicMock()
    speech.speech_bubble.winfo_exists.return_value = True
    speech.speech_bubble.winfo_width.return_value = 120
    speech.speech_bubble.winfo_height.return_value = 80
    speech.speech_bubble.winfo_reqwidth.return_value = 120
    speech.speech_bubble.winfo_reqheight.return_value = 80
    speech.root.winfo_width.return_value = 100
    speech.img_normal = MagicMock(width=100)
    speech.get_screen_bounds = MagicMock(return_value=(0, 0, 2000, 2000))
    speech._update_bubble_tail = MagicMock()

    speech.position_speech_bubble()

    speech.speech_bubble.geometry.assert_called_once_with("120x80+790+290")


def test_fit_speech_bubble_to_content_preserves_screen_position(speech):
    speech.speech_bubble = MagicMock()
    speech.speech_bubble.winfo_exists.return_value = True
    speech.speech_bubble.winfo_reqwidth.return_value = 360
    speech.speech_bubble.winfo_reqheight.return_value = 180
    speech.speech_bubble.winfo_rootx.return_value = 420
    speech.speech_bubble.winfo_rooty.return_value = 210
    speech.speech_bubble.state.return_value = "normal"
    speech._has_active_speech_bubble = MagicMock(return_value=True)
    speech._redraw_bubble_shell = MagicMock()

    speech._fit_speech_bubble_to_content()

    speech.speech_bubble.geometry.assert_called_once_with("360x180+420+210")


def test_move_speech_bubble_with_kinito_uses_drag_offset(speech):
    speech._bubble_kinito_offset_x = 10
    speech._bubble_kinito_offset_y = -200
    speech.speech_bubble = MagicMock()
    speech.speech_bubble.winfo_exists.return_value = True
    speech.speech_bubble.winfo_width.return_value = 120
    speech.speech_bubble.winfo_height.return_value = 80
    speech.speech_bubble.winfo_reqwidth.return_value = 120
    speech.speech_bubble.winfo_reqheight.return_value = 80
    speech.get_screen_bounds = MagicMock(return_value=(0, 0, 2000, 2000))
    speech._update_bubble_tail = MagicMock()

    speech._move_speech_bubble_with_kinito(500, 300)

    speech.speech_bubble.geometry.assert_called_once_with("120x80+510+100")


@pytest.mark.parametrize(
    "text,expected",
    [
        ("", 6500),
        ("x" * 100, 6500),
        ("x" * 500, 21500),
        ("x" * 2000, 46500),
    ],
)
def test_bubble_close_delay_poem(speech, text, expected):
    assert speech._bubble_close_delay_after_tts(text, long_read=True) == expected


def test_run_tts_uses_balcon_when_available(speech):
    speech._available_voices = {"Eddie"}
    process = MagicMock(returncode=0)
    process.communicate.return_value = ("", "")
    with (
        patch("kinito.speech.os.path.isfile", return_value=True),
        patch(
            "kinito.speech.subprocess.Popen",
            return_value=process,
        ) as popen,
    ):
        assert speech._run_tts("Hello") is True
        popen.assert_called_once()
        command = popen.call_args.args[0]
        assert "-i" in command
        assert "-t" not in command
        assert process.communicate.call_args.kwargs["input"] == normalize_text_for_tts("Hello")


def test_run_tts_passes_quoted_text_via_stdin(speech):
    speech._available_voices = {"Eddie"}
    process = MagicMock(returncode=0)
    process.communicate.return_value = ("", "")
    quoted = 'Play "Duck, Duck, Goose" now'
    with (
        patch("kinito.speech.os.path.isfile", return_value=True),
        patch("kinito.speech.subprocess.Popen", return_value=process),
    ):
        assert speech._run_tts(quoted) is True
    assert process.communicate.call_args.kwargs["input"] == normalize_text_for_tts(quoted)


def test_run_tts_falls_back_to_pyttsx3(speech):
    speech._available_voices = set()
    with (
        patch("kinito.speech.os.path.isfile", return_value=False),
        patch.object(speech, "_run_pyttsx3_fallback", return_value=True) as fallback,
    ):
        assert speech._run_tts("Hello") is True
        fallback.assert_called_once_with(normalize_text_for_tts("Hello"))


def test_run_tts_aborts_after_interrupt_without_next_voice(speech):
    """Killed balcon must not retry the same line with another voice."""
    speech._available_voices = {"Eddie", "Peter"}
    speech._speech_epoch = 1
    process = MagicMock(returncode=1)

    def communicate_and_interrupt(*_args, **_kwargs):
        speech._speech_epoch = 2
        return ("", "")

    process.communicate.side_effect = communicate_and_interrupt

    with (
        patch("kinito.speech.os.path.isfile", return_value=True),
        patch(
            "kinito.speech.subprocess.Popen",
            return_value=process,
        ) as popen,
    ):
        assert speech._run_tts("Hello", speech_epoch=1) is False

    popen.assert_called_once()


def test_run_tts_skips_pyttsx3_when_interrupted(speech):
    speech._speech_epoch = 2
    with (
        patch("kinito.speech.os.path.isfile", return_value=False),
        patch.object(speech, "_run_pyttsx3_fallback", return_value=True) as fallback,
    ):
        assert speech._run_tts("Hello", speech_epoch=1) is False
    fallback.assert_not_called()


def test_show_speech_bubble_ignores_stale_epoch(speech):
    speech._speech_epoch = 2
    speech.root = MagicMock()
    speech.play_sfx = MagicMock()
    speech.create_wrapped_label = MagicMock(return_value=MagicMock())
    speech._schedule_speech_bubble_position = MagicMock()

    speech.show_speech_bubble("Hi", speech_epoch=1)

    speech.play_sfx.assert_not_called()
    speech._schedule_speech_bubble_position.assert_not_called()


def test_schedule_speech_bubble_position_waits_before_reveal(speech):
    speech.root = MagicMock()
    speech._reveal_speech_bubble = MagicMock()

    speech._schedule_speech_bubble_position()

    assert speech.root.after.call_count == 2
    first_delay = speech.root.after.call_args_list[0][0][0]
    second_delay = speech.root.after.call_args_list[1][0][0]
    assert first_delay == SpeechMixin.BUBBLE_REVEAL_DELAY_MS
    assert second_delay == SpeechMixin.BUBBLE_REVEAL_DELAY_MS * 2


def test_speak_uses_lock(speech):
    speech._speech_lock = MagicMock()
    speech._speech_lock.__enter__ = MagicMock(return_value=None)
    speech._speech_lock.__exit__ = MagicMock(return_value=False)
    speech.root = MagicMock()
    speech._speech_epoch = 0
    speech._tts_process = None
    with (
        patch.object(speech, "_run_tts") as run_tts,
        patch.object(speech, "interrupt_speech") as interrupt,
    ):
        speech.speak("Hi", show_bubble=False, wait_for_tts=True)
    interrupt.assert_called_once()
    speech._speech_lock.__enter__.assert_called_once()
    run_tts.assert_called_once()


def test_schedule_bubble_close_if_current_ignores_stale_epoch(speech):
    speech._speech_epoch = 2
    speech._active_bubble_epoch = 1
    speech._awaiting_response = False
    speech._schedule_bubble_close = MagicMock()
    speech._has_active_speech_bubble = MagicMock(return_value=True)
    speech._schedule_bubble_close_if_current(1, 1500)
    speech._schedule_bubble_close.assert_not_called()


def test_interrupt_speech_stops_active_tts_and_bumps_epoch(speech):
    speech._speech_epoch = 3
    speech._bubble_close_timer = 42
    speech.talking = True
    speech._cancel_bubble_close_timer = MagicMock()
    speech._stop_active_tts = MagicMock()
    speech._has_active_speech_bubble = MagicMock(return_value=False)

    speech.interrupt_speech()

    speech._stop_active_tts.assert_called_once()
    speech._cancel_bubble_close_timer.assert_called_once()
    assert speech._speech_epoch == 4
    assert speech.talking is False


def test_interrupt_speech_closes_orphan_bubble(speech):
    speech._speech_epoch = 1
    speech._cancel_bubble_close_timer = MagicMock()
    speech._stop_active_tts = MagicMock()
    speech._has_active_speech_bubble = MagicMock(return_value=True)
    speech._close_speech_bubble_impl = MagicMock()
    speech._chat_mode = False
    speech._awaiting_response = False

    speech.interrupt_speech()

    speech._close_speech_bubble_impl.assert_called_once()


def test_interrupt_speech_keeps_interactive_bubble(speech):
    speech._cancel_bubble_close_timer = MagicMock()
    speech._stop_active_tts = MagicMock()
    speech._has_active_speech_bubble = MagicMock(return_value=True)
    speech._close_speech_bubble_impl = MagicMock()
    speech._chat_mode = False
    speech._awaiting_response = True

    speech.interrupt_speech()

    speech._close_speech_bubble_impl.assert_not_called()


def test_interrupt_speech_keeps_chat_bubble(speech):
    speech._cancel_bubble_close_timer = MagicMock()
    speech._stop_active_tts = MagicMock()
    speech._has_active_speech_bubble = MagicMock(return_value=True)
    speech._close_speech_bubble_impl = MagicMock()
    speech._chat_mode = True

    speech.interrupt_speech()

    speech._close_speech_bubble_impl.assert_not_called()


def test_response_buttons_need_close_without_not_now(speech):
    assert speech._response_buttons_need_close([dlg.BUTTON_SURE, dlg.BUTTON_YES]) is True


def test_response_buttons_skip_close_with_not_now(speech):
    assert speech._response_buttons_need_close([dlg.BUTTON_SURE, dlg.BUTTON_NOT_NOW]) is False


def test_response_buttons_skip_close_with_no(speech):
    assert speech._response_buttons_need_close([dlg.BUTTON_YES, dlg.BUTTON_NO]) is False


def test_response_buttons_skip_close_with_poem_reject(speech):
    assert speech._response_buttons_need_close([dlg.BUTTON_YES, dlg.BUTTON_POEM_REJECT]) is False


def test_handle_response_interrupts_before_handler(speech):
    speech.interrupt_speech = MagicMock()
    speech.close_speech_bubble = MagicMock()
    speech.speech_bubble = MagicMock()
    speech.speech_bubble.wm_title.return_value = dlg.MENU_PROMPT
    speech._has_active_speech_bubble = MagicMock(return_value=True)

    with patch("kinito.speech.handle_dialog_response") as handle:
        speech.handle_response(dlg.BUTTON_FUN_FACT)

    speech.interrupt_speech.assert_called_once()
    speech.close_speech_bubble.assert_called_once()
    handle.assert_called_once()


def test_schedule_response_timeout_closes_unanswered_dialog(speech):
    speech._awaiting_response = True
    speech._has_active_speech_bubble = MagicMock(return_value=True)
    speech.close_speech_bubble = MagicMock()
    speech.root = MagicMock()

    speech._schedule_response_timeout()
    speech.root.after.assert_called_once_with(
        SpeechMixin.RESPONSE_TIMEOUT_MS,
        speech.root.after.call_args.args[1],
    )
    generation = speech._response_timeout_generation
    speech._on_response_timeout(generation)

    speech.close_speech_bubble.assert_called_once()


def test_response_timeout_ignores_stale_generation(speech):
    speech._awaiting_response = True
    speech._has_active_speech_bubble = MagicMock(return_value=True)
    speech.close_speech_bubble = MagicMock()
    speech._response_timeout_generation = 2

    speech._on_response_timeout(1)

    speech.close_speech_bubble.assert_not_called()


def test_close_speech_bubble_cancels_response_timeout(speech):
    speech._response_timeout_timer = 99
    speech._response_timeout_generation = 1
    speech.root = MagicMock()
    speech._has_active_speech_bubble = MagicMock(return_value=False)
    speech._stop_active_tts = MagicMock()

    speech._close_speech_bubble_impl()

    speech.root.after_cancel.assert_called_once_with(99)
    assert speech._response_timeout_generation == 2


@pytest.mark.parametrize(
    "text,question,expected",
    [
        ("You are awesome!", None, "talking"),
        ("Want a story?", None, "thinking"),
        ("Hello there.", False, "talking"),
        ("Guess a number!", True, "thinking"),
        (dlg.MENU_PROMPT, None, "thinking"),
    ],
)
def test_infer_talk_sprite_mode(speech, text, question, expected):
    assert speech._infer_talk_sprite_mode(text, question=question) == expected
