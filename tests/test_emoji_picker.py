"""Tests for Kuteken pixel emoji catalog and chat insert helpers."""

from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from unittest.mock import MagicMock

from PIL import Image

import kinito.features.emoji_picker as emoji_picker_module
from kinito.assets import emoji_catalog_path, emoji_sheet_path
from kinito.features.emoji_picker import (
    TK_SAFE_WHITE,
    _py_index_to_tk,
    _tk_index_to_py,
    crop_emoji_tile,
    delete_char_before_cursor,
    flatten_for_transparent_bubble,
    insert_emoji_into_entry,
    load_emoji_catalog,
    normalize_emoji_char,
    warm_emoji_glyph_cache,
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
    assert tile.mode == "RGB"
    # No pure white — would punch through the bubble's transparentcolor.
    assert (255, 255, 255) not in {tile.getpixel((x, y)) for y in range(tile.height) for x in range(tile.width)}


def test_flatten_for_transparent_bubble_remaps_white_and_fills_alpha():
    src = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
    src.putpixel((1, 1), (255, 255, 255, 255))
    src.putpixel((2, 2), (240, 206, 105, 255))
    flat = flatten_for_transparent_bubble(src, background=(255, 248, 231))
    assert flat.mode == "RGB"
    assert flat.getpixel((0, 0)) == (255, 248, 231)
    assert flat.getpixel((1, 1)) == TK_SAFE_WHITE
    assert flat.getpixel((2, 2)) == (240, 206, 105)


def test_crop_emoji_tile_out_of_bounds():
    sheet = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    assert crop_emoji_tile(sheet, {"x": 0, "y": 0, "w": 24, "h": 24, "char": "😀"}) is None


def test_normalize_emoji_char_strips_variation_selectors():
    assert normalize_emoji_char("❤️") == "❤"
    assert normalize_emoji_char("🧡") == "🧡"
    assert normalize_emoji_char("😀") == "😀"
    assert normalize_emoji_char("") == ""


def test_insert_emoji_into_entry():
    entry = MagicMock()
    entry.winfo_exists.return_value = True
    insert_emoji_into_entry(entry, "😀")
    entry.insert.assert_called_once()
    assert entry.insert.call_args[0][1] == "😀"


def test_insert_red_heart_strips_fe0f_for_tk_spacing():
    entry = MagicMock()
    entry.winfo_exists.return_value = True
    insert_emoji_into_entry(entry, "❤️")
    entry.insert.assert_called_once()
    assert entry.insert.call_args[0][1] == "❤"


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


def test_warm_emoji_glyph_cache_noop_without_parent():
    warm_emoji_glyph_cache(None, ("Tahoma", 10), chars="😀")
    parent = MagicMock()
    parent.winfo_exists.return_value = False
    warm_emoji_glyph_cache(parent, ("Tahoma", 10), chars="😀")


def test_warm_emoji_glyph_cache_renders_offscreen_and_destroys(monkeypatch):
    parent = MagicMock()
    parent.winfo_exists.return_value = True
    label = MagicMock()
    created = []

    def fake_label(p, **kwargs):
        assert p is parent
        created.append(kwargs)
        return label

    monkeypatch.setattr(emoji_picker_module.tk, "Label", fake_label)
    warm_emoji_glyph_cache(parent, [("Tahoma", 10), ("Tahoma", 11)], chars="😀❤")

    assert len(created) == 2
    assert all(kw["text"] == "😀❤" for kw in created)
    assert label.place.call_count == 2
    label.place.assert_called_with(x=-9999, y=-9999)
    assert label.update_idletasks.call_count == 2
    assert label.destroy.call_count == 2


def test_warm_emoji_glyph_cache_swallows_tcl_errors(monkeypatch):
    parent = MagicMock()
    parent.winfo_exists.return_value = True

    def failing_label(*args, **kwargs):
        raise tk.TclError("dead widget")

    monkeypatch.setattr(emoji_picker_module.tk, "Label", failing_label)
    warm_emoji_glyph_cache(parent, ("Tahoma", 10), chars="😀")


def test_warm_emoji_glyph_cache_uses_catalog_chars(monkeypatch):
    parent = MagicMock()
    parent.winfo_exists.return_value = True
    label = MagicMock()
    texts = []

    def fake_label(p, **kwargs):
        texts.append(kwargs["text"])
        return label

    monkeypatch.setattr(emoji_picker_module.tk, "Label", fake_label)
    warm_emoji_glyph_cache(parent, ("Tahoma", 10))

    expected = [normalize_emoji_char(e["char"]) for e in load_emoji_catalog()]
    assert all(ch in texts[0] for ch in expected if ch)
    assert len(expected) >= 100


def test_emoji_font_warmup_runs_once():
    from kinito.features.emoji_picker import EmojiPickerMixin

    stub = EmojiPickerMixin()
    stub._init_emoji_picker_state()
    stub._emoji_dropdown_parent = MagicMock()
    stub._emoji_dropdown_parent.winfo_exists.return_value = True
    stub._chat_entry_font = lambda: ("Tahoma", 10)
    stub._bubble_font = lambda: ("Tahoma", 11)

    calls = []

    original = emoji_picker_module.warm_emoji_glyph_cache
    emoji_picker_module.warm_emoji_glyph_cache = lambda *a, **k: calls.append((a, k))
    try:
        stub._schedule_emoji_font_warmup()
        stub._schedule_emoji_font_warmup()
    finally:
        emoji_picker_module.warm_emoji_glyph_cache = original

    assert len(calls) == 1
    assert calls[0][0][1] == [("Tahoma", 10), ("Tahoma", 11)]


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
