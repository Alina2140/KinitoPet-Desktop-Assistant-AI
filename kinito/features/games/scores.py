"""Persistent highscores for selected mini-games under UserMedia."""

from __future__ import annotations

import json
import os
import threading
from typing import Any

from kinito.assets import user_media_directory
from kinito.memory.store import _write_text_atomic

SCORES_VERSION = 1
SCORES_FILENAME = "game_scores.json"

# Memory boards track a separate best-move record per pair count.
# Keep in sync with PAIR_OPTIONS / DEFAULT_PAIR_COUNT in memory.py.
_MEMORY_PAIR_OPTIONS = (8, 12, 16)
_MEMORY_DEFAULT_PAIR_COUNT = 16
_LEGACY_MEMORY_BEST_KEY = "memory_best_moves"

# Integer scores; 0 means "no record yet" for lower-is-better keys.
DEFAULT_SCORES: dict[str, int] = {
    "snake_highscore": 0,
    "tetris_highscore": 0,
    **{f"memory_best_moves_{n}": 0 for n in _MEMORY_PAIR_OPTIONS},
    "trivia_best_score": 0,
    "trivia_streak": 0,
    "number_guess_best_attempts": 0,
    "battleships_best_shots": 0,
}

TRIVIA_STREAK_THRESHOLD = 3

# Keys where a lower positive value is better (0 = unset).
_LOW_IS_BETTER_KEYS = frozenset(
    {
        *(f"memory_best_moves_{n}" for n in _MEMORY_PAIR_OPTIONS),
        "number_guess_best_attempts",
        "battleships_best_shots",
    }
)


def _normalize_memory_pair_count(pair_count: int | None) -> int:
    """Clamp *pair_count* to a supported Memory board size."""
    if pair_count in _MEMORY_PAIR_OPTIONS:
        return int(pair_count)
    return _MEMORY_DEFAULT_PAIR_COUNT


def _memory_best_key(pair_count: int | None) -> str:
    """Return the scores key for the given Memory pair count."""
    return f"memory_best_moves_{_normalize_memory_pair_count(pair_count)}"


def scores_file_path(directory: str | None = None) -> str:
    """Return the path to the JSON game-scores file."""
    base = directory or user_media_directory
    return os.path.join(base, SCORES_FILENAME)


class GameScoresStore:
    """Load and persist mini-game highscores under GameAssets/UserMedia/."""

    def __init__(self, directory: str | None = None) -> None:
        self._directory = directory or user_media_directory
        self._path = scores_file_path(self._directory)
        self._data: dict[str, Any] = self._empty_data()
        self._lock = threading.RLock()
        self.load()

    @staticmethod
    def _empty_data() -> dict[str, Any]:
        return {"version": SCORES_VERSION, **DEFAULT_SCORES}

    def load(self) -> None:
        """Load scores from disk, or start with defaults if missing/invalid."""
        if not os.path.isfile(self._path):
            self._data = self._empty_data()
            return
        try:
            with open(self._path, encoding="utf-8") as handle:
                raw = json.load(handle)
        except (OSError, json.JSONDecodeError, TypeError):
            self._data = self._empty_data()
            return
        if not isinstance(raw, dict):
            self._data = self._empty_data()
            return
        self._data = self._normalize_loaded(raw)

    def save(self) -> None:
        """Persist scores atomically."""
        with self._lock:
            os.makedirs(self._directory, exist_ok=True)
            payload = json.dumps(self._data, ensure_ascii=False, indent=2)
            _write_text_atomic(self._path, payload)

    def _normalize_loaded(self, raw: dict[str, Any]) -> dict[str, Any]:
        data = self._empty_data()
        for key, default in DEFAULT_SCORES.items():
            value = raw.get(key, default)
            if isinstance(value, bool):
                data[key] = default
            elif isinstance(value, int):
                data[key] = max(0, value)
            elif isinstance(value, float) and value.is_integer():
                data[key] = max(0, int(value))
            else:
                data[key] = default
        self._migrate_legacy_memory_best(raw, data)
        return data

    @staticmethod
    def _migrate_legacy_memory_best(raw: dict[str, Any], data: dict[str, Any]) -> None:
        """Move a pre-split Memory best onto the default board if needed."""
        legacy = raw.get(_LEGACY_MEMORY_BEST_KEY)
        if isinstance(legacy, bool):
            return
        if isinstance(legacy, float) and legacy.is_integer():
            legacy = int(legacy)
        if not isinstance(legacy, int) or legacy <= 0:
            return
        default_key = _memory_best_key(_MEMORY_DEFAULT_PAIR_COUNT)
        if data.get(default_key, 0) == 0:
            data[default_key] = legacy

    def get(self, key: str) -> int:
        """Return an integer score value (0 if unknown)."""
        if key in self._data and isinstance(self._data[key], int):
            return max(0, self._data[key])
        return int(DEFAULT_SCORES.get(key, 0))

    def snake_highscore(self) -> int:
        """Return the best Snake score."""
        return self.get("snake_highscore")

    def record_snake_score(self, score: int) -> bool:
        """Update Snake highscore if *score* is higher. Return True on new best."""
        score = max(0, int(score))
        current = self.snake_highscore()
        if score <= current:
            return False
        with self._lock:
            self._data["snake_highscore"] = score
            self.save()
        return True

    def tetris_highscore(self) -> int:
        """Return the best Tetris score."""
        return self.get("tetris_highscore")

    def record_tetris_score(self, score: int) -> bool:
        """Update Tetris highscore if *score* is higher. Return True on new best."""
        score = max(0, int(score))
        current = self.tetris_highscore()
        if score <= current:
            return False
        with self._lock:
            self._data["tetris_highscore"] = score
            self.save()
        return True

    def memory_best_moves(self, pair_count: int | None = None) -> int | None:
        """Return best (lowest) Memory moves for *pair_count*, or None if unset."""
        return self._get_low_best(_memory_best_key(pair_count))

    def record_memory_moves(self, moves: int, pair_count: int | None = None) -> bool:
        """Update Memory best for *pair_count* if *moves* is a new low."""
        return self._record_low_best(_memory_best_key(pair_count), moves)

    def number_guess_best_attempts(self) -> int | None:
        """Return fewest Number Guess attempts on a win, or None if unset."""
        return self._get_low_best("number_guess_best_attempts")

    def record_number_guess_attempts(self, attempts: int) -> bool:
        """Update Number Guess best if *attempts* is a new low. Return True on new best."""
        return self._record_low_best("number_guess_best_attempts", attempts)

    def battleships_best_shots(self) -> int | None:
        """Return fewest Battleships shots on a win, or None if unset."""
        return self._get_low_best("battleships_best_shots")

    def record_battleships_shots(self, shots: int) -> bool:
        """Update Battleships best if *shots* is a new low. Return True on new best."""
        return self._record_low_best("battleships_best_shots", shots)

    def _get_low_best(self, key: str) -> int | None:
        """Return a lower-is-better score, or None if unset."""
        value = self.get(key)
        return value if value > 0 else None

    def _record_low_best(self, key: str, value: int) -> bool:
        """Store *value* when it beats the previous low for *key*."""
        if key not in _LOW_IS_BETTER_KEYS:
            return False
        value = max(1, int(value))
        current = self._get_low_best(key)
        if current is not None and value >= current:
            return False
        with self._lock:
            self._data[key] = value
            self.save()
        return True

    def trivia_best_score(self) -> int:
        """Return the best True-or-False round score."""
        return self.get("trivia_best_score")

    def trivia_streak(self) -> int:
        """Return consecutive winning trivia rounds (score >= threshold)."""
        return self.get("trivia_streak")

    def record_trivia_score(
        self,
        score: int,
        *,
        total: int = 5,
        win_threshold: int = TRIVIA_STREAK_THRESHOLD,
    ) -> dict[str, int | bool]:
        """Update trivia best/streak. Return summary flags for dialogue."""
        score = max(0, min(int(total), int(score)))
        with self._lock:
            best = self.trivia_best_score()
            new_best = score > best
            if new_best:
                self._data["trivia_best_score"] = score

            if score >= win_threshold:
                streak = self.trivia_streak() + 1
            else:
                streak = 0
            self._data["trivia_streak"] = streak
            self.save()
            return {
                "best": self.trivia_best_score(),
                "streak": streak,
                "new_best": new_best,
            }
