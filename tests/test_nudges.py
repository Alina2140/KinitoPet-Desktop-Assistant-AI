import tkinter as tk
from unittest.mock import MagicMock, patch

import pytest

from content import dialogue as dlg
from kinito.features.nudges import NudgesMixin


class NudgeStub(NudgesMixin):
    pass


def _require_tk_root() -> tk.Tk:
    """Return a withdrawn Tk root, or skip when Tcl/Tk is unavailable."""
    try:
        root = tk.Tk()
        root.withdraw()
        return root
    except tk.TclError as exc:
        pytest.skip(f"No usable Tcl/Tk display: {exc}")


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


def test_present_ambient_nudge_uses_windows_popup(nudges):
    with patch.object(nudges, "_pick_ambient_nudge_text", return_value="I am watching."):
        nudges.show_popup_text = MagicMock()
        nudges._present_ambient_nudge()
    nudges.show_popup_text.assert_called_once_with("I am watching.", title="KinitoPET")
    nudges.speak.assert_not_called()


def test_show_popup_text_builds_windows_style_dialog(nudges):
    root = _require_tk_root()
    nudges.root = root
    try:
        nudges.show_popup_text = NudgesMixin.show_popup_text.__get__(nudges, NudgeStub)
        nudges.show_popup_text("Drink some water.", title="KinitoPET", auto_close_ms=0)
        popups = [child for child in root.winfo_children() if isinstance(child, tk.Toplevel)]
        assert len(popups) == 1
        popup = popups[0]
        assert popup.title() == "KinitoPET"
        assert popup.wm_attributes("-topmost") == 1
        labels = []

        def _collect(widget):
            if isinstance(widget, tk.Label):
                labels.append(widget)
            for child in widget.winfo_children():
                _collect(child)

        _collect(popup)
        message = next(label for label in labels if label.cget("text") == "Drink some water.")
        assert "Segoe UI" in str(message.cget("font"))
        assert any(getattr(widget, "_nudge_ok_text", None) == "OK" for widget in labels)
        popup.update_idletasks()
        # Compact: shorter than the old fixed 420x180 popup.
        assert popup.winfo_width() <= 400
        assert popup.winfo_height() <= 170
        popup.destroy()
    finally:
        root.destroy()


def test_show_popup_text_grows_for_long_messages(nudges):
    root = _require_tk_root()
    nudges.root = root
    try:
        nudges.show_popup_text = NudgesMixin.show_popup_text.__get__(nudges, NudgeStub)
        short = "Hi."
        long = (
            "Don't forget to hydrate! Water is your friend. "
            "I'm your friend too. Drink both. Stay a while."
        )
        nudges.show_popup_text(short, title="KinitoPET", auto_close_ms=0)
        short_popup = next(
            child for child in root.winfo_children() if isinstance(child, tk.Toplevel)
        )
        short_popup.update_idletasks()
        short_w = short_popup.winfo_width()
        short_popup.destroy()

        nudges.show_popup_text(long, title="KinitoPET", auto_close_ms=0)
        long_popup = next(
            child for child in root.winfo_children() if isinstance(child, tk.Toplevel)
        )
        long_popup.update_idletasks()
        long_w = long_popup.winfo_width()
        long_h = long_popup.winfo_height()
        long_popup.destroy()

        assert short_w < long_w or long_h > 120
    finally:
        root.destroy()


def test_show_popup_text_uses_random_on_screen_position(nudges):
    root = _require_tk_root()
    nudges.root = root
    try:
        nudges.show_popup_text = NudgesMixin.show_popup_text.__get__(nudges, NudgeStub)
        with patch(
            "kinito.features.nudges.random_fully_visible_origin",
            return_value=(123, 456),
        ) as place:
            nudges.show_popup_text("Hello there.", title="KinitoPET", auto_close_ms=0)
        place.assert_called_once()
        popup = next(
            child for child in root.winfo_children() if isinstance(child, tk.Toplevel)
        )
        geom = popup.geometry()
        assert geom.endswith("+123+456")
        popup.destroy()
    finally:
        root.destroy()


def test_pick_ambient_nudge_text_can_use_app_awareness(nudges):
    from kinito.app_context import AppSnapshot

    nudges.get_app_snapshot = MagicMock(
        return_value=AppSnapshot("Chrome", ("Chrome",))
    )
    with (
        patch("kinito.features.nudges.maybe_pick_app_aware_nudge_line", return_value="Still in Chrome?"),
        patch("kinito.features.nudges.pick_nudge_line", return_value="Drink water!"),
    ):
        assert nudges._pick_ambient_nudge_text() == "Still in Chrome?"


def test_pick_ambient_nudge_text_falls_back_without_apps(nudges):
    nudges.get_app_snapshot = MagicMock(return_value=None)
    with patch("kinito.features.nudges.pick_nudge_line", return_value="Drink water!"):
        assert nudges._pick_ambient_nudge_text() == "Drink water!"


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
