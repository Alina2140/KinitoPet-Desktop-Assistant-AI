from unittest.mock import MagicMock, patch

import pytest

from kinito.features.media import MediaMixin


class MediaStub(MediaMixin):
    MEDIA_WIDTH = 720
    MEDIA_HEIGHT = 540


@pytest.fixture
def media():
    stub = MediaStub()
    stub._media_active = False
    stub._running = True
    stub.speak = MagicMock()
    stub.root = MagicMock()
    stub.root.update_idletasks = MagicMock()
    stub.root.winfo_rootx.return_value = 100
    stub.root.winfo_rooty.return_value = 200
    stub.root.winfo_width.return_value = 150
    stub.get_screen_bounds = MagicMock(return_value=(0, 0, 800, 600))
    stub._is_busy_with_speech = MagicMock(return_value=False)
    return stub


def test_show_random_media_skips_when_nothing_available(media):
    with (
        patch("kinito.features.media.list_allowed_images", return_value=[]),
        patch("kinito.features.media.pick_random_video", return_value=None),
    ):
        media.show_random_media()
    media.speak.assert_not_called()


def test_show_random_media_opens_image(media):
    with (
        patch("kinito.features.media.list_allowed_images", return_value=["C:/safe/cat.png"]),
        patch("kinito.features.media.pick_random_video", return_value=None),
        patch.object(media, "show_allowed_image") as show_image,
        patch("kinito.features.media.random.choice", return_value="image"),
    ):
        media.show_random_media()
    show_image.assert_called_once_with(quiet=True)


def test_show_allowed_image_without_files(media):
    with patch("kinito.features.media.pick_random_image", return_value=None):
        media.show_allowed_image()
    media.speak.assert_called_once()


def test_show_allowed_image_launches_thread(media):
    with (
        patch("kinito.features.media.pick_random_image", return_value="C:/safe/cat.png"),
        patch("kinito.features.media.is_allowed_image_path", return_value=True),
        patch("kinito.features.media.threading.Thread") as thread_cls,
    ):
        media.show_allowed_image()
    thread_cls.assert_called_once()
    assert thread_cls.call_args.kwargs["target"] == media._launch_image


def test_show_allowed_video_without_sources(media):
    with patch("kinito.features.media.pick_random_video", return_value=None):
        media.show_allowed_video()
    media.speak.assert_called_once()


def test_show_allowed_video_rejects_invalid_local_path(media):
    with patch(
        "kinito.features.media.pick_random_video",
        return_value=("local", "C:/unsafe/video.mp4"),
    ):
        with patch("kinito.features.media.is_allowed_video_path", return_value=False):
            media.show_allowed_video()
    media.speak.assert_called_once()


def test_close_media_terminates_running_process(media):
    process = MagicMock()
    process.poll.return_value = None
    media._media_process = process
    media._finish_media_window = MagicMock()
    media.close_media()
    process.terminate.assert_called_once()
    media._finish_media_window.assert_called_once_with(speak_close=False)
