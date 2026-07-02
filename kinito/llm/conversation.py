"""Chat history management for Ollama conversations."""

from __future__ import annotations

from copy import deepcopy


class ConversationHistory:
    """Stores user/assistant messages sent to Ollama (system prompt kept separate)."""

    def __init__(self, max_messages: int = 20) -> None:
        self._max_messages = max(1, max_messages)
        self._messages: list[dict[str, str]] = []

    def reset(self) -> None:
        """Clear all stored messages."""
        self._messages.clear()

    def add_user(self, text: str) -> None:
        """Append a user message."""
        self._append("user", text)

    def add_assistant(self, text: str) -> None:
        """Append an assistant message."""
        self._append("assistant", text)

    def _append(self, role: str, text: str) -> None:
        content = text.strip()
        if not content:
            return
        self._messages.append({"role": role, "content": content})
        self._trim()

    def _trim(self) -> None:
        if len(self._messages) <= self._max_messages:
            return
        overflow = len(self._messages) - self._max_messages
        del self._messages[:overflow]

    def messages_for_api(self, system_prompt: str) -> list[dict[str, str]]:
        """Return messages including the system prompt for Ollama /api/chat."""
        payload = [{"role": "system", "content": system_prompt}]
        payload.extend(deepcopy(self._messages))
        return payload

    def __len__(self) -> int:
        return len(self._messages)
