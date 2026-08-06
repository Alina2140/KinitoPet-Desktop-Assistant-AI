"""Tests for spontaneous painting gallery popups."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from content import dialogue as dlg
from kinito.features.paint import PaintMixin


class PaintRecallStub(PaintMixin):
    pass


@pytest.fixture
def paint_recall(tmp_path):
    stub = PaintRecallStub()
    stub.root = MagicMock()
    stub.paused = False
    stub.is_dragging = False
    stub._running = True
    stub._paint_recall_enabled = True
    stub._focus_mode = False
    stub._camera_active = False
    stub._browser_active = False
    stub._is_game_active = MagicMock(return_value=False)
    stub._is_busy_with_speech = MagicMock(return_value=False)
    stub._is_position_locked_by_user = MagicMock(return_value=False)
    stub._persist_settings = MagicMock()
    stub.speak = MagicMock()
    stub._paint_gallery_window = None
    stub._paint_detail_window = None
    stub._paint_recall_popup = None
    stub._last_paint_recall_at = 0.0
    stub._ollama_client = MagicMock()
    stub._ollama_client.is_available.return_value = False

    painting = tmp_path / "paint_test.png"
    Image.new("RGB", (40, 30), color=(200, 100, 50)).save(painting)
    stub._list_painting_paths = MagicMock(return_value=[str(painting)])
    return stub


def test_maybe_trigger_respects_disabled(paint_recall):
    paint_recall._paint_recall_enabled = False
    assert paint_recall.maybe_trigger_paint_recall() is False
    paint_recall.root.after.assert_not_called()


def test_maybe_trigger_respects_empty_gallery(paint_recall):
    paint_recall._list_painting_paths.return_value = []
    with patch("kinito.features.paint.random.random", return_value=0.0):
        assert paint_recall.maybe_trigger_paint_recall() is False


def test_maybe_trigger_respects_cooldown(paint_recall):
    paint_recall._last_paint_recall_at = time.monotonic()
    with patch("kinito.features.paint.random.random", return_value=0.0):
        assert paint_recall.maybe_trigger_paint_recall() is False


def test_maybe_trigger_schedules_on_hit(paint_recall):
    with patch("kinito.features.paint.random.random", return_value=0.0):
        assert paint_recall.maybe_trigger_paint_recall() is True
    paint_recall.root.after.assert_called_once()
    assert paint_recall.root.after.call_args.args[1] == paint_recall._start_paint_recall


def test_worker_falls_back_without_vision(paint_recall):
    path = paint_recall._list_painting_paths()[0]
    paint_recall._present_paint_recall = MagicMock()
    paint_recall._paint_recall_worker(path)
    paint_recall.root.after.assert_called()
    callback = paint_recall.root.after.call_args.args[1]
    callback()
    paint_recall._present_paint_recall.assert_called_once()
    called_path, called_line = paint_recall._present_paint_recall.call_args.args
    assert called_path == path
    assert isinstance(called_line, str) and called_line.strip()


def test_toggle_paint_recall_disables(paint_recall):
    paint_recall.toggle_paint_recall()
    assert paint_recall._paint_recall_enabled is False
    paint_recall._persist_settings.assert_called_once()
    paint_recall.speak.assert_called_once()
    spoken = paint_recall.speak.call_args.args[0]
    assert spoken in dlg.PAINT_RECALL_OFF_LINES
