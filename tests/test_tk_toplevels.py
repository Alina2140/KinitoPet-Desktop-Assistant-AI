"""Tests for staged child-Toplevel helpers."""

from unittest.mock import MagicMock, patch

import kinito.tk_toplevels as tops


def test_create_staged_toplevel_withdraws_and_parks_offscreen():
    root = MagicMock()
    popup = MagicMock()
    with (
        patch("kinito.tk_toplevels.tk.Toplevel", return_value=popup) as ctor,
        patch("kinito.tk_toplevels.detach_toplevel_owner") as detach,
    ):
        result = tops.create_staged_toplevel(root)
    ctor.assert_called_once_with(root)
    assert result is popup
    popup.withdraw.assert_called_once()
    popup.attributes.assert_called_with("-alpha", 0.0)
    popup.geometry.assert_called_with(tops.CHILD_TOPLEVEL_OFFSCREEN)
    detach.assert_called_once_with(popup)


def test_reveal_staged_toplevel_sets_geometry_and_shows():
    popup = MagicMock()
    with patch("kinito.tk_toplevels.detach_toplevel_owner"):
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


def test_position_hold_enforces_pinned_coords_until_release():
    app = MagicMock()
    app.x = 40
    app.y = 50
    app.root.winfo_exists.return_value = True
    app.root.winfo_rootx.return_value = 999
    app.root.winfo_rooty.return_value = 888
    token = object()

    tops.hold_assistant_screen_position(app, 40, 50, token=token)
    assert tops.enforce_assistant_position_hold(app) is True
    app.root.geometry.assert_called_with("+40+50")
    assert app.x == 40
    assert app.y == 50

    tops.release_assistant_position_hold(app, token=token, restore=True)
    assert getattr(app, "_assistant_position_hold", None) is None
    assert tops.enforce_assistant_position_hold(app) is False


def test_clear_assistant_position_hold_allows_sync_again():
    app = MagicMock()
    token = object()
    tops.hold_assistant_screen_position(app, 10, 20, token=token)
    tops.clear_assistant_position_hold(app)
    assert getattr(app, "_assistant_position_hold", None) is None
    assert tops.enforce_assistant_position_hold(app) is False


def test_restore_uses_win32_setwindowpos_when_available():
    app = MagicMock()
    app.x = 1
    app.y = 2
    app.root.winfo_exists.return_value = True
    with (
        patch("kinito.tk_toplevels.sys.platform", "win32"),
        patch("kinito.tk_toplevels._toplevel_hwnd", return_value=42),
        patch("ctypes.windll.user32.SetWindowPos") as set_pos,
    ):
        tops.restore_assistant_screen_position(app, 100, 200)
    app.root.geometry.assert_called_with("+100+200")
    set_pos.assert_called()
    args = set_pos.call_args[0]
    assert args[0] == 42
    assert args[2] == 100
    assert args[3] == 200
