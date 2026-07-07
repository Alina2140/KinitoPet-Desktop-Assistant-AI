from unittest.mock import MagicMock, patch
import threading

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


def test_speak_stops_speech_accompaniment_after_tts(speech):
    speech._speech_epoch = 0
    speech._speech_lock = threading.Lock()
    speech._run_tts = MagicMock()
    speech.stop_speech_accompaniment_music = MagicMock()
    speech._start_speech_accompaniment = MagicMock()
    speech._focus_mode = False

    speech.speak("poem line", show_bubble=False, wait_for_tts=True)

    speech.stop_speech_accompaniment_music.assert_called_once()


def test_speak_starts_accompaniment_after_interrupt(speech):
    speech._speech_epoch = 0
    speech._speech_lock = threading.Lock()
    speech._run_tts = MagicMock()
    speech._start_speech_accompaniment = MagicMock()
    speech.interrupt_speech = MagicMock()
    speech._focus_mode = False

    speech.speak(
        "poem line",
        show_bubble=False,
        wait_for_tts=True,
        speech_accompaniment_path="poem.mp3",
        speech_accompaniment_volume=0.6,
    )

    speech.interrupt_speech.assert_called_once()
    speech._start_speech_accompaniment.assert_called_once_with("poem.mp3", 0.6)


def test_interrupt_speech_stops_speech_accompaniment(speech):
    speech._speech_epoch = 0
    speech._next_speech_epoch = MagicMock(side_effect=lambda: setattr(speech, "_speech_epoch", 1))
    speech._stop_active_tts = MagicMock()
    speech._cancel_bubble_close_timer = MagicMock()
    speech.talking = True
    speech.stop_speech_accompaniment_music = MagicMock()

    speech.interrupt_speech()

    speech.stop_speech_accompaniment_music.assert_called_once()
