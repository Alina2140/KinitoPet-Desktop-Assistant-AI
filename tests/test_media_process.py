from unittest.mock import MagicMock, patch

from content.media_validator import is_allowed_video_url
from kinito.features.media_process import run_video_window


def test_run_video_window_blocks_disallowed_url():
    with patch("kinito.features.media_process.webview", create=True):
        assert run_video_window("https://evil.example.com/", 0, 0, 640, 480) == 1


def test_run_video_window_opens_allowed_url():
    url = "https://science.nasa.gov/earth/earth-at-night/"
    assert is_allowed_video_url(url) is True
    mock_webview = MagicMock()
    with patch.dict("sys.modules", {"webview": mock_webview}):
        with patch("kinito.features.media_process.browser_window_icon_path", return_value=None):
            result = run_video_window(url, 10, 20, 640, 480)
    assert result == 0
    mock_webview.create_window.assert_called_once()
    mock_webview.start.assert_called_once()
