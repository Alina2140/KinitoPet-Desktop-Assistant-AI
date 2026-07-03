"""HTTP client for the local Ollama API."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from kinito.llm.config import AvailabilityCache, LLMConfig


class OllamaError(Exception):
    """Base error for Ollama client failures."""


class OllamaUnavailableError(OllamaError):
    """Raised when Ollama cannot be reached or returns an error response."""


class OllamaClient:
    """Thin wrapper around Ollama's /api/chat and /api/generate endpoints."""

    def __init__(self, config: LLMConfig | None = None) -> None:
        self.config = config or LLMConfig.from_env()
        self._availability = AvailabilityCache(self.config.availability_cache_s)

    def is_available(self, *, force_check: bool = False) -> bool:
        """Return whether Ollama responds to a lightweight health check."""
        if not self.config.enabled:
            return False
        if not force_check:
            cached = self._availability.get()
            if cached is not None:
                return cached
        available = self._ping()
        self._availability.set(available)
        return available

    def _ping(self) -> bool:
        try:
            self._request("GET", "/api/tags", body=None)
            return True
        except OllamaError:
            return False

    def chat(self, messages: list[dict[str, str]], *, max_tokens: int | None = None) -> str:
        """Send a chat completion request and return the assistant reply text."""
        tokens = max_tokens if max_tokens is not None else self.config.max_tokens_long
        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": False,
            "keep_alive": self.config.keep_alive,
            "options": {"num_predict": tokens},
        }
        data = self._request("POST", "/api/chat", body=payload)
        content = self._extract_message_content(data)
        if not content:
            raise OllamaUnavailableError("Ollama returned an empty chat response.")
        return content

    def generate(self, prompt: str, *, system: str | None = None, max_tokens: int = 128) -> str:
        """Send a single-shot generate request (used for idle lines)."""
        payload: dict[str, Any] = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": self.config.keep_alive,
        }
        if system:
            payload["system"] = system
        payload["options"] = {"num_predict": max_tokens}
        data = self._request("POST", "/api/generate", body=payload)
        content = str(data.get("response", "")).strip()
        if not content:
            raise OllamaUnavailableError("Ollama returned an empty generate response.")
        return content

    def _extract_message_content(self, data: dict[str, Any]) -> str:
        message = data.get("message")
        if isinstance(message, dict):
            return str(message.get("content", "")).strip()
        return str(data.get("response", "")).strip()

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None,
    ) -> dict[str, Any]:
        url = f"{self.config.base_url}{path}"
        headers = {"Content-Type": "application/json"}
        payload = None
        if body is not None:
            payload = json.dumps(body).encode("utf-8")

        request = urllib.request.Request(url, data=payload, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_s) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise OllamaUnavailableError(f"Ollama HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            self._availability.set(False)
            raise OllamaUnavailableError(f"Could not reach Ollama at {self.config.base_url}") from exc

        if not raw.strip():
            return {}
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise OllamaUnavailableError("Ollama returned invalid JSON.") from exc
        if not isinstance(parsed, dict):
            raise OllamaUnavailableError("Ollama returned an unexpected response shape.")
        return parsed

    def warmup(self) -> None:
        """Load the model into memory so later requests start faster."""
        self.generate("Hi", system="Reply with one word.", max_tokens=4)

    def invalidate_availability_cache(self) -> None:
        """Force the next availability check to hit the network."""
        self._availability.clear()
