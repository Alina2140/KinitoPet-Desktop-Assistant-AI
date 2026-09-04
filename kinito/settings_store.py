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
    "sound_effects_enabled": True,
    "window_grab_enabled": True,
    "tts_enabled": True,
    "player_focus_enabled": True,
    "special_days_enabled": True,
    "emoji_picker_enabled": True,
    "mood_system_enabled": True,
    "color_guess_voice_enabled": True,
}

# Integer settings (clamped on load/save).
DEFAULT_INT_SETTINGS: dict[str, int] = {
    "tts_volume": 100,
    "music_volume": 75,
}

TTS_VOLUME_MIN = 0
TTS_VOLUME_MAX = 100
TTS_VOLUME_DEFAULT = 100

MUSIC_VOLUME_MIN = 0
MUSIC_VOLUME_MAX = 100
MUSIC_VOLUME_DEFAULT = 75

# Back-compat alias used by older tests/imports.
DEFAULT_SETTINGS = DEFAULT_BOOL_SETTINGS

HIDDEN_MENU_BUTTONS_KEY = "hidden_menu_buttons"
MUSIC_FOLDER_KEY = "music_folder"


def clamp_tts_volume(value: int | float) -> int:
    """Clamp TTS volume to the supported 0–100 range."""
    try:
        volume = int(round(float(value)))
    except (TypeError, ValueError):
        return TTS_VOLUME_DEFAULT
    return max(TTS_VOLUME_MIN, min(TTS_VOLUME_MAX, volume))


def clamp_music_volume(value: int | float) -> int:
    """Clamp music volume to the supported 0–100 range."""
    try:
        volume = int(round(float(value)))
    except (TypeError, ValueError):
        return MUSIC_VOLUME_DEFAULT
    return max(MUSIC_VOLUME_MIN, min(MUSIC_VOLUME_MAX, volume))


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
            **DEFAULT_INT_SETTINGS,
            HIDDEN_MENU_BUTTONS_KEY: [],
            MUSIC_FOLDER_KEY: "",
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
        for key, default in DEFAULT_INT_SETTINGS.items():
            value = raw.get(key, default)
            if key == "tts_volume":
                data[key] = clamp_tts_volume(value if value is not None else default)
            elif key == "music_volume":
                data[key] = clamp_music_volume(value if value is not None else default)
            elif isinstance(value, bool):
                data[key] = default
            elif isinstance(value, int):
                data[key] = value
            elif isinstance(value, float) and value.is_integer():
                data[key] = int(value)
            else:
                data[key] = default
        hidden = raw.get(HIDDEN_MENU_BUTTONS_KEY, [])
        if isinstance(hidden, list):
            data[HIDDEN_MENU_BUTTONS_KEY] = [
                str(item) for item in hidden if isinstance(item, str) and item
            ]
        else:
            data[HIDDEN_MENU_BUTTONS_KEY] = []
        folder = raw.get(MUSIC_FOLDER_KEY, "")
        data[MUSIC_FOLDER_KEY] = str(folder).strip() if isinstance(folder, str) else ""
        return data

    def get(self, key: str, default: bool | None = None) -> bool:
        """Return a boolean setting, falling back to *default* or built-in default."""
        if key in self._data and isinstance(self._data[key], bool):
            return self._data[key]
        if default is not None:
            return default
        return bool(DEFAULT_BOOL_SETTINGS.get(key, False))

    def get_int(self, key: str, default: int | None = None) -> int:
        """Return an integer setting, falling back to *default* or built-in default."""
        if key in self._data and isinstance(self._data[key], int) and not isinstance(
            self._data[key], bool
        ):
            value = self._data[key]
            if key == "tts_volume":
                return clamp_tts_volume(value)
            if key == "music_volume":
                return clamp_music_volume(value)
            return value
        if default is not None:
            return int(default)
        return int(DEFAULT_INT_SETTINGS.get(key, 0))

    def get_str(self, key: str, default: str = "") -> str:
        """Return a string setting such as the music folder path."""
        value = self._data.get(key, default)
        if isinstance(value, str):
            return value
        return default

    def update(self, **values: Any) -> None:
        """Update known boolean/int/string settings and save immediately."""
        changed = False
        for key, value in values.items():
            if key in DEFAULT_BOOL_SETTINGS:
                coerced = bool(value)
                if self._data.get(key) != coerced:
                    self._data[key] = coerced
                    changed = True
            elif key in DEFAULT_INT_SETTINGS:
                if key == "tts_volume":
                    coerced = clamp_tts_volume(value)
                elif key == "music_volume":
                    coerced = clamp_music_volume(value)
                else:
                    try:
                        coerced = int(value)
                    except (TypeError, ValueError):
                        continue
                if self._data.get(key) != coerced:
                    self._data[key] = coerced
                    changed = True
            elif key == MUSIC_FOLDER_KEY:
                coerced = str(value).strip() if value is not None else ""
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

    def get_music_folder(self) -> str:
        """Return the persisted music playlist folder path."""
        return self.get_str(MUSIC_FOLDER_KEY, "")

    def set_music_folder(self, folder: str) -> None:
        """Persist the music playlist folder path."""
        self.update(**{MUSIC_FOLDER_KEY: folder})
