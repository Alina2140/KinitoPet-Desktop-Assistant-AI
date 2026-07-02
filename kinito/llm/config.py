"""Configuration for the local Ollama LLM integration."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class LLMConfig:
    """Runtime settings for Ollama (overridable via environment variables)."""

    base_url: str = "http://127.0.0.1:11434"
    model: str = "llama3.2:3b"
    timeout_s: int = 60
    enabled: bool = True
    idle_lines: bool = True
    idle_chance: float = 0.25
    replace_chance: float = 0.30
    max_history: int = 20
    availability_cache_s: float = 30.0

    @classmethod
    def from_env(cls) -> LLMConfig:
        """Build config from environment variables with sensible defaults."""
        return cls(
            base_url=os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/"),
            model=os.environ.get("OLLAMA_MODEL", "llama3.2:3b"),
            timeout_s=_env_int("OLLAMA_TIMEOUT_S", 60),
            enabled=_env_bool("OLLAMA_ENABLED", True),
            idle_lines=_env_bool("OLLAMA_IDLE_LINES", True),
            idle_chance=_env_float("OLLAMA_IDLE_CHANCE", 0.25),
            replace_chance=_env_float(
                "OLLAMA_REPLACE_CHANCE",
                _env_float("OLLAMA_IDLE_CHANCE", 0.30),
            ),
            max_history=_env_int("OLLAMA_MAX_HISTORY", 20),
            availability_cache_s=_env_float("OLLAMA_AVAILABILITY_CACHE_S", 30.0),
        )


class AvailabilityCache:
    """Short-lived cache for Ollama reachability checks."""

    def __init__(self, ttl_s: float = 30.0) -> None:
        self._ttl_s = ttl_s
        self._available: bool | None = None
        self._checked_at: float = 0.0

    def get(self) -> bool | None:
        """Return cached availability if still fresh, else None."""
        if self._available is None:
            return None
        if time.monotonic() - self._checked_at > self._ttl_s:
            return None
        return self._available

    def set(self, available: bool) -> None:
        """Store a fresh availability result."""
        self._available = available
        self._checked_at = time.monotonic()

    def clear(self) -> None:
        """Invalidate the cache."""
        self._available = None
        self._checked_at = 0.0
