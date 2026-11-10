"""Tests for Kinito's paint requests (draw a subject for him)."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from content import dialogue as dlg
from content import paint_request_lines
from content.dialog_registry import find_dialog_spec, handle_dialog_response
from kinito.features.paint import PaintMixin, PaintWindow


class PaintRequestStub(PaintMixin):
    pass


@pytest.fixture
def paint_request():
    stub = PaintRequestStub()
    stub.root = MagicMock()
    stub.paused = False
    stub.is_dragging = False
    stub._running = True
    stub._paint_requests_enabled = True
    stub._focus_mode = False
    stub._camera_active = False
    stub._browser_active = False
    stub._is_game_active = MagicMock(return_value=False)
    stub._is_busy_with_speech = MagicMock(return_value=False)
    stub._is_position_locked_by_user = MagicMock(return_value=False)
    stub._is_paint_active = MagicMock(return_value=False)
    stub._persist_settings = MagicMock()
    stub.speak = MagicMock()
    stub.speak_paint_line = MagicMock()
    stub._last_paint_request_at = 0.0
    stub._ollama_client = MagicMock()
    stub._ollama_client.is_available.return_value = False
    return stub


def test_maybe_trigger_respects_disabled(paint_request):
    paint_request._paint_requests_enabled = False
    assert paint_request.maybe_trigger_paint_request() is False
    paint_request.root.after.assert_not_called()


def test_maybe_trigger_respects_paint_active(paint_request):
    paint_request._is_paint_active.return_value = True
    with patch("kinito.features.paint.random.random", return_value=0.0):
        assert paint_request.maybe_trigger_paint_request() is False


def test_maybe_trigger_respects_cooldown(paint_request):
    paint_request._last_paint_request_at = time.monotonic()
    with patch("kinito.features.paint.random.random", return_value=0.0):
        assert paint_request.maybe_trigger_paint_request() is False


def test_maybe_trigger_schedules_request(paint_request):
    with patch("kinito.features.paint.random.random", return_value=0.0):
        assert paint_request.maybe_trigger_paint_request() is True
    paint_request.root.after.assert_called_once()


def test_start_paint_request_speaks_and_opens(paint_request):
    with (
        patch("kinito.features.paint.random.choices") as choices,
        patch("kinito.features.paint.random.choice", side_effect=lambda p: p[0]),
        patch("kinito.features.paint.PaintWindow") as window_cls,
    ):
        choices.return_value = [("best_friend", "your best friend", 3)]
        paint_request._start_paint_request()
        line = paint_request.speak_paint_line.call_args.args[0]
        assert line in paint_request_lines.PAINT_REQUEST_LINES["best_friend"]
        # Window creation deferred onto the UI thread.
        callback = paint_request.root.after.call_args.args[1]
        callback()
        subject = window_cls.call_args.args[1]
        assert subject["id"] == "best_friend"
        window_cls.return_value.open.assert_called_once()


def _window(subject, *, dirty=False, saved=None):
    win = PaintWindow(MagicMock(), subject)
    win._dirty = dirty
    win._saved_name = saved
    return win


def test_subject_close_line_abandoned():
    win = _window({"id": "me", "title": "me (Kinito!)"})
    assert win._subject_close_line() in paint_request_lines.PAINT_REQUEST_ABANDONED_LINES


def test_subject_close_line_unsaved():
    win = _window({"id": "me", "title": "me (Kinito!)"}, dirty=True)
    assert win._subject_close_line() in paint_request_lines.PAINT_REQUEST_UNSAVED_LINES


def test_subject_close_line_none_when_saved_or_no_subject():
    win = _window({"id": "me", "title": "me (Kinito!)"}, saved="paint_x.png")
    assert win._subject_close_line() is None
    assert _window(None, dirty=True)._subject_close_line() is None


def test_window_title_includes_subject():
    win = _window({"id": "fear", "title": "your biggest fear"})
    assert win._window_title() == "draw: your biggest fear - Paint"
    assert _window(None)._window_title() == "untitled - Paint"


def test_vision_looks_like_kinito_parsing(paint_request):
    client = paint_request._ollama_client
    client.is_available.return_value = True
    client.chat_with_image.return_value = "YES"
    assert paint_request._vision_looks_like_kinito(b"x") is True
    client.chat_with_image.return_value = "no, not really"
    assert paint_request._vision_looks_like_kinito(b"x") is False
    client.chat_with_image.return_value = "it's a house"
    assert paint_request._vision_looks_like_kinito(b"x") is None
    client.is_available.return_value = False
    assert paint_request._vision_looks_like_kinito(b"x") is None


def test_defer_best_friend_question_speaks_when_idle(paint_request):
    win = _window({"id": "best_friend", "title": "your best friend"})
    win.app = paint_request
    win._defer_best_friend_question()
    paint_request.speak.assert_called_once_with(dlg.WHO_BEST_FRIEND_QUESTION, 45, True)


def test_defer_best_friend_question_waits_when_busy(paint_request):
    paint_request._is_busy_with_speech.return_value = True
    win = _window({"id": "best_friend", "title": "your best friend"})
    win.app = paint_request
    win._defer_best_friend_question()
    paint_request.speak.assert_not_called()
    paint_request.root.after.assert_called_once()


def test_best_friend_question_kinito_answer(mock_app):
    spec = find_dialog_spec(dlg.WHO_BEST_FRIEND_QUESTION)
    handle_dialog_response(mock_app, spec, "Kinito, obviously")
    line = mock_app.speak.call_args.args[0]
    assert line in [
        template.format(response="Kinito, obviously")
        for template in paint_request_lines.BEST_FRIEND_IS_ME_LINES
    ]


def test_best_friend_question_other_answer(mock_app):
    spec = find_dialog_spec(dlg.WHO_BEST_FRIEND_QUESTION)
    handle_dialog_response(mock_app, spec, "Sarah")
    line = mock_app.speak.call_args.args[0]
    assert line in [
        template.format(response="Sarah")
        for template in paint_request_lines.BEST_FRIEND_NOT_ME_LINES
    ]
    mock_app._memory.set_fact.assert_called_once_with("best_friend", "Sarah")
