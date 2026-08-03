"""Tests for the Paint feature: dialogs, save path, tools, gallery."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

from PIL import Image

from content import dialogue as dlg
from content import llm_prompts as prompts
from content import paint_lines
from content.dialog_registry import find_dialog_spec, handle_dialog_response
from kinito.assets import ensure_user_media_directories
from kinito.features.paint import PaintMixin, PaintWindow, _hex_to_rgb


def test_paint_picker_dialog_registered():
    spec = find_dialog_spec(dlg.PAINT_PICKER_QUESTION)
    assert spec is not None
    assert spec.marker == dlg.PAINT_PICKER_MARKER
    assert dlg.BUTTON_PAINT_DRAW in spec.ui.buttons
    assert dlg.BUTTON_PAINT_GALLERY in spec.ui.buttons
    assert dlg.BUTTON_BACK in spec.ui.buttons


def test_handle_menu_paint_opens_picker(mock_app):
    spec = find_dialog_spec(dlg.ACTIONS_MENU_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_PAINT)
    mock_app.offer_paint_picker.assert_called_once()


def test_handle_paint_picker_draw(mock_app):
    spec = find_dialog_spec(dlg.PAINT_PICKER_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_PAINT_DRAW)
    mock_app.open_paint.assert_called_once()


def test_handle_paint_picker_gallery(mock_app):
    spec = find_dialog_spec(dlg.PAINT_PICKER_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_PAINT_GALLERY)
    mock_app.open_paint_gallery.assert_called_once()


def test_paint_prompt_exists():
    assert isinstance(prompts.PAINT_PROMPT, str) and prompts.PAINT_PROMPT.strip()


def test_hex_to_rgb():
    assert _hex_to_rgb("#ff0000") == (255, 0, 0)
    assert _hex_to_rgb("#00ff00") == (0, 255, 0)


def test_ensure_user_media_creates_paintings(tmp_path, monkeypatch):
    media = tmp_path / "UserMedia"
    paints = media / "paintings"
    monkeypatch.setattr("kinito.assets.user_media_directory", str(media))
    monkeypatch.setattr("kinito.assets.paintings_directory", str(paints))
    ensure_user_media_directories()
    assert paints.is_dir()


def test_paint_window_save_writes_png(tmp_path, monkeypatch):
    paints = tmp_path / "paintings"
    paints.mkdir()
    monkeypatch.setattr("kinito.features.paint.paintings_directory", str(paints))
    monkeypatch.setattr(
        "kinito.features.paint.ensure_user_media_directories", lambda: None
    )

    app = MagicMock()
    app.root = MagicMock()
    app.root.after = MagicMock(side_effect=lambda delay, fn, *a: fn(*a) if callable(fn) else None)
    app.speak_paint_line = MagicMock()
    app.window = MagicMock()

    window = PaintWindow(app)
    window.window = MagicMock()
    window._draw.ellipse((10, 10, 40, 40), fill=(0, 0, 0))
    path = window.save()

    assert path is not None
    assert os.path.isfile(path)
    assert path.endswith(".png")
    img = Image.open(path)
    assert img.size == (PaintWindow.CANVAS_W, PaintWindow.CANVAS_H)
    assert window._saved_name == os.path.basename(path)
    window.window.title.assert_called()
    title = window.window.title.call_args.args[0]
    assert title.endswith(" - Paint")
    assert window._saved_name in title
    app.speak_paint_line.assert_called()
    assert app.speak_paint_line.call_args.args[0] in paint_lines.PAINT_SAVE_LINES


def test_paint_window_tools_and_stamp():
    app = MagicMock()
    window = PaintWindow(app)
    window.canvas = MagicMock()
    window._set_tool("pencil")
    window._set_tip("circle", 10)
    window._set_color("#ff0000")
    window._stamp(50, 50)
    window.canvas.create_oval.assert_called()
    pixel = window._image.getpixel((50, 50))
    assert pixel == (255, 0, 0)


def test_paint_window_eraser_uses_white():
    app = MagicMock()
    window = PaintWindow(app)
    window.canvas = MagicMock()
    window._set_color("#000000")
    window._draw.rectangle((0, 0, 20, 20), fill=(0, 0, 0))
    window._set_tool("eraser")
    window._stamp(10, 10)
    assert window._image.getpixel((10, 10)) == (255, 255, 255)


def test_paint_window_commit_shapes():
    app = MagicMock()
    window = PaintWindow(app)
    window.canvas = MagicMock()
    window._set_color("#0000ff")

    window._set_tool("line")
    window._commit_shape(0, 0, 30, 30)
    window.canvas.create_line.assert_called()

    window._set_tool("circle")
    window._commit_shape(5, 5, 40, 40)
    window.canvas.create_oval.assert_called()

    window._set_tool("rect")
    window._commit_shape(5, 5, 40, 40)
    window.canvas.create_rectangle.assert_called()


def test_spray_uses_tip_size_and_throttles():
    app = MagicMock()
    window = PaintWindow(app)
    window.canvas = MagicMock()
    window._set_tool("spray")
    window._set_tip("circle", 4)
    window._set_color("#000000")

    with patch.object(window, "_stamp") as stamp:
        window._spray_at(50, 50)
        first_calls = stamp.call_count
        assert 1 <= first_calls <= 3
        # Same spot / tiny move should be throttled away.
        stamp.reset_mock()
        window._spray_at(51, 50)
        assert stamp.call_count == 0
        # Farther move sprays again.
        window._spray_at(80, 50)
        assert stamp.call_count >= 1


class _GamesStub:
    def _is_game_active(self):
        return False


class _PaintHost(PaintMixin, _GamesStub):
    def __init__(self):
        self.root = MagicMock()
        self.root.after = MagicMock(
            side_effect=lambda delay, fn, *a: fn(*a) if callable(fn) else None
        )
        self.speak = MagicMock()
        self._paint_window = None
        self._paint_session = None
        self._paint_gallery_window = None
        self._paint_detail_window = None
        self.show_popup_image = MagicMock()


def test_speak_paint_line_uses_ai_hint():
    host = _PaintHost()
    host.speak_paint_line("Nice strokes!")
    host.speak.assert_called_once_with("Nice strokes!", ai_hint=prompts.PAINT_PROMPT)


def test_offer_paint_picker_speaks_question():
    host = _PaintHost()
    host.offer_paint_picker()
    host.speak.assert_called_once_with(dlg.PAINT_PICKER_QUESTION, 45, True)


def test_open_paint_gallery_empty(tmp_path, monkeypatch):
    paints = tmp_path / "paintings"
    paints.mkdir()
    monkeypatch.setattr("kinito.features.paint.paintings_directory", str(paints))
    monkeypatch.setattr(
        "kinito.features.paint.ensure_user_media_directories", lambda: None
    )
    host = _PaintHost()
    host.open_paint_gallery()
    assert host.speak.call_args.args[0] in paint_lines.PAINT_GALLERY_EMPTY_LINES
    assert host.speak.call_args.kwargs.get("ai_hint") == prompts.PAINT_PROMPT


def test_open_paint_gallery_with_files(tmp_path, monkeypatch):
    paints = tmp_path / "paintings"
    paints.mkdir()
    sample = paints / "paint_test.png"
    Image.new("RGB", (8, 8), "red").save(sample)

    monkeypatch.setattr("kinito.features.paint.paintings_directory", str(paints))
    monkeypatch.setattr(
        "kinito.features.paint.ensure_user_media_directories", lambda: None
    )

    host = _PaintHost()
    with patch.object(host, "_show_paint_gallery") as show:
        host.open_paint_gallery()
        show.assert_called_once()
        paths = show.call_args.args[0]
        assert any(p.endswith("paint_test.png") for p in paths)
    assert host.speak.call_args.args[0] in paint_lines.PAINT_GALLERY_OPEN_LINES


def test_is_game_active_when_paint_open():
    host = _PaintHost()
    fake = MagicMock()
    fake.winfo_exists.return_value = True
    host._paint_window = fake
    assert host._is_paint_active() is True
    assert host._is_game_active() is True
    assert host._is_paint_only_active() is True


def test_is_paint_only_active_false_when_real_game():
    class _BusyGame(_GamesStub):
        def _is_game_active(self):
            return True

    class Host(PaintMixin, _BusyGame):
        def __init__(self):
            self._paint_window = MagicMock()
            self._paint_window.winfo_exists.return_value = True

    host = Host()
    assert host._is_paint_active() is True
    assert host._is_paint_only_active() is False


def test_delete_painting_removes_file(tmp_path, monkeypatch):
    paints = tmp_path / "paintings"
    paints.mkdir()
    sample = paints / "paint_delete_me.png"
    Image.new("RGB", (8, 8), "blue").save(sample)
    monkeypatch.setattr("kinito.features.paint.paintings_directory", str(paints))
    monkeypatch.setattr(
        "kinito.features.paint.ensure_user_media_directories", lambda: None
    )

    host = _PaintHost()
    assert sample.is_file()
    os.remove(sample)
    assert host._list_painting_paths() == []


def test_paint_mixin_on_floating_assistant():
    from kinito.app import FloatingAssistant
    from kinito.features.paint import PaintMixin

    assert issubclass(FloatingAssistant, PaintMixin)
    assert hasattr(FloatingAssistant, "offer_paint_picker")
    assert hasattr(FloatingAssistant, "open_paint")
    assert hasattr(FloatingAssistant, "open_paint_gallery")
    assert hasattr(FloatingAssistant, "speak_paint_line")
    assert hasattr(FloatingAssistant, "_is_paint_only_active")


def test_thumbnail_helper(tmp_path):
    from kinito.features.paint import _THUMB_SIZE, _thumbnail_image

    sample = tmp_path / "thumb.png"
    Image.new("RGB", (40, 30), "green").save(sample)
    thumb = _thumbnail_image(str(sample))
    assert thumb is not None
    assert thumb.size == _THUMB_SIZE
    assert _thumbnail_image(str(tmp_path / "missing.png")) is None
