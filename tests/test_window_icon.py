"""Tests for shared window icon helpers."""

import os
from unittest.mock import MagicMock, patch

import pytest

from kinito import assets
from kinito.window_icon import apply_window_icon, set_default_window_icon, window_icon_path


def test_window_icon_path_points_to_favicon():
    assert window_icon_path().endswith("Favicon.png")
    assert os.path.isabs(window_icon_path())


@pytest.mark.skipif(
    not os.path.isfile(assets.favicon_path),
    reason="Favicon.png is not present in this checkout",
)
def test_set_default_window_icon_uses_iconphoto():
    root = MagicMock()
    with patch("kinito.window_icon._load_photo") as load_photo:
        photo = MagicMock()
        load_photo.return_value = photo
        set_default_window_icon(root)
    root.iconphoto.assert_called_once_with(True, photo)


def test_apply_window_icon_falls_back_to_ico():
    window = MagicMock()
    with patch("kinito.window_icon._load_photo", return_value=None):
        with patch("kinito.window_icon.os.path.isfile", return_value=True):
            apply_window_icon(window)
    window.iconbitmap.assert_called_once_with(assets.icon_path)
