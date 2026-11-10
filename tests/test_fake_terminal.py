from unittest.mock import MagicMock, patch

import pytest

from content import dialogue as dlg
from kinito.features.fake_terminal import FakeTerminalMixin


class TerminalStub(FakeTerminalMixin):
    pass


@pytest.fixture
def terminal():
    stub = TerminalStub()
    stub._running = True
    stub._terminal_enabled = True
    stub.paused = False
    stub.is_dragging = False
    stub._camera_active = False
    stub._browser_active = False
    stub._terminal_window = None
    stub._terminal_text = None
    stub._terminal_timers = []
    stub._terminal_lines = []
    stub._terminal_line_index = 0
    stub._terminal_char_index = 0
    stub._last_terminal_at = 0.0
    stub.root = MagicMock()
    stub.root.after = MagicMock(side_effect=lambda _ms, _cb: "timer")
    stub.root.after_cancel = MagicMock()
    stub.root.update_idletasks = MagicMock()
    stub.root.winfo_vrootx.return_value = 0
    stub.root.winfo_vrooty.return_value = 0
    stub.root.winfo_vrootwidth.return_value = 1920
    stub.root.winfo_vrootheight.return_value = 1080
    stub.speak = MagicMock()
    return stub


def test_maybe_trigger_terminal_respects_disabled(terminal):
    terminal._terminal_enabled = False
    assert terminal.maybe_trigger_terminal() is False
    terminal.root.after.assert_not_called()


def test_maybe_trigger_terminal_respects_paused(terminal):
    terminal.paused = True
    assert terminal.maybe_trigger_terminal() is False
    terminal.root.after.assert_not_called()


def test_maybe_trigger_terminal_schedules_on_hit(terminal):
    with patch("kinito.features.fake_terminal.random.random", return_value=0.0):
        assert terminal.maybe_trigger_terminal() is True
    terminal.root.after.assert_called_once_with(0, terminal._open_fake_terminal)


def test_maybe_trigger_terminal_skips_on_miss(terminal):
    with (
        patch.object(terminal, "TERMINAL_CHANCE", 0.5),
        patch("kinito.features.fake_terminal.random.random", return_value=0.99),
    ):
        assert terminal.maybe_trigger_terminal() is False
    terminal.root.after.assert_not_called()


def test_maybe_trigger_terminal_respects_cooldown(terminal):
    import time

    terminal._last_terminal_at = time.monotonic()
    with patch("kinito.features.fake_terminal.random.random", return_value=0.0):
        assert terminal.maybe_trigger_terminal() is False
    terminal.root.after.assert_not_called()


def test_toggle_terminal_disables_and_hides(terminal):
    window = MagicMock()
    window.winfo_exists.return_value = True
    terminal._terminal_window = window
    terminal.toggle_terminal()
    assert terminal._terminal_enabled is False
    window.destroy.assert_called_once()
    assert terminal._terminal_window is None
    assert terminal.speak.call_args[0][0] in dlg.TERMINAL_OFF_LINES


def test_toggle_terminal_enables(terminal):
    terminal._terminal_enabled = False
    terminal.toggle_terminal()
    assert terminal._terminal_enabled is True
    assert terminal.speak.call_args[0][0] in dlg.TERMINAL_ON_LINES


def test_terminal_script_lines_replaces_user_placeholder(terminal):
    with patch(
        "kinito.features.fake_terminal.random.choice",
        return_value=(("cmd", "echo {user}"),),
    ):
        lines = terminal._terminal_script_lines()
    assert lines == [("cmd", "echo " + lines[0][1].removeprefix("echo "))]
    assert "{user}" not in lines[0][1]


def test_terminal_type_next_types_cmd_characters(terminal):
    window = MagicMock()
    window.winfo_exists.return_value = True
    terminal._terminal_window = window
    terminal._terminal_text = MagicMock()
    terminal._terminal_lines = [("cmd", "dir")]
    terminal._terminal_line_index = 0
    terminal._terminal_char_index = 0

    terminal._terminal_type_next()

    text_widget = terminal._terminal_text
    text_widget.insert.assert_called_once_with("end", "C")
    assert terminal._terminal_char_index == 1
    terminal.root.after.assert_called_with(
        terminal.TERMINAL_TYPE_MS, terminal._terminal_type_next
    )


def test_terminal_type_next_prints_out_lines_instantly(terminal):
    window = MagicMock()
    window.winfo_exists.return_value = True
    terminal._terminal_window = window
    terminal._terminal_text = MagicMock()
    terminal._terminal_lines = [("out", "done.")]
    terminal._terminal_line_index = 0
    terminal._terminal_char_index = 0

    terminal._terminal_type_next()

    terminal._terminal_text.insert.assert_called_once_with("end", "done.\n")
    assert terminal._terminal_line_index == 1
    terminal.root.after.assert_called_with(
        terminal.TERMINAL_LINE_PAUSE_MS, terminal._terminal_type_next
    )


def test_terminal_type_next_schedules_close_after_last_line(terminal):
    window = MagicMock()
    window.winfo_exists.return_value = True
    terminal._terminal_window = window
    terminal._terminal_lines = [("out", "x")]
    terminal._terminal_line_index = 1

    terminal._terminal_type_next()

    terminal.root.after.assert_called_with(
        terminal.TERMINAL_CLOSE_DELAY_MS, terminal.hide_fake_terminal
    )


def test_hide_fake_terminal_cancels_timers_and_destroys(terminal):
    window = MagicMock()
    terminal._terminal_window = window
    terminal._terminal_timers = ["t1", "t2"]

    terminal.hide_fake_terminal()

    assert terminal.root.after_cancel.call_count == 2
    window.destroy.assert_called_once()
    assert terminal._terminal_window is None
    assert terminal._terminal_timers == []
