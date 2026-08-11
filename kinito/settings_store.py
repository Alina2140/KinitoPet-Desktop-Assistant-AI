"""File-backed settings for toggles that should survive app restarts."""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Iterable
from typing import Any

from kinito.assets import user_media_directory

SETTINGS_VERSION = 1
SETTINGS_FILENAME = "settings.json"

DEFAULT_BOOL_SETTINGS: dict[str, bool] = {
    "screen_effects_enabled": True,
    "ambient_reminders_enabled": True,
    "app_awareness_enabled": True,
    "screen_comments_enabled": True,
    "paint_recall_enabled": True,
    "snoring_enabled": True,
    "window_grab_enabled": True,
    "tts_enabled": True,
    "special_days_enabled": True,
    "emoji_picker_enabled": True,
    "mood_system_enabled": True,
}

# Back-compat alias used by older tests/imports.
DEFAULT_SETTINGS = DEFAULT_BOOL_SETTINGS

HIDDEN_MENU_BUTTONS_KEY = "hidden_menu_buttons"


def settings_file_path(directory: str | None = None) -> str:
    """Return the path to the JSON settings file."""
    base = directory or user_media_directory
    return os.path.join(base, SETTINGS_FILENAME)


def _atomic_replace(temp_path: str, final_path: str) -> None:
    """Replace *final_path* atomically; retry once on Windows file locks."""
    try:
        os.replace(temp_path, final_path)
    except PermissionError:
        if sys.platform != "win32":
            raise
        if os.path.isfile(final_path):
            os.remove(final_path)
        os.replace(temp_path, final_path)


class SettingsStore:
    """Load and persist assistant settings under GameAssets/UserMedia/."""

    def __init__(self, directory: str | None = None) -> None:
        self._directory = directory or user_media_directory
        self._path = settings_file_path(self._directory)
        self._data: dict[str, Any] = self._empty_data()
        self.load()

    @staticmethod
    def _empty_data() -> dict[str, Any]:
        return {
            "version": SETTINGS_VERSION,
            **DEFAULT_BOOL_SETTINGS,
            HIDDEN_MENU_BUTTONS_KEY: [],
        }

    def load(self) -> None:
        """Load settings from disk, or start with defaults if missing/invalid."""
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
        """Persist settings atomically."""
        os.makedirs(self._directory, exist_ok=True)
        temp_path = f"{self._path}.tmp"
        payload = json.dumps(self._data, ensure_ascii=False, indent=2)
        with open(temp_path, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        _atomic_replace(temp_path, self._path)

    def _normalize_loaded(self, raw: dict[str, Any]) -> dict[str, Any]:
        data = self._empty_data()
        for key in DEFAULT_BOOL_SETTINGS:
            value = raw.get(key, DEFAULT_BOOL_SETTINGS[key])
            data[key] = bool(value) if isinstance(value, bool) else DEFAULT_BOOL_SETTINGS[key]
        hidden = raw.get(HIDDEN_MENU_BUTTONS_KEY, [])
        if isinstance(hidden, list):
            data[HIDDEN_MENU_BUTTONS_KEY] = [
                str(item) for item in hidden if isinstance(item, str) and item
            ]
        else:
            data[HIDDEN_MENU_BUTTONS_KEY] = []
        return data

    def get(self, key: str, default: bool | None = None) -> bool:
        """Return a boolean setting, falling back to *default* or built-in default."""
        if key in self._data and isinstance(self._data[key], bool):
            return self._data[key]
        if default is not None:
            return default
        return bool(DEFAULT_BOOL_SETTINGS.get(key, False))

    def update(self, **values: bool) -> None:
        """Update known boolean settings and save immediately."""
        changed = False
        for key, value in values.items():
            if key not in DEFAULT_BOOL_SETTINGS:
                continue
            coerced = bool(value)
            if self._data.get(key) != coerced:
                self._data[key] = coerced
                changed = True
        if changed or not os.path.isfile(self._path):
            self.save()

    def get_hidden_menu_buttons(self) -> set[str]:
        """Return stable ids of menu buttons the user has hidden."""
        raw = self._data.get(HIDDEN_MENU_BUTTONS_KEY, [])
        if not isinstance(raw, list):
            return set()
        return {str(item) for item in raw if isinstance(item, str) and item}

    def set_hidden_menu_buttons(self, button_ids: Iterable[str]) -> None:
        """Persist the set of hidden menu button ids."""
        cleaned = sorted({str(item) for item in button_ids if str(item)})
        if self._data.get(HIDDEN_MENU_BUTTONS_KEY) == cleaned:
            return
        self._data[HIDDEN_MENU_BUTTONS_KEY] = cleaned
        self.save()
