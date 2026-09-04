"""Tests for staged child-Toplevel helpers."""

from unittest.mock import MagicMock, patch

import kinito.tk_toplevels as tops


def test_create_staged_toplevel_withdraws_and_parks_offscreen():
    root = MagicMock()
    popup = MagicMock()
    with patch("kinito.tk_toplevels.tk.Toplevel", return_value=popup) as ctor:
        result = tops.create_staged_toplevel(root)
    ctor.assert_called_once_with(root)
    assert result is popup
    popup.withdraw.assert_called_once()
    popup.attributes.assert_called_with("-alpha", 0.0)
    popup.geometry.assert_called_with(tops.CHILD_TOPLEVEL_OFFSCREEN)


def test_reveal_staged_toplevel_sets_geometry_and_shows():
    popup = MagicMock()
    tops.reveal_staged_toplevel(popup, geometry="200x100+10+20")
    popup.geometry.assert_called_with("200x100+10+20")
    popup.wm_attributes.assert_called_with("-topmost", True)
    popup.deiconify.assert_called_once()
    popup.attributes.assert_called_with("-alpha", 1.0)


def test_pin_and_restore_assistant_screen_position():
    app = MagicMock()
    app.x = 40
    app.y = 50
    app.root.winfo_exists.return_value = True

    pinned = tops.pin_assistant_screen_position(app)
    assert pinned == (40, 50)

    tops.restore_assistant_screen_position(app, 111, 222)
    assert app.x == 111
    assert app.y == 222
    app.root.geometry.assert_called_with("+111+222")
