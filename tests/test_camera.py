from unittest.mock import MagicMock, patch

import pytest

from content import dialogue as dlg
from kinito.features.camera import CameraMixin


class CameraStub(CameraMixin):
    pass


@pytest.fixture
def camera():
    stub = CameraStub()
    stub._camera_active = False
    stub._camera_cap = None
    stub._camera_window = None
    stub._camera_label = None
    stub._camera_line_timer = None
    stub._camera_initial_check_id = None
    stub._camera_feed_live = False
    stub._camera_success_streak = 0
    stub._camera_failed_reads = 0
    stub._camera_open_line_spoken = False
    stub.root = MagicMock()
    stub.root.after = MagicMock()
    stub.root.after_cancel = MagicMock()
    stub.speak = MagicMock()
    stub._is_busy_with_speech = MagicMock(return_value=False)
    return stub


def test_open_camera_without_opencv(camera):
    with patch.dict("sys.modules", {"cv2": None}):
        with patch("builtins.__import__", side_effect=ImportError("no cv2")):
            camera.open_camera()
    assert camera._camera_active is False
    camera.speak.assert_called_once()


def test_open_camera_failure_releases_capture(camera):
    fake_cv2 = MagicMock()
    cap = MagicMock()
    cap.isOpened.return_value = False
    fake_cv2.VideoCapture.return_value = cap
    fake_cv2.CAP_DSHOW = 700

    with patch.dict("sys.modules", {"cv2": fake_cv2}):
        camera.open_camera()

    assert cap.release.called
    assert camera._camera_active is False
    camera.speak.assert_called()


def test_close_camera_releases_and_destroys_window(camera):
    cap = MagicMock()
    window = MagicMock()
    window.winfo_exists.return_value = True
    camera._camera_active = True
    camera._camera_cap = cap
    camera._camera_window = window
    camera._camera_line_timer = 42
    camera._speak_camera_comment = MagicMock()

    camera.close_camera()

    cap.release.assert_called_once()
    window.destroy.assert_called_once()
    assert camera._camera_cap is None
    assert camera._camera_window is None
    camera._speak_camera_comment.assert_called_once_with(dlg.CAMERA_CLOSE_LINES)


def test_speak_camera_comment_retries_while_busy(camera):
    camera._camera_active = True
    camera._is_busy_with_speech.return_value = True
    camera._try_speak_pending_camera_comment = MagicMock()

    camera._speak_camera_comment(dlg.CAMERA_OPEN_LINES)

    assert camera._pending_camera_lines is dlg.CAMERA_OPEN_LINES
    camera._try_speak_pending_camera_comment.assert_called_once()


def test_open_camera_when_already_active_speaks_hint(camera):
    camera._camera_active = True
    camera._speak_camera_comment = MagicMock()

    camera.open_camera()

    camera._speak_camera_comment.assert_called_once_with(dlg.CAMERA_ALREADY_OPEN_LINES)


def test_update_camera_frame_stops_on_read_error(camera):
    fake_cv2 = MagicMock()
    fake_cv2.error = Exception
    cap = MagicMock()
    cap.read.side_effect = fake_cv2.error("read failed")
    camera._camera_active = True
    camera._camera_cap = cap
    camera.close_camera = MagicMock()

    with patch.dict("sys.modules", {"cv2": fake_cv2}):
        camera._update_camera_frame()

    camera.close_camera.assert_called_once()


def test_check_camera_initial_signal_comments_when_no_feed(camera):
    camera._camera_active = True
    camera._camera_label = MagicMock()
    camera._speak_camera_comment = MagicMock()

    camera._check_camera_initial_signal()

    assert camera._camera_open_line_spoken is True
    camera._speak_camera_comment.assert_called_once_with(dlg.CAMERA_NO_SIGNAL_LINES)


def test_on_camera_feed_restored_speaks_open_line_first_time(camera):
    camera._camera_active = True
    camera._speak_camera_comment = MagicMock()

    camera._on_camera_feed_restored()

    camera._speak_camera_comment.assert_called_once_with(dlg.CAMERA_OPEN_LINES)
    assert camera._camera_open_line_spoken is True


def test_on_camera_feed_lost_speaks_lost_line(camera):
    camera._camera_active = True
    camera._camera_label = MagicMock()
    camera._speak_camera_comment = MagicMock()

    camera._on_camera_feed_lost()

    camera._speak_camera_comment.assert_called_once_with(dlg.CAMERA_SIGNAL_LOST_LINES)


def test_update_camera_frame_detects_signal_loss(camera):
    fake_cv2 = MagicMock()
    cap = MagicMock()
    cap.read.return_value = (False, None)
    camera._camera_active = True
    camera._camera_cap = cap
    camera._camera_feed_live = True
    camera._camera_failed_reads = CameraMixin.CAMERA_FAILED_READS_TO_LOST - 1
    camera._on_camera_feed_lost = MagicMock()

    with patch.dict("sys.modules", {"cv2": fake_cv2}):
        camera._update_camera_frame()

    camera._on_camera_feed_lost.assert_called_once()
    assert camera._camera_feed_live is False
