"""Tests for local STT silence detection and chat voice wiring."""

import tkinter as tk
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from content import dialogue as dlg
from kinito.speech import SpeechMixin
from kinito.speech_chat import (
    CHAT_VOICE_CONTINUOUS,
    CHAT_VOICE_PUSH,
    SpeechChatMixin,
)
from kinito.stt.voice_input import SilenceDetector


@pytest.fixture
def detector():
    return SilenceDetector(
        silence_ms=300,
        min_speech_ms=100,
        speech_rms=0.05,
        chunk_ms=100,
        max_utterance_ms=5000,
        calibration_chunks=1,
    )


def _loud(samples: int = 1600) -> np.ndarray:
    return np.full(samples, 0.2, dtype=np.float32)


def _quiet(samples: int = 1600) -> np.ndarray:
    return np.zeros(samples, dtype=np.float32)


def test_silence_detector_rms_zero_for_empty():
    assert SilenceDetector.rms(np.array([], dtype=np.float32)) == 0.0


def test_silence_detector_waits_for_speech_then_silence(detector):
    assert detector.feed(_quiet()) is None
    assert detector.feed(_loud()) is None  # speech starts (1 chunk = 100ms >= min)
    assert detector.feed(_quiet()) is None  # 100ms silence
    assert detector.feed(_quiet()) is None  # 200ms
    assert detector.feed(_quiet()) == "finalize"  # 300ms silence


def test_silence_detector_ignores_leading_silence(detector):
    for _ in range(10):
        assert detector.feed(_quiet()) is None


def test_silence_detector_max_utterance_without_speech():
    long = SilenceDetector(
        silence_ms=10_000,
        min_speech_ms=100,
        speech_rms=0.05,
        chunk_ms=100,
        max_utterance_ms=300,
        calibration_chunks=1,
    )
    assert long.feed(_quiet()) is None
    assert long.feed(_quiet()) is None
    assert long.feed(_quiet()) == "finalize"


def test_silence_detector_max_utterance(detector):
    long = SilenceDetector(
        silence_ms=10_000,
        min_speech_ms=100,
        speech_rms=0.05,
        chunk_ms=100,
        max_utterance_ms=300,
        calibration_chunks=1,
    )
    assert long.feed(_loud()) is None
    assert long.feed(_loud()) is None
    assert long.feed(_loud()) == "finalize"


class ChatSpeechStub(SpeechChatMixin, SpeechMixin):
    def send_chat_message(self, text: str) -> None:
        self._last_chat_message = text
        self._sent_messages = getattr(self, "_sent_messages", [])
        self._sent_messages.append(text)


@pytest.fixture
def chat_app():
    stub = ChatSpeechStub()
    stub.talking = False
    stub._awaiting_response = False
    stub._bubble_close_timer = None
    stub._speech_epoch = 0
    stub._speech_lock = MagicMock()
    stub._speech_lock.__enter__ = MagicMock(return_value=None)
    stub._speech_lock.__exit__ = MagicMock(return_value=False)
    stub.root = MagicMock()
    stub.root.after = MagicMock()
    stub.root.after_cancel = MagicMock()
    stub.play_sfx = MagicMock()
    stub.play_mp3 = MagicMock()
    stub._init_chat_state()
    stub._conversation = MagicMock()
    stub._conversation.reset = MagicMock()
    stub.change_sprite = MagicMock()
    stub.tk_img_thinking = MagicMock()
    stub.tk_img_talking = MagicMock()
    stub.tk_img_normal = MagicMock()
    stub._available_voices = set()
    stub._tts_cancelled = False
    stub._run_tts = MagicMock(return_value=True)
    stub.interrupt_speech = MagicMock()
    stub._cancel_bubble_close_timer = MagicMock()
    stub._fit_speech_bubble_to_content = MagicMock()
    stub._schedule_speech_bubble_position = MagicMock()
    stub._has_active_speech_bubble = MagicMock(return_value=False)
    stub._new_speech_bubble_toplevel = MagicMock()
    stub.speech_bubble = MagicMock()
    stub.speech_bubble.winfo_exists = MagicMock(return_value=True)
    stub.get_entry_char_width = SpeechMixin.get_entry_char_width.__get__(stub, ChatSpeechStub)
    stub.BUBBLE_BG = SpeechMixin.BUBBLE_BG
    stub.BUBBLE_TRANSPARENT_BG = SpeechMixin.BUBBLE_TRANSPARENT_BG
    stub.BUBBLE_OFF_SCREEN_GEOMETRY = SpeechMixin.BUBBLE_OFF_SCREEN_GEOMETRY
    stub.BUBBLE_BTN_BG = SpeechMixin.BUBBLE_BTN_BG
    stub.BUBBLE_BTN_ACTIVE = SpeechMixin.BUBBLE_BTN_ACTIVE
    stub._chat_greeting = MagicMock(return_value=dlg.CHAT_GREETING)
    stub.speak = MagicMock()
    stub.create_wrapped_label = MagicMock(return_value=MagicMock())
    stub._create_bubble_shell = MagicMock(return_value=MagicMock())
    stub._create_bubble_button = MagicMock(return_value=MagicMock())
    stub._close_speech_bubble_impl = MagicMock()
    stub.close_speech_bubble = MagicMock()
    return stub


def test_begin_chat_sets_push_mode(chat_app):
    chat_app.open_chat_bubble = MagicMock()
    chat_app.speak_chat_response = MagicMock()
    with patch(
        "kinito.stt.voice_input.check_voice_input_available",
        return_value=(True, None),
    ):
        chat_app._begin_chat_with_voice_mode(CHAT_VOICE_PUSH)
    assert chat_app._chat_voice_mode == CHAT_VOICE_PUSH
    chat_app.open_chat_bubble.assert_called_once()
    chat_app.speak_chat_response.assert_not_called()


def test_begin_chat_continuous_speaks_greeting(chat_app):
    chat_app.open_chat_bubble = MagicMock()
    chat_app.speak_chat_response = MagicMock()
    with patch(
        "kinito.stt.voice_input.check_voice_input_available",
        return_value=(True, None),
    ):
        chat_app._begin_chat_with_voice_mode(CHAT_VOICE_CONTINUOUS)
    assert chat_app._chat_voice_mode == CHAT_VOICE_CONTINUOUS
    chat_app.speak_chat_response.assert_called_once_with(dlg.CHAT_GREETING)


def test_continuous_mode_hides_text_entry(chat_app):
    chat_app._chat_voice_mode = CHAT_VOICE_CONTINUOUS
    chat_app._create_bubble_button = MagicMock(return_value=MagicMock())
    chat_app._update_mic_button_appearance = MagicMock()
    try:
        root = tk.Tk()
        root.withdraw()
        frame = tk.Frame(root)
    except tk.TclError:
        pytest.skip("No display for Tk")
        return
    try:
        with patch("kinito.speech_chat.load_mic_button_icon", return_value=None):
            chat_app._show_chat_input_row(frame)
        assert chat_app._chat_entry_widget is None
        assert chat_app._emoji_picker_button is None
        assert chat_app._chat_mic_button is not None
    finally:
        root.destroy()


def test_begin_chat_continuous_falls_back_without_stt(chat_app):
    chat_app.open_chat_bubble = MagicMock()
    chat_app.append_chat_message = MagicMock()
    chat_app.speak_chat_response = MagicMock()
    with patch(
        "kinito.stt.voice_input.check_voice_input_available",
        return_value=(False, "missing"),
    ):
        chat_app._begin_chat_with_voice_mode(CHAT_VOICE_CONTINUOUS)
    assert chat_app._chat_voice_mode == CHAT_VOICE_PUSH
    chat_app.append_chat_message.assert_called()
    chat_app.speak_chat_response.assert_not_called()


def test_voice_transcript_sends_chat_message(chat_app):
    chat_app._chat_mode = True
    chat_app._chat_voice_mode = CHAT_VOICE_PUSH
    entry = MagicMock()
    entry.winfo_exists.return_value = True
    chat_app._chat_entry_widget = entry
    chat_app._on_voice_transcript("Hello friend")
    assert chat_app._last_chat_message == "Hello friend"
    entry.delete.assert_called()


def test_voice_transcript_empty_resumes_continuous(chat_app):
    chat_app._chat_mode = True
    chat_app._chat_voice_mode = CHAT_VOICE_CONTINUOUS
    chat_app._chat_voice_paused = False
    chat_app._on_voice_transcript("   ")
    chat_app.root.after.assert_called()
    assert not hasattr(chat_app, "_last_chat_message")


def test_voice_capture_blocked_while_talking(chat_app):
    chat_app._chat_mode = True
    chat_app.talking = True
    assert chat_app._voice_capture_allowed() is False


def test_voice_capture_blocked_while_generating(chat_app):
    chat_app._chat_mode = True
    chat_app._chat_generating = True
    assert chat_app._voice_capture_allowed() is False


def test_set_chat_generating_stops_voice(chat_app):
    chat_app._chat_mode = True
    chat_app._chat_voice_listening = True
    controller = MagicMock()
    chat_app._voice_input = controller
    chat_app._chat_entry_widget = MagicMock()
    chat_app._chat_entry_widget.winfo_exists.return_value = True
    chat_app.set_chat_generating(True)
    controller.stop.assert_called_once()
    assert chat_app._chat_voice_listening is False


def test_close_chat_mode_stops_voice(chat_app):
    chat_app._chat_mode = True
    chat_app._chat_voice_mode = CHAT_VOICE_CONTINUOUS
    controller = MagicMock()
    chat_app._voice_input = controller
    chat_app._close_speech_bubble_impl = MagicMock()
    chat_app.close_chat_mode()
    controller.stop.assert_called_once()
    assert chat_app._chat_voice_mode is None
    assert chat_app._chat_mode is False


def test_on_chat_tts_finished_resumes_continuous(chat_app):
    chat_app._chat_mode = True
    chat_app._chat_voice_mode = CHAT_VOICE_CONTINUOUS
    chat_app._chat_voice_paused = False
    chat_app.talking = False
    chat_app._chat_generating = False
    chat_app._start_voice_listening = MagicMock()
    with patch(
        "kinito.stt.voice_input.check_voice_input_available",
        return_value=(True, None),
    ):
        chat_app._on_chat_tts_finished()
    chat_app._start_voice_listening.assert_called_once()


def test_on_chat_tts_finished_skips_push_mode(chat_app):
    chat_app._chat_mode = True
    chat_app._chat_voice_mode = CHAT_VOICE_PUSH
    chat_app._start_voice_listening = MagicMock()
    chat_app._on_chat_tts_finished()
    chat_app._start_voice_listening.assert_not_called()
