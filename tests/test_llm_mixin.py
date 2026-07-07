"""Tests for the Ollama LLM mixin."""

from unittest.mock import MagicMock, patch

import pytest

from kinito.features.llm import LLMMixin
from kinito.llm.config import LLMConfig
from kinito.llm.ollama_client import OllamaUnavailableError
from kinito.speech import SpeechMixin


class LLMStub(LLMMixin, SpeechMixin):
    pass


@pytest.fixture
def llm_app():
    app = LLMStub()
    app.root = MagicMock()
    app.root.after = lambda _delay, fn, *args: fn(*args)
    app.talking = False
    app._awaiting_response = False
    app._speech_epoch = 0
    app._speech_lock = MagicMock()
    app._speech_lock.__enter__ = MagicMock(return_value=None)
    app._speech_lock.__exit__ = MagicMock(return_value=False)
    app._llm_config = LLMConfig(
        enabled=True,
        idle_lines=True,
        idle_chance=1.0,
        replace_chance=1.0,
    )
    app._ollama_client = MagicMock()
    app._ollama_client.is_available.return_value = True
    app._ollama_client.chat.return_value = "Hello friend!"
    app._ollama_client.generate.return_value = "Just checking in on you."
    app._init_chat_state()
    app._conversation = MagicMock()
    app._conversation.messages_for_api.return_value = [{"role": "user", "content": "Hi"}]
    app._conversation.reset = MagicMock()
    app._conversation.add_user = MagicMock()
    app._conversation.add_assistant = MagicMock()
    app.open_chat_bubble = MagicMock()
    app.append_chat_message = MagicMock()
    app.set_chat_generating = MagicMock()
    app.speak_chat_response = MagicMock()
    app._can_initiate_spontaneous_speech = MagicMock(return_value=True)
    app._chat_mode = False
    app._chat_generating = False
    app._ai_generating = False
    return app


def test_start_chat_opens_bubble_when_ollama_available(llm_app):
    llm_app.start_chat()
    llm_app._conversation.reset.assert_called_once()
    llm_app.open_chat_bubble.assert_called_once()


@patch.object(SpeechMixin, "speak")
def test_start_chat_fallback_when_unavailable(mock_speak, llm_app):
    llm_app._ollama_client.is_available.return_value = False
    llm_app.start_chat()
    mock_speak.assert_called_once()
    llm_app.open_chat_bubble.assert_not_called()


def test_send_chat_message_calls_ollama_and_updates_ui(llm_app):
    llm_app._chat_mode = True

    with patch("kinito.features.llm.threading.Thread") as thread_cls:
        thread_cls.return_value = MagicMock()
        llm_app.send_chat_message("Hello")

        thread_cls.assert_called_once()
        worker = thread_cls.call_args.kwargs["target"]
        worker()

    llm_app._conversation.add_user.assert_called_once_with("Hello")
    llm_app.append_chat_message.assert_called()
    llm_app._conversation.add_assistant.assert_called_once_with("Hello friend!")
    llm_app.speak_chat_response.assert_called_once_with("Hello friend!")


def test_send_chat_message_error_shows_fallback(llm_app):
    llm_app._chat_mode = True
    llm_app._ollama_client.chat.side_effect = OllamaUnavailableError("down")

    with patch("kinito.features.llm.threading.Thread") as thread_cls:
        thread_cls.return_value = MagicMock()
        llm_app.send_chat_message("Hello")
        thread_cls.call_args.kwargs["target"]()

    llm_app.speak_chat_response.assert_called_once()


def test_should_use_ai_idle_line_requires_availability(llm_app):
    llm_app._chat_mode = False
    assert llm_app._should_use_ai_idle_line() is True
    llm_app._ollama_client.is_available.return_value = False
    assert llm_app._should_use_ai_idle_line() is False


def test_activate_pending_visuals_starts_hug(llm_app):
    llm_app._begin_hug_after_speech = True
    llm_app._enter_hug_pose = MagicMock()
    llm_app._activate_pending_visuals()
    llm_app._enter_hug_pose.assert_called_once()
    assert llm_app._begin_hug_after_speech is False


@patch.object(SpeechMixin, "speak")
def test_speak_ai_idle_line_fallback_on_error(mock_speak, llm_app):
    llm_app._ollama_client.generate.side_effect = OllamaUnavailableError("down")

    with patch("kinito.features.llm.threading.Thread") as thread_cls:
        thread_cls.return_value = MagicMock()
        llm_app.speak_ai_idle_line()
        thread_cls.call_args.kwargs["target"]()

    mock_speak.assert_called_once()
    assert mock_speak.call_args.args[0]
    assert llm_app._ai_generating is False


@patch.object(SpeechMixin, "speak")
def test_generate_and_speak_shows_thinking_sprite(mock_speak, llm_app):
    llm_app.change_sprite = MagicMock()
    llm_app.tk_img_thinking = "thinking"

    with patch("kinito.features.llm.threading.Thread") as thread_cls:
        thread_cls.return_value = MagicMock()
        llm_app._generate_and_speak("fallback", ai_hint="say hi")

    llm_app.change_sprite.assert_called_with("thinking")
    assert llm_app._talk_sprite_mode == "thinking"
    assert llm_app._ai_generating is True


@patch.object(SpeechMixin, "speak")
def test_speak_skips_ai_for_interactive_dialog(mock_speak, llm_app):
    with patch("kinito.features.llm.find_dialog_spec", return_value=object()):
        llm_app.speak("Want to play a game?", 45, True)

    mock_speak.assert_called_once()
    assert "skip_ai" not in mock_speak.call_args.kwargs


@patch.object(SpeechMixin, "speak")
def test_speak_uses_ai_for_plain_lines(mock_speak, llm_app):
    with patch("kinito.features.llm.find_dialog_spec", return_value=None):
        with patch("kinito.features.llm.threading.Thread") as thread_cls:
            thread_cls.return_value = MagicMock()
            llm_app.speak("Hello there!")
            thread_cls.call_args.kwargs["target"]()

    mock_speak.assert_called_once()
    assert mock_speak.call_args.args[0] == "Just checking in on you."


@patch.object(SpeechMixin, "speak")
def test_speak_preserves_poem_accompaniment_through_ai(mock_speak, llm_app):
    llm_app.close_speech_bubble = MagicMock()

    with patch("kinito.features.llm.find_dialog_spec", return_value=None):
        with patch("kinito.features.llm.threading.Thread") as thread_cls:
            thread_cls.return_value = MagicMock()
            llm_app.speak(
                "Roses are red",
                long_bubble=True,
                speech_accompaniment_path="poem.mp3",
                speech_accompaniment_volume=0.75,
            )
            thread_cls.call_args.kwargs["target"]()

    mock_speak.assert_called_once()
    assert mock_speak.call_args.args[0] == "Just checking in on you."
    assert mock_speak.call_args.kwargs["speech_accompaniment_path"] == "poem.mp3"
    assert mock_speak.call_args.kwargs["speech_accompaniment_volume"] == 0.75
    assert mock_speak.call_args.kwargs["long_bubble"] is True
