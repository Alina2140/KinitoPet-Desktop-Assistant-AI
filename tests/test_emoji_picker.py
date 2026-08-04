"""Tests for Kuteken pixel emoji catalog and chat insert helpers."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

from PIL import Image

from kinito.assets import emoji_catalog_path, emoji_sheet_path
from kinito.features.emoji_picker import (
    _py_index_to_tk,
    _tk_index_to_py,
    crop_emoji_tile,
    delete_char_before_cursor,
    insert_emoji_into_entry,
    load_emoji_catalog,
)


def test_load_emoji_catalog_from_assets():
    entries = load_emoji_catalog()
    assert len(entries) >= 100
    first = entries[0]
    assert {"x", "y", "w", "h", "char"} <= set(first)
    assert first["char"]
    assert first["w"] > 0 and first["h"] > 0


def test_utf16_index_roundtrip_for_supplementary_emoji():
    text = "a😀b"
    assert _py_index_to_tk(text, 0) == 0
    assert _py_index_to_tk(text, 1) == 1
    assert _py_index_to_tk(text, 2) == 3  # 😀 is two UTF-16 units
    assert _py_index_to_tk(text, 3) == 4
    assert _tk_index_to_py(text, 3) == 2
    assert _tk_index_to_py(text, 4) == 3


def test_load_emoji_catalog_missing_file(tmp_path: Path):
    assert load_emoji_catalog(tmp_path / "missing.json") == []


def test_load_emoji_catalog_invalid_json(tmp_path: Path):
    path = tmp_path / "bad.json"
    path.write_text("{not-json", encoding="utf-8")
    assert load_emoji_catalog(path) == []


def test_load_emoji_catalog_skips_bad_entries(tmp_path: Path):
    path = tmp_path / "catalog.json"
    path.write_text(
        json.dumps(
            [
                {"x": 0, "y": 0, "w": 24, "h": 24, "char": "😀"},
                {"x": 0, "y": 0, "w": 24, "h": 24},
                "nope",
                {"x": 0, "y": 0, "w": 0, "h": 24, "char": "x"},
            ]
        ),
        encoding="utf-8",
    )
    entries = load_emoji_catalog(path)
    assert len(entries) == 1
    assert entries[0]["char"] == "😀"


def test_crop_emoji_tile_from_sheet():
    assert Path(emoji_sheet_path).is_file()
    entries = load_emoji_catalog()
    sheet = Image.open(emoji_sheet_path).convert("RGBA")
    tile = crop_emoji_tile(sheet, entries[0], display_size=28)
    assert tile is not None
    assert tile.size == (28, 28)


def test_crop_emoji_tile_out_of_bounds():
    sheet = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    assert crop_emoji_tile(sheet, {"x": 0, "y": 0, "w": 24, "h": 24, "char": "😀"}) is None


def test_insert_emoji_into_entry():
    entry = MagicMock()
    entry.winfo_exists.return_value = True
    insert_emoji_into_entry(entry, "😀")
    entry.insert.assert_called_once()
    assert entry.insert.call_args[0][1] == "😀"


def test_insert_emoji_into_entry_noop_when_missing():
    insert_emoji_into_entry(None, "😀")
    entry = MagicMock()
    entry.winfo_exists.return_value = False
    insert_emoji_into_entry(entry, "😀")
    entry.insert.assert_not_called()


def test_delete_char_before_cursor_uses_utf16_indices():
    entry = MagicMock()
    entry.winfo_exists.return_value = True
    entry.selection_present.return_value = False
    entry.get.return_value = "a😀"
    # Cursor after emoji: Tk index 3 (a=1, emoji=2)
    entry.index.return_value = 3
    assert delete_char_before_cursor(entry) == "break"
    entry.delete.assert_called_once_with(1, 3)


def test_delete_char_before_cursor_removes_variation_pair():
    entry = MagicMock()
    entry.winfo_exists.return_value = True
    entry.selection_present.return_value = False
    entry.get.return_value = "❤\ufe0f"
    entry.index.return_value = 2
    assert delete_char_before_cursor(entry) == "break"
    entry.delete.assert_called_once_with(0, 2)


def test_catalog_path_constants():
    assert emoji_catalog_path.endswith("catalog.json")
    assert emoji_sheet_path.endswith("emojis.png")
    assert Path(emoji_catalog_path).is_file()
    assert Path(emoji_sheet_path).is_file()


def test_close_chat_mode_closes_emoji_picker():
    from kinito.speech import SpeechMixin
    from kinito.speech_chat import SpeechChatMixin

    class Stub(SpeechChatMixin, SpeechMixin):
        def send_chat_message(self, text: str) -> None:
            pass

    stub = Stub()
    stub._init_chat_state()
    stub._conversation = MagicMock()
    stub._close_speech_bubble_impl = MagicMock()
    stub._close_emoji_picker = MagicMock()
    stub.close_chat_mode()
    stub._close_emoji_picker.assert_called_once()
