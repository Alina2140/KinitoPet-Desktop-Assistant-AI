from unittest.mock import MagicMock, patch

import pytest

from kinito.app import FloatingAssistant


@pytest.fixture
def pause_app():
    app = FloatingAssistant.__new__(FloatingAssistant)
    app.root = MagicMock()
    app._running = True
    app.paused = False
    app._auto_wake_timer = None
    app.tk_img_normal = "normal"
    app.speak = MagicMock()
    app.change_sprite = MagicMock()
    return app


def test_spontaneous_pause_schedules_auto_wake(pause_app):
    with patch("kinito.app.random.randint", return_value=60):
        pause_app.pause(spontaneous=True)

    assert pause_app.paused is True
    pause_app.root.after.assert_called_once_with(60_000, pause_app._wake_from_spontaneous_nap)
    assert pause_app._auto_wake_timer is not None


def test_manual_pause_does_not_schedule_auto_wake(pause_app):
    pause_app.pause(spontaneous=False)
    assert pause_app.paused is True
    pause_app.root.after.assert_not_called()


def test_wake_from_spontaneous_nap_calls_unpause(pause_app):
    pause_app.paused = True
    with patch.object(pause_app, "unpause") as unpause:
        pause_app._wake_from_spontaneous_nap()
    unpause.assert_called_once()


def test_unpause_cancels_auto_wake_timer(pause_app):
    pause_app._auto_wake_timer = 42
    pause_app.unpause()
    pause_app.root.after_cancel.assert_called_once_with(42)
    assert pause_app._auto_wake_timer is None
