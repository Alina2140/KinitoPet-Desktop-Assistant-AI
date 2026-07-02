"""Tests for the Ollama HTTP client."""

import json
from unittest.mock import MagicMock, patch

import pytest

from kinito.llm.config import LLMConfig
from kinito.llm.conversation import ConversationHistory
from kinito.llm.ollama_client import OllamaClient, OllamaUnavailableError


def _mock_urlopen(response_data: dict | str, *, status: int = 200):
    body = response_data if isinstance(response_data, str) else json.dumps(response_data)
    mock_response = MagicMock()
    mock_response.read.return_value = body.encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = False
    return mock_response


@pytest.fixture
def client():
    config = LLMConfig(
        base_url="http://127.0.0.1:11434",
        model="test-model",
        timeout_s=5,
        enabled=True,
    )
    return OllamaClient(config)


def test_chat_returns_assistant_message(client):
    payload = {"message": {"role": "assistant", "content": "Hello there!"}}
    with patch("urllib.request.urlopen", return_value=_mock_urlopen(payload)):
        result = client.chat([{"role": "user", "content": "Hi"}])
    assert result == "Hello there!"


def test_generate_returns_response_text(client):
    payload = {"response": "Just wandering by your desktop."}
    with patch("urllib.request.urlopen", return_value=_mock_urlopen(payload)):
        result = client.generate("Say hello.")
    assert result == "Just wandering by your desktop."


def test_chat_raises_on_empty_response(client):
    with patch("urllib.request.urlopen", return_value=_mock_urlopen({"message": {"content": ""}})):
        with pytest.raises(OllamaUnavailableError):
            client.chat([{"role": "user", "content": "Hi"}])


def test_is_available_uses_cache(client):
    with patch("urllib.request.urlopen", return_value=_mock_urlopen({"models": []})) as urlopen:
        assert client.is_available() is True
        assert client.is_available() is True
        assert urlopen.call_count == 1


def test_is_available_false_when_disabled():
    config = LLMConfig(enabled=False)
    client = OllamaClient(config)
    assert client.is_available(force_check=True) is False


def test_connection_error_raises_unavailable(client):
    with patch("urllib.request.urlopen", side_effect=OSError("connection refused")):
        with pytest.raises(OllamaUnavailableError):
            client.chat([{"role": "user", "content": "Hi"}])


def test_conversation_history_trim_and_api_payload():
    history = ConversationHistory(max_messages=2)
    history.add_user("one")
    history.add_assistant("two")
    history.add_user("three")
    assert len(history) == 2
    messages = history.messages_for_api("system")
    assert messages[0]["role"] == "system"
    assert messages[-1]["content"] == "three"
