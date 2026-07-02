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
