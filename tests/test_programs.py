from unittest.mock import MagicMock, patch

import pytest

from kinito.features.programs import ProgramsMixin


class ProgramsStub(ProgramsMixin):
    pass


@pytest.fixture
def programs():
    stub = ProgramsStub()
    stub.speak = MagicMock()
    stub.speak_random_question = MagicMock()
    stub._running = True
    stub._reminder_id = 0
    stub._focus_mode = False
    stub._focus_timer_id = 0
    stub.root = MagicMock()
    stub.root.winfo_exists.return_value = True
    stub.play_mp3 = MagicMock()
    stub.play_sfx = MagicMock()
    stub._reminder_countdown_btn = MagicMock()
    stub._reminder_countdown_btn.winfo_ismapped.return_value = False
    stub._reminder_end_at = None
    stub._focus_timer_countdown_btn = MagicMock()
    stub._focus_timer_countdown_btn.winfo_ismapped.return_value = False
    stub._focus_timer_end_at = None
    return stub


def test_set_reminder_invalid_input(programs):
    programs.set_reminder("no digits here")
    programs.speak.assert_called_once()


def test_set_reminder_starts_countdown(programs):
    with patch.object(programs, "_start_reminder") as start:
        programs.set_reminder("about 5 minutes please")
    start.assert_called_once_with(5 * 60)
    programs.speak.assert_called_once()


def test_format_reminder_countdown():
    assert ProgramsMixin.format_reminder_countdown(125) == "2:05"
    assert ProgramsMixin.format_reminder_countdown(3661) == "1:01:01"


def test_cancel_reminder_clears_timer(programs):
    programs._reminder_end_at = 999999.0
    with patch.object(programs, "_clear_reminder") as clear:
        programs.cancel_reminder()
    clear.assert_called_once()
    programs.speak.assert_called_once()


def test_adjust_reminder_restarts_timer(programs):
    with patch.object(programs, "_start_reminder") as start:
        programs.adjust_reminder("10")
    start.assert_called_once_with(10 * 60)


def test_launch_shortcut_returns_false_on_error(programs):
    with patch("kinito.features.programs.os.startfile", side_effect=OSError):
        assert programs._launch_shortcut("missing.lnk") is False


def test_show_reminder_countdown_places_below_sprite(programs):
    import time

    programs.panel = MagicMock()
    programs.panel.winfo_height.return_value = 180
    programs.img_normal = MagicMock(height=180)
    programs._window_screen_size = MagicMock(return_value=(120, 180))
    programs.root.winfo_width.return_value = 120
    programs.root.winfo_height.return_value = 180
    programs._reminder_countdown_btn.winfo_reqheight.return_value = 20
    programs._reminder_end_at = time.monotonic() + 300

    programs._show_reminder_countdown_button()

    programs._reminder_countdown_btn.place.assert_called_once()
    place_kwargs = programs._reminder_countdown_btn.place.call_args.kwargs
    assert place_kwargs["y"] == 190
    assert place_kwargs["anchor"] == "n"
    programs.root.geometry.assert_called_once()
    assert programs.root.geometry.call_args.args[0].startswith("120x214+")


def test_minimize_current_window_swallows_failsafe(programs):
    import pyautogui

    with patch(
        "kinito.features.programs.pyautogui.hotkey", side_effect=pyautogui.FailSafeException
    ):
        programs.minimize_current_window()


def test_set_focus_timer_requires_focus_mode(programs):
    programs._focus_mode = False
    with patch.object(programs, "_start_focus_timer") as start:
        programs.set_focus_timer("5")
    start.assert_not_called()


def test_set_focus_timer_starts_countdown(programs):
    programs._focus_mode = True
    with patch.object(programs, "_start_focus_timer") as start:
        programs.set_focus_timer("about 5 minutes please")
    start.assert_called_once_with(5 * 60)
    programs.speak.assert_called_once()
    assert programs.speak.call_args.kwargs.get("allow_in_focus") is True


def test_cancel_focus_timer_clears_timer(programs):
    programs._focus_mode = True
    programs._focus_timer_end_at = 999999.0
    with patch.object(programs, "_clear_focus_timer") as clear:
        programs.cancel_focus_timer()
    clear.assert_called_once()
    programs.speak.assert_called_once()


def test_fire_focus_timer_exits_focus_mode(programs):
    programs._focus_mode = True
    programs._fire_focus_timer()
    assert programs._focus_mode is False
    programs.play_sfx.assert_called_once()
    programs.speak.assert_called_once()


def test_open_focus_timer_controls_prompts_to_set(programs):
    from content import dialogue as dlg

    programs._focus_mode = True
    programs.open_focus_timer_controls()
    programs.speak.assert_called_once_with(
        dlg.FOCUS_TIMER_MINUTES_PROMPT,
        45,
        True,
        allow_in_focus=True,
    )


def test_open_focus_timer_controls_opens_manage_when_active(programs):
    import time

    from content import dialogue as dlg

    programs._focus_mode = True
    programs._focus_timer_end_at = time.monotonic() + 120
    programs.open_focus_timer_controls()
    programs.speak.assert_called_once_with(
        dlg.FOCUS_TIMER_MANAGE_PROMPT,
        45,
        True,
        allow_in_focus=True,
    )
