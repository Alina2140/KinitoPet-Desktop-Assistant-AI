"""Tests for quiet focus mode."""

from unittest.mock import MagicMock

import pytest

from kinito.speech import SpeechMixin


class SpeechStub(SpeechMixin):
    def __init__(self):
        self._speech_epoch = 0
        self._focus_mode = False
        self.talking = False
        self._awaiting_response = False


@pytest.fixture
def speech():
    return SpeechStub()


def test_speak_is_blocked_in_focus_mode(speech):
    speech._focus_mode = True
    speech.interrupt_speech = MagicMock()
    speech.speak("Hello")
    speech.interrupt_speech.assert_not_called()


def test_speak_brief_is_blocked_in_focus_mode(speech):
    speech._focus_mode = True
    speech.interrupt_speech = MagicMock()
    speech.show_speech_bubble = MagicMock()
    speech.speak_brief("Quiet")
    speech.show_speech_bubble.assert_not_called()


def test_toggle_focus_on_speaks_without_ai_and_allows_in_focus():
    from unittest.mock import MagicMock, patch

    from content import dialogue as dlg
    from kinito.app import FloatingAssistant

    app = FloatingAssistant.__new__(FloatingAssistant)
    app._focus_mode = False
    app.interrupt_speech = MagicMock()
    app.close_speech_bubble = MagicMock()
    app.end_hug = MagicMock()
    app.hide_screen_glitch = MagicMock()
    app.hide_blue_screen = MagicMock()
    app._ensure_single_game_window = MagicMock()
    app.close_camera = MagicMock()
    app.close_browser = MagicMock()
    app.speak = MagicMock()

    with patch("kinito.app.dlg.pick_line", return_value=dlg.FOCUS_ON_LINES[0]):
        FloatingAssistant.toggle_focus(app)

    assert app._focus_mode is True
    app.speak.assert_called_once_with(
        dlg.FOCUS_ON_LINES[0],
        skip_ai=True,
        allow_in_focus=True,
    )


def test_toggle_focus_off_clears_focus_timer():
    from unittest.mock import MagicMock, patch

    from content import dialogue as dlg
    from kinito.app import FloatingAssistant

    app = FloatingAssistant.__new__(FloatingAssistant)
    app._focus_mode = True
    app._clear_focus_timer = MagicMock()
    app.speak = MagicMock()

    with patch("kinito.app.dlg.pick_line", return_value=dlg.FOCUS_OFF_LINES[0]):
        FloatingAssistant.toggle_focus(app)

    assert app._focus_mode is False
    app._clear_focus_timer.assert_called_once()
    app.speak.assert_called_once_with(dlg.FOCUS_OFF_LINES[0], skip_ai=True)
