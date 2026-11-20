"""Tests for the Sticky Notes feature: dialogs, store roundtrip, mixin."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from content import dialogue as dlg
from content import llm_prompts as prompts
from content import sticky_notes_lines
from content.dialog_registry import find_dialog_spec, handle_dialog_response
from kinito.features.sticky_notes import (
    NOTE_COLORS,
    NOTE_STYLES,
    StickyNotesMixin,
    _sanitize_note_id,
    delete_note_file,
    load_notes,
    new_note_data,
    save_note,
)


def _patch_notes_dir(monkeypatch, tmp_path):
    notes = tmp_path / "sticky_notes"
    notes.mkdir()
    monkeypatch.setattr(
        "kinito.features.sticky_notes.sticky_notes_directory", str(notes)
    )
    monkeypatch.setattr(
        "kinito.features.sticky_notes.ensure_user_media_directories", lambda: None
    )
    return notes


def test_chat_note_is_saved_with_content_without_speech(tmp_path, monkeypatch):
    _patch_notes_dir(monkeypatch, tmp_path)
    app = MagicMock()
    with patch("kinito.features.sticky_notes.StickyNoteWindow") as window:
        StickyNotesMixin.create_chat_note(app, "Shopping", "Milk\nBread")
    notes = load_notes()
    assert len(notes) == 1
    assert notes[0]["title"] == "Shopping"
    assert notes[0]["text"] == "Milk\nBread"
    window.return_value.open.assert_called_once_with(activate=False)
    app.speak.assert_not_called()


def test_chat_note_save_failure_does_not_open_window():
    with (
        patch("kinito.features.sticky_notes.save_note", return_value=False),
        patch("kinito.features.sticky_notes.StickyNoteWindow") as window,
        pytest.raises(OSError),
    ):
        StickyNotesMixin.create_chat_note(MagicMock(), "Title", "Text")
    window.assert_not_called()


def test_sticky_notes_picker_dialog_registered():
    spec = find_dialog_spec(dlg.STICKY_NOTES_PICKER_QUESTION)
    assert spec is not None
    assert spec.marker == dlg.STICKY_NOTES_PICKER_MARKER
    assert dlg.BUTTON_STICKY_NOTE_NEW in spec.ui.buttons
    assert dlg.BUTTON_STICKY_NOTE_LIST in spec.ui.buttons
    assert dlg.BUTTON_BACK in spec.ui.buttons


def test_handle_menu_sticky_notes_opens_picker(mock_app):
    spec = find_dialog_spec(dlg.ACTIONS_MENU_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_STICKY_NOTES)
    mock_app.offer_sticky_notes_picker.assert_called_once()


def test_handle_sticky_notes_picker_new(mock_app):
    spec = find_dialog_spec(dlg.STICKY_NOTES_PICKER_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_STICKY_NOTE_NEW)
    mock_app.open_sticky_note.assert_called_once()


def test_handle_sticky_notes_picker_list(mock_app):
    spec = find_dialog_spec(dlg.STICKY_NOTES_PICKER_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_STICKY_NOTE_LIST)
    mock_app.open_sticky_notes_list.assert_called_once()


def test_sticky_note_prompt_exists():
    assert isinstance(prompts.STICKY_NOTE_PROMPT, str)
    assert prompts.STICKY_NOTE_PROMPT.strip()


def test_sanitize_note_id():
    assert _sanitize_note_id("abc-123_x") == "abc-123_x"
    assert _sanitize_note_id("../evil") == "evil"
    assert _sanitize_note_id("a/b.json") == "abjson"
    assert _sanitize_note_id("") is None
    assert _sanitize_note_id("...") is None
    assert _sanitize_note_id(None) is None
    assert _sanitize_note_id(123) is None


def test_new_note_data_defaults():
    note = new_note_data()
    assert note["id"]
    assert note["color"] in NOTE_COLORS
    assert note["style"] in NOTE_STYLES
    assert note["text"] == ""


def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    notes = _patch_notes_dir(monkeypatch, tmp_path)
    note = new_note_data(x=100, y=200)
    note["text"] = "hello sticky world"
    assert save_note(note) is True
    files = list(notes.iterdir())
    assert len(files) == 1
    loaded = load_notes()
    assert len(loaded) == 1
    assert loaded[0]["id"] == note["id"]
    assert loaded[0]["text"] == "hello sticky world"
    assert loaded[0]["x"] == 100
    assert loaded[0]["y"] == 200


def test_load_notes_skips_invalid(tmp_path, monkeypatch):
    notes = _patch_notes_dir(monkeypatch, tmp_path)
    (notes / "note_bad.json").write_text("{not json", encoding="utf-8")
    (notes / "note_noid.json").write_text("{}", encoding="utf-8")
    (notes / "other.txt").write_text("hi", encoding="utf-8")
    assert load_notes() == []


def test_load_notes_normalizes_fields(tmp_path, monkeypatch):
    notes = _patch_notes_dir(monkeypatch, tmp_path)
    (notes / "note_weird.json").write_text(
        '{"id": "weird", "text": 42, "color": "neon", "style": "wild", "x": "a"}',
        encoding="utf-8",
    )
    loaded = load_notes()
    assert len(loaded) == 1
    assert loaded[0]["color"] == "yellow"
    assert loaded[0]["style"] == "plain"
    assert loaded[0]["x"] is None


def test_delete_note_file(tmp_path, monkeypatch):
    _patch_notes_dir(monkeypatch, tmp_path)
    note = new_note_data()
    assert save_note(note) is True
    assert delete_note_file(note["id"]) is True
    assert load_notes() == []
    assert delete_note_file(note["id"]) is False
    assert delete_note_file("../x") is False


class _StickyHost(StickyNotesMixin):
    def __init__(self):
        self.root = MagicMock()
        self.root.after = MagicMock(
            side_effect=lambda delay, fn, *a: fn(*a) if callable(fn) else None
        )
        self.speak = MagicMock()
        self.paused = False
        self.is_dragging = False
        self._focus_mode = False
        self._camera_active = False
        self._browser_active = False
        self._sticky_note_windows = {}
        self._sticky_notes_list_window = None
        self._sticky_notes_recall_enabled = True
        self._last_sticky_notes_recall_at = 0.0
        self._is_busy_with_speech = lambda: False
        self._is_game_active = lambda: False


def test_speak_sticky_note_line_uses_ai_hint():
    host = _StickyHost()
    host.speak_sticky_note_line("Sticky!")
    host.speak.assert_called_once_with("Sticky!", ai_hint=prompts.STICKY_NOTE_PROMPT)


def test_offer_sticky_notes_picker_speaks_question():
    host = _StickyHost()
    host.offer_sticky_notes_picker()
    host.speak.assert_called_once_with(dlg.STICKY_NOTES_PICKER_QUESTION, 45, True)


def test_open_sticky_notes_list_empty(tmp_path, monkeypatch):
    _patch_notes_dir(monkeypatch, tmp_path)
    host = _StickyHost()
    host.open_sticky_notes_list()
    assert (
        host.speak.call_args.args[0]
        in sticky_notes_lines.STICKY_NOTE_LIST_EMPTY_LINES
    )
    assert host.speak.call_args.kwargs.get("ai_hint") == prompts.STICKY_NOTE_PROMPT


def test_open_sticky_notes_list_with_notes(tmp_path, monkeypatch):
    _patch_notes_dir(monkeypatch, tmp_path)
    note = new_note_data()
    note["text"] = "buy milk"
    save_note(note)

    host = _StickyHost()
    with patch.object(host, "_show_sticky_notes_list") as show:
        host.open_sticky_notes_list()
        show.assert_called_once()
        notes = show.call_args.args[0]
        assert notes[0]["id"] == note["id"]
    assert (
        host.speak.call_args.args[0]
        in sticky_notes_lines.STICKY_NOTE_LIST_OPEN_LINES
    )


def test_recall_guarded_when_empty(tmp_path, monkeypatch):
    _patch_notes_dir(monkeypatch, tmp_path)
    host = _StickyHost()
    assert host.maybe_trigger_sticky_notes_recall() is False


def test_recall_guarded_when_disabled(tmp_path, monkeypatch):
    _patch_notes_dir(monkeypatch, tmp_path)
    note = new_note_data()
    note["text"] = "remember me"
    save_note(note)
    host = _StickyHost()
    host._sticky_notes_recall_enabled = False
    assert host.maybe_trigger_sticky_notes_recall() is False


def test_recall_forces_presentation(tmp_path, monkeypatch):
    _patch_notes_dir(monkeypatch, tmp_path)
    note = new_note_data()
    note["text"] = "remember me"
    save_note(note)
    host = _StickyHost()
    with patch("kinito.features.sticky_notes.random.random", return_value=0.0):
        with patch.object(host, "_present_sticky_note_recall") as present:
            assert host.maybe_trigger_sticky_notes_recall() is True
            present.assert_called_once()
            assert present.call_args.args[0]["id"] == note["id"]


def test_toggle_sticky_notes_recall():
    host = _StickyHost()
    host._persist_settings = MagicMock()
    assert host._sticky_notes_recall_enabled is True
    host.toggle_sticky_notes_recall()
    assert host._sticky_notes_recall_enabled is False
    assert host.speak.call_args.args[0] in dlg.STICKY_NOTES_RECALL_OFF_LINES
    host.toggle_sticky_notes_recall()
    assert host._sticky_notes_recall_enabled is True
    assert host.speak.call_args.args[0] in dlg.STICKY_NOTES_RECALL_ON_LINES


@pytest.fixture
def note_editor():
    import tkinter as tk

    from kinito.features.sticky_notes import StickyNoteWindow

    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("No display for Tk")
    root.withdraw()
    app = MagicMock()
    app.root = root
    editor = StickyNoteWindow(app, new_note_data())
    editor.open()
    root.update()
    yield editor
    editor._teardown(save=False)
    root.destroy()


def _set_editor_text(editor, value, cursor="end-1c"):
    editor._text.delete("1.0", "end")
    editor._text.insert("1.0", value)
    editor._text.mark_set("insert", cursor)
    editor._text.edit_reset()


@pytest.mark.parametrize(
    ("value", "expected"),
    [("• item", "• item\n• "), ("  ☑ done", "  ☑ done\n  ☐ "),
     ("9. item", "9. item\n10. "), ("  plain", "  plain\n  "),
     ("• ", ""), ("  ☐ ", "☐ ")],
)
def test_note_enter_continues_lists(note_editor, value, expected):
    _set_editor_text(note_editor, value)
    assert note_editor._on_return() == "break"
    assert note_editor._text.get("1.0", "end-1c") == expected
    note_editor._text.edit_undo()
    assert note_editor._text.get("1.0", "end-1c") == value
    note_editor._text.edit_redo()
    assert note_editor._text.get("1.0", "end-1c") == expected


def test_note_list_selection_and_indent(note_editor):
    _set_editor_text(note_editor, "one\ntwo\nthree")
    text = note_editor._text
    text.tag_add("sel", "1.0", "3.0")
    note_editor._apply_list("number")
    assert text.get("1.0", "end-1c") == "1. one\n2. two\nthree"
    note_editor._indent_lines()
    assert text.get("1.0", "end-1c") == "  1. one\n  2. two\nthree"
    note_editor._indent_lines(outdent=True)
    note_editor._apply_list("check")
    assert text.get("1.0", "end-1c") == "☐ one\n☐ two\nthree"
    note_editor._apply_list("check")
    assert text.get("1.0", "end-1c") == "one\ntwo\nthree"


@pytest.mark.parametrize("marker", ["☐", "☑"])
def test_note_checkbox_hover_cursor(note_editor, marker):
    _set_editor_text(note_editor, f"  {marker} milk\ntext ☐ elsewhere")
    text = note_editor._text
    note_editor.window.update()

    def hover(index):
        x, y, width, height = text.bbox(index)
        text.event_generate("<Motion>", x=x + width // 2, y=y + height // 2)
        note_editor.window.update()

    hover("1.2")
    assert text.cget("cursor") == "hand2"
    hover("1.4")
    assert text.cget("cursor") == "xterm"
    hover("1.2")
    text.event_generate("<Leave>")
    assert text.cget("cursor") == "xterm"
    hover("2.5")
    assert text.cget("cursor") == "xterm"
    text.event_generate("<Motion>", x=0, y=0)
    assert text.cget("cursor") == "xterm"
    assert text.get("1.0", "end-1c") == f"  {marker} milk\ntext ☐ elsewhere"


def test_note_checkbox_click_and_roundtrip(note_editor, tmp_path, monkeypatch):
    from types import SimpleNamespace

    _patch_notes_dir(monkeypatch, tmp_path)
    _set_editor_text(note_editor, "  ☐ milk")
    text = note_editor._text
    note_editor.window.update()
    x, y, width, height = text.bbox("1.2")
    note_editor._on_checkbox_click(SimpleNamespace(x=x + width // 2, y=y + height // 2))
    assert text.get("1.0", "end-1c") == "  ☑ milk"
    note_editor._on_checkbox_click(SimpleNamespace(x=0, y=y + height // 2))
    assert text.get("1.0", "end-1c") == "  ☑ milk"
    text.edit_undo()
    assert text.get("1.0", "end-1c") == "  ☐ milk"
    text.edit_redo()
    note_editor.window.update()
    assert note_editor._save_after is not None
    note_editor.save()
    assert load_notes()[0]["text"] == "  ☑ milk"
    for style in NOTE_STYLES:
        note_editor.set_style(style)
        note_editor.set_color("pink")
        assert text.get("1.0", "end-1c") == "  ☑ milk"


@pytest.mark.parametrize(
    ("line", "expected"),
    [("plain", ("", "", "plain")), ("  • item", ("  ", "• ", "item")),
     ("\t☑ done", ("\t", "☑ ", "done")), ("12. text", ("", "12. ", "text")),
     ("x ☐ y", ("", "", "x ☐ y")), ("", ("", "", ""))],
)
def test_note_list_parts(line, expected):
    from kinito.features.sticky_notes import _list_parts

    assert _list_parts(line) == expected


def test_note_menu_keyboard_and_reopen(note_editor, tmp_path, monkeypatch):
    from kinito.features.sticky_notes import StickyNoteWindow

    _patch_notes_dir(monkeypatch, tmp_path)
    _set_editor_text(note_editor, "milk")
    with patch("kinito.features.sticky_notes.Menu.tk_popup"):
        note_editor._show_menu_button()
    menu = note_editor._menu
    assert [menu.entrycget(i, "label") for i in range(menu.index("end") + 1)] == [
        "Color", "Style", "Lists",
    ]
    list_menu = menu.nametowidget(menu.entrycget(2, "menu"))
    assert list_menu.index("end") == 2
    list_menu.invoke(2)
    text = note_editor._text
    assert text.get("1.0", "end-1c") == "☐ milk"
    text.focus_force()
    note_editor.window.update()
    text.event_generate("<Return>")
    text.event_generate("<Tab>")
    note_editor.window.update()
    assert text.get("1.0", "end-1c") == "☐ milk\n  ☐ "
    text.event_generate("<Shift-Tab>")
    note_editor.window.update()
    assert text.get("1.0", "end-1c") == "☐ milk\n☐ "
    text.event_generate("<Shift-Return>")
    note_editor.window.update()
    assert text.get("1.0", "end-1c") == "☐ milk\n☐ \n"
    note_editor.save()
    reopened = StickyNoteWindow(note_editor.app, load_notes()[0])
    try:
        reopened.open()
        assert reopened._text.get("1.0", "end-1c") == text.get("1.0", "end-1c")
        reopened.toggle_collapse()
        reopened.toggle_collapse()
        assert not reopened._collapsed
    finally:
        reopened._teardown(save=False)


def test_note_character_limit_preserved(note_editor, tmp_path, monkeypatch):
    _patch_notes_dir(monkeypatch, tmp_path)
    _set_editor_text(note_editor, "x" * 2000)
    note_editor._apply_list("bullet")
    note_editor.save()
    assert len(load_notes()[0]["text"]) == 2000


def test_note_shift_enter_and_selection_replacement(note_editor):
    _set_editor_text(note_editor, "• hello world", "1.7")
    note_editor._text.tag_add("sel", "1.7", "1.13")
    note_editor._on_return(plain=True)
    assert note_editor._text.get("1.0", "end-1c") == "• hello\n"


def test_sticky_notes_mixin_on_floating_assistant():
    from kinito.app import FloatingAssistant
    from kinito.features.sticky_notes import StickyNotesMixin

    assert issubclass(FloatingAssistant, StickyNotesMixin)
    assert hasattr(FloatingAssistant, "offer_sticky_notes_picker")
    assert hasattr(FloatingAssistant, "open_sticky_note")
    assert hasattr(FloatingAssistant, "open_sticky_notes_list")
    assert hasattr(FloatingAssistant, "speak_sticky_note_line")
    assert hasattr(FloatingAssistant, "toggle_sticky_notes_recall")
