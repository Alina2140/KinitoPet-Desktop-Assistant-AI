"""Tests for safe Tk after scheduling helpers."""

from unittest.mock import MagicMock

from kinito.tk_timers import cancel_after, root_is_alive, schedule_after


def test_root_is_alive_false_when_not_running():
    root = MagicMock()
    root.winfo_exists.return_value = True
    assert root_is_alive(root, running=False) is False


def test_schedule_after_cancels_previous_job():
    root = MagicMock()
    owner = MagicMock()
    owner._running = True
    owner._timer = "old-id"
    root.winfo_exists.return_value = True
    root.after.return_value = "new-id"

    schedule_after(root, owner, "_timer", 100, lambda: None)

    root.after_cancel.assert_called_once_with("old-id")
    root.after.assert_called_once()
    assert owner._timer == "new-id"


def test_schedule_after_skips_when_root_gone():
    root = MagicMock()
    owner = MagicMock()
    owner._running = True
    root.winfo_exists.return_value = False

    schedule_after(root, owner, "_timer", 100, lambda: None)

    root.after.assert_not_called()


def test_cancel_after_clears_attribute():
    root = MagicMock()
    owner = MagicMock()
    owner._timer = "job-1"

    cancel_after(root, owner, "_timer")

    root.after_cancel.assert_called_once_with("job-1")
    assert owner._timer is None
