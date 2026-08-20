"""Tests for ephemeral screen commentary."""

from unittest.mock import MagicMock, patch

import pytest

from content import dialogue as dlg
from kinito.features.screen_comments import ScreenCommentsMixin


class ScreenCommentStub(ScreenCommentsMixin):
    pass


@pytest.fixture
def screen_comments():
    stub = ScreenCommentStub()
    stub._running = True
    stub._screen_comments_enabled = True
    stub._last_screen_comment_at = 0.0
    stub.paused = False
    stub.is_dragging = False
    stub._camera_active = False
    stub._browser_active = False
    stub._focus_mode = False
    stub.root = MagicMock()
    stub.root.after = MagicMock()
    stub.speak = MagicMock()
    stub._is_busy_with_speech = MagicMock(return_value=False)
    stub._is_game_active = MagicMock(return_value=False)
    stub._ollama_client = MagicMock()
    stub._ollama_client.is_available.return_value = False
    stub._persist_settings = MagicMock()
    return stub


def test_maybe_trigger_respects_disabled(screen_comments):
    screen_comments._screen_comments_enabled = False
    assert screen_comments.maybe_trigger_screen_comment() is False
    screen_comments.root.after.assert_not_called()


def test_maybe_trigger_respects_focus_mode(screen_comments):
    screen_comments._focus_mode = True
    assert screen_comments.maybe_trigger_screen_comment() is False


def test_maybe_trigger_respects_busy(screen_comments):
    screen_comments._is_busy_with_speech.return_value = True
    assert screen_comments.maybe_trigger_screen_comment() is False


def test_maybe_trigger_respects_cooldown(screen_comments):
    import time

    screen_comments._last_screen_comment_at = time.monotonic()
    with patch("kinito.features.screen_comments.random.random", return_value=0.0):
        assert screen_comments.maybe_trigger_screen_comment() is False


def test_screen_comment_cooldown_is_nudge_scale():
    assert ScreenCommentsMixin.SCREEN_COMMENT_COOLDOWN_SECONDS >= 300


def test_maybe_trigger_schedules_on_hit(screen_comments):
    with patch("kinito.features.screen_comments.random.random", return_value=0.0):
        assert screen_comments.maybe_trigger_screen_comment() is True
    screen_comments.root.after.assert_called_once()
    assert screen_comments.root.after.call_args.args[1] == screen_comments._start_screen_comment


def test_maybe_trigger_allows_zero_sentinel_on_fresh_boot(screen_comments):
    """0.0 means never triggered — must not collide with low uptime clocks."""
    screen_comments._last_screen_comment_at = 0.0
    with (
        patch("kinito.features.screen_comments.random.random", return_value=0.0),
        patch("kinito.features.screen_comments.time.monotonic", return_value=60.0),
    ):
        assert screen_comments.maybe_trigger_screen_comment() is True


def test_capture_does_not_save_or_store_on_self(screen_comments):
    fake_image = MagicMock()
    fake_image.convert.return_value = fake_image
    fake_image.size = (1920, 1080)
    fake_image.resize.return_value = fake_image

    def fake_save(buffer, format=None, quality=None):
        buffer.write(b"jpeg-bytes")

    fake_image.save.side_effect = fake_save

    with patch("PIL.ImageGrab.grab", return_value=fake_image) as grab:
        data = screen_comments._capture_screen_jpeg_bytes()

    assert data == b"jpeg-bytes"
    grab.assert_called_once()
    fake_image.save.assert_called_once()
    assert not hasattr(screen_comments, "_last_screenshot")
    # save was only to BytesIO, not a path
    call_kwargs = fake_image.save.call_args
    assert call_kwargs.kwargs.get("format") == "JPEG"
    assert not isinstance(call_kwargs.args[0], str)


def test_vision_comment_uses_client_without_storing_image(screen_comments):
    screen_comments._ollama_client.is_available.return_value = True
    screen_comments._ollama_client.chat_with_image.return_value = "Nice busy desktop!"
    line = screen_comments._vision_screen_comment(b"img")
    assert line == "Nice busy desktop!"
    screen_comments._ollama_client.chat_with_image.assert_called_once()
    assert not hasattr(screen_comments, "_last_screenshot")


def test_worker_falls_back_when_vision_unavailable(screen_comments):
    screen_comments._capture_screen_jpeg_bytes = MagicMock(return_value=b"img")
    screen_comments._vision_screen_comment = MagicMock(return_value=None)
    screen_comments._screen_comment_worker()
    screen_comments.root.after.assert_called()
    spoken = screen_comments.root.after.call_args.args[1]
    # lambda closes over spoken line — invoke it
    spoken()
    screen_comments.speak.assert_called_once()
    assert screen_comments.speak.call_args.kwargs.get("skip_ai") is True


def test_toggle_screen_comments_disables(screen_comments):
    screen_comments.toggle_screen_comments()
    assert screen_comments._screen_comments_enabled is False
    screen_comments._persist_settings.assert_called_once()
    screen_comments.speak.assert_called_once()
    spoken = screen_comments.speak.call_args.args[0]
    assert spoken in dlg.SCREEN_COMMENTS_OFF_LINES
