from unittest.mock import MagicMock

import pytest

from kinito.speech import SpeechMixin


class SpeechStub(SpeechMixin):
    pass


@pytest.fixture
def speech():
    stub = SpeechStub()
    stub.talking = False
    stub._awaiting_response = False
    stub._bubble_close_timer = None
    stub.root = MagicMock()
    stub.root.after = MagicMock()
    stub.root.after_cancel = MagicMock()
    stub.play_mp3 = MagicMock()
    return stub


@pytest.mark.parametrize(
    "prompt,width",
    [
        ("", 15),
        ("What is your favorite color?", 22),
        ("x" * 120, 40),
    ],
)
def test_get_entry_char_width_bounds(speech, prompt, width):
    assert speech.get_entry_char_width(prompt) <= 40
    assert speech.get_entry_char_width(prompt) >= 15


def test_is_busy_with_speech_when_talking(speech):
    speech.talking = True
    assert speech._is_busy_with_speech() is True


def test_is_busy_when_awaiting_response(speech):
    speech._awaiting_response = True
    assert speech._is_busy_with_speech() is True


def test_load_available_voices_empty_without_balcon(speech):
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("kinito.speech.os.path.isfile", lambda p: False)
        voices = speech._load_available_voices()
    assert voices == set()


def test_cancel_bubble_close_timer(speech):
    speech._bubble_close_timer = 99
    speech._cancel_bubble_close_timer()
    speech.root.after_cancel.assert_called_once_with(99)
    assert speech._bubble_close_timer is None
