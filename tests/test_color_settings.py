"""Tests for the Adjust colors settings (snake color and chat name color)."""

from unittest.mock import MagicMock

from kinito.colors import (
    brightness,
    darken_hex,
    hex_to_rgb,
    lighten_hex,
    normalize_hex_color,
    rgb_to_hex,
)
from kinito.features.color_settings import ColorSettingsMixin
from kinito.features.games.snake_ui import SNAKE_BODY, snake_palette
from kinito.settings_store import DEFAULT_COLOR_SETTINGS
from kinito.speech_chat import SpeechChatMixin


class ColorStub(ColorSettingsMixin, SpeechChatMixin):
    def __init__(self):
        self._persist_settings = MagicMock()


def test_normalize_hex_color():
    assert normalize_hex_color(" #AABBCC ", "#000000") == "#aabbcc"
    assert normalize_hex_color("#abc", "#000000") == "#000000"
    assert normalize_hex_color("red", "#000000") == "#000000"
    assert normalize_hex_color(None, "#000000") == "#000000"


def test_hex_rgb_roundtrip():
    assert hex_to_rgb("#1a2b3c") == (26, 43, 60)
    assert rgb_to_hex(26, 43, 60) == "#1a2b3c"
    assert rgb_to_hex(-5, 300, 128) == "#00ff80"


def test_lighten_hex():
    assert lighten_hex("#000000", 0) == "#000000"
    assert lighten_hex("#000000", 1) == "#ffffff"
    assert lighten_hex("#000000", 0.5) == "#808080"


def test_darken_hex_and_brightness():
    assert darken_hex("#ffffff", 0) == "#ffffff"
    assert darken_hex("#ffffff", 1) == "#000000"
    assert darken_hex("#ffffff", 0.5) == "#808080"
    assert brightness("#000000") == 0
    assert brightness("#ffffff") == 1


def test_snake_palette_head_is_darker_than_body():
    head, body = snake_palette("#3b82f6")
    assert body == "#3b82f6"
    assert head == darken_hex("#3b82f6", 0.45)
    assert brightness(head) < brightness(body)


def test_snake_palette_lightens_head_of_very_dark_body():
    head, body = snake_palette("#111111")
    assert body == "#111111"
    assert brightness(head) > brightness(body)


def test_default_snake_color_matches_game_default():
    assert DEFAULT_COLOR_SETTINGS["snake_color"] == SNAKE_BODY


def test_colors_default_when_unset():
    stub = ColorStub()
    assert stub.snake_color() == DEFAULT_COLOR_SETTINGS["snake_color"]
    assert stub.chat_name_color() == DEFAULT_COLOR_SETTINGS["chat_name_color"]


def test_snake_and_chat_colors_are_independent():
    stub = ColorStub()
    stub.set_snake_color("#EC4899")
    assert stub.snake_color() == "#ec4899"
    assert stub.chat_name_color() == DEFAULT_COLOR_SETTINGS["chat_name_color"]
    stub.set_chat_name_color("#16a34a")
    assert stub.chat_name_color() == "#16a34a"
    assert stub.snake_color() == "#ec4899"
    assert stub._persist_settings.call_count == 2


def test_battleships_color_refreshes_and_persists():
    stub = ColorStub()
    assert stub.battleships_color() == "#7c3aed"
    stub._battleships_game = MagicMock()
    stub.set_battleships_color("#16A34A")
    assert stub.battleships_color() == "#16a34a"
    stub._battleships_game.refresh_player_colors.assert_called_once()
    stub._persist_settings.assert_called_once()
    stub.set_battleships_color("invalid")
    assert stub.battleships_color() == "#16a34a"
    stub.set_battleships_color("rainbow")
    assert stub.battleships_color() == "rainbow"
    assert stub.connect_four_color() == "#7c3aed"


def test_battleships_color_survives_reload(tmp_path):
    from kinito.settings_store import SettingsStore

    store = SettingsStore(directory=str(tmp_path))
    store.update(battleships_color="#0891b2")
    assert SettingsStore(directory=str(tmp_path)).get_str("battleships_color") == "#0891b2"


def test_invalid_color_keeps_previous_choice():
    stub = ColorStub()
    stub.set_snake_color("#ef4444")
    stub.set_snake_color("not a color")
    assert stub.snake_color() == "#ef4444"


def test_chat_name_color_restyles_open_chat_log():
    stub = ColorStub()
    stub._chat_log_widget = MagicMock()
    stub.set_chat_name_color("#dc2626")
    stub._chat_log_widget.tag_configure.assert_called_once_with(
        "chat_user", foreground="#dc2626"
    )


def test_chat_user_color_falls_back_without_color_settings():
    class PlainChat(SpeechChatMixin):
        pass

    assert PlainChat()._chat_user_color() == SpeechChatMixin.CHAT_USER_COLOR
