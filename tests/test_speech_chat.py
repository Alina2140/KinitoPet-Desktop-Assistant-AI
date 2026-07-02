"""Tests for chat-mode speech bubble behavior."""

import tkinter as tk
from unittest.mock import MagicMock

import pytest

from kinito.speech import SpeechMixin
from kinito.speech_chat import SpeechChatMixin


class ChatSpeechStub(SpeechChatMixin, SpeechMixin):
    def send_chat_message(self, text: str) -> None:
        self._last_chat_message = text


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
    return stub


def test_init_chat_state_defaults(chat_app):
    assert chat_app._chat_mode is False
    assert chat_app._chat_generating is False


def test_close_chat_mode_resets_conversation(chat_app):
    chat_app._chat_mode = True
    chat_app._close_speech_bubble_impl = MagicMock()
    chat_app.close_chat_mode()
    chat_app._conversation.reset.assert_called_once()
    assert chat_app._chat_mode is False
    chat_app._close_speech_bubble_impl.assert_called_once()


def test_set_chat_generating_disables_input(chat_app):
    entry = MagicMock()
    entry.winfo_exists.return_value = True
    chat_app._chat_entry_widget = entry
    chat_app.set_chat_generating(True)
    entry.configure.assert_called_with(state=tk.DISABLED)
