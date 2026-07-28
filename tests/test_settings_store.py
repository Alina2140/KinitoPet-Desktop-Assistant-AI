"""Tests for persistent settings store."""

import json
import os

import pytest

from kinito.settings_store import SettingsStore


@pytest.fixture
def settings_dir(tmp_path):
    return str(tmp_path / "user_media")


@pytest.fixture
def store(settings_dir):
    return SettingsStore(directory=settings_dir)


def test_defaults_when_missing(store):
    assert store.get("screen_effects_enabled") is True
    assert store.get("ambient_reminders_enabled") is True
    assert store.get("app_awareness_enabled") is True
    assert store.get("snoring_enabled") is True
    assert store.get("window_grab_enabled") is True
    assert store.get("tts_enabled") is True
    assert store.get_hidden_menu_buttons() == set()


def test_update_and_reload_roundtrip(store, settings_dir):
    store.update(
        screen_effects_enabled=False,
        ambient_reminders_enabled=False,
        app_awareness_enabled=False,
        snoring_enabled=False,
        window_grab_enabled=False,
        tts_enabled=False,
    )
    store.set_hidden_menu_buttons({"main.chat", "actions.hug"})
    reloaded = SettingsStore(directory=settings_dir)
    assert reloaded.get("screen_effects_enabled") is False
    assert reloaded.get("ambient_reminders_enabled") is False
    assert reloaded.get("app_awareness_enabled") is False
    assert reloaded.get("snoring_enabled") is False
    assert reloaded.get("window_grab_enabled") is False
    assert reloaded.get("tts_enabled") is False
    assert reloaded.get_hidden_menu_buttons() == {"main.chat", "actions.hug"}


def test_invalid_file_falls_back_to_defaults(settings_dir):
    os.makedirs(settings_dir, exist_ok=True)
    path = os.path.join(settings_dir, "settings.json")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("{not-json")
    store = SettingsStore(directory=settings_dir)
    assert store.get("screen_effects_enabled") is True


def test_ignores_unknown_keys(store):
    store.update(screen_effects_enabled=False, not_a_real_setting=False)
    with open(store._path, encoding="utf-8") as handle:
        raw = json.load(handle)
    assert "not_a_real_setting" not in raw
    assert raw["screen_effects_enabled"] is False
