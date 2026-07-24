from unittest.mock import MagicMock, patch

import pytest

from content import dialogue as dlg
from kinito.features.nudges import NudgesMixin


class NudgeStub(NudgesMixin):
    pass


@pytest.fixture
def nudges():
    stub = NudgeStub()
    stub._running = True
    stub._ambient_reminders_enabled = True
    stub._last_nudge_at = 0.0
    stub.paused = False
    stub.is_dragging = False
    stub._camera_active = False
    stub._browser_active = False
    stub._focus_mode = False
    stub.root = MagicMock()
    stub.root.after = MagicMock()
    stub.root.winfo_vrootx.return_value = 0
    stub.root.winfo_vrooty.return_value = 0
    stub.root.winfo_vrootwidth.return_value = 1920
    stub.root.winfo_vrootheight.return_value = 1080
    stub.speak = MagicMock()
    stub.show_popup_text = MagicMock()
    stub._is_busy_with_speech = MagicMock(return_value=False)
    stub._is_game_active = MagicMock(return_value=False)
    return stub


def test_maybe_trigger_ambient_reminder_respects_disabled(nudges):
    nudges._ambient_reminders_enabled = False
    assert nudges.maybe_trigger_ambient_reminder() is False
    nudges.root.after.assert_not_called()


def test_maybe_trigger_ambient_reminder_respects_focus(nudges):
    nudges._focus_mode = True
    assert nudges.maybe_trigger_ambient_reminder() is False
    nudges.root.after.assert_not_called()


def test_maybe_trigger_ambient_reminder_respects_busy_speech(nudges):
    nudges._is_busy_with_speech.return_value = True
    assert nudges.maybe_trigger_ambient_reminder() is False
    nudges.root.after.assert_not_called()


def test_maybe_trigger_ambient_reminder_respects_cooldown(nudges):
    with patch("kinito.features.nudges.time.monotonic", return_value=1000.0):
        nudges._last_nudge_at = 1000.0 - 60.0
        with patch("kinito.features.nudges.random.random", return_value=0.0):
            assert nudges.maybe_trigger_ambient_reminder() is False
    nudges.root.after.assert_not_called()


def test_maybe_trigger_ambient_reminder_schedules_on_hit(nudges):
    with (
        patch("kinito.features.nudges.time.monotonic", return_value=5000.0),
        patch("kinito.features.nudges.random.random", return_value=0.0),
    ):
        assert nudges.maybe_trigger_ambient_reminder() is True
        assert nudges._last_nudge_at == 5000.0
    nudges.root.after.assert_called_once_with(0, nudges._present_ambient_nudge)


def test_maybe_trigger_ambient_reminder_skips_on_miss(nudges):
    with (
        patch("kinito.features.nudges.time.monotonic", return_value=5000.0),
        patch("kinito.features.nudges.random.random", return_value=0.99),
    ):
        assert nudges.maybe_trigger_ambient_reminder() is False
    nudges.root.after.assert_not_called()


def test_present_ambient_nudge_uses_bubble(nudges):
    with (
        patch("kinito.features.nudges.pick_nudge_line", return_value="Drink water!"),
        patch("kinito.features.nudges.random.random", return_value=0.9),
    ):
        nudges._present_ambient_nudge()
    nudges.speak.assert_called_once_with("Drink water!")
    nudges.show_popup_text.assert_not_called()


def test_present_ambient_nudge_uses_popup(nudges):
    with (
        patch("kinito.features.nudges.pick_nudge_line", return_value="I am watching."),
        patch("kinito.features.nudges.random.random", return_value=0.1),
    ):
        # Restore real show_popup_text path via MagicMock already on stub
        nudges.show_popup_text = MagicMock()
        nudges._present_ambient_nudge()
    nudges.show_popup_text.assert_called_once_with("I am watching.", title="KinitoPET")
    nudges.speak.assert_not_called()


def test_toggle_ambient_reminders_disables(nudges):
    nudges.toggle_ambient_reminders()
    assert nudges._ambient_reminders_enabled is False
    nudges.speak.assert_called_once()
    assert nudges.speak.call_args[0][0] in dlg.REMINDERS_OFF_LINES


def test_toggle_ambient_reminders_enables(nudges):
    nudges._ambient_reminders_enabled = False
    nudges.toggle_ambient_reminders()
    assert nudges._ambient_reminders_enabled is True
    assert nudges.speak.call_args[0][0] in dlg.REMINDERS_ON_LINES
