"""Tests for Windows per-monitor DPI helpers."""

from unittest.mock import MagicMock, patch

import pytest

from kinito import dpi


def test_enable_per_monitor_dpi_awareness_noop_off_windows():
    with patch.object(dpi.sys, "platform", "linux"):
        assert dpi.enable_per_monitor_dpi_awareness() is False


def test_enable_prefers_per_monitor_v2_context():
    user32 = MagicMock()
    user32.SetProcessDpiAwarenessContext.return_value = 1
    fake_ctypes = MagicMock()
    fake_ctypes.windll.user32 = user32
    fake_ctypes.c_void_p = lambda value: value

    with patch.object(dpi.sys, "platform", "win32"):
        with patch.dict("sys.modules", {"ctypes": fake_ctypes}):
            # Re-import path: function imports ctypes internally.
            assert dpi.enable_per_monitor_dpi_awareness() is True

    user32.SetProcessDpiAwarenessContext.assert_called()
    first_ctx = user32.SetProcessDpiAwarenessContext.call_args_list[0].args[0]
    assert first_ctx == dpi._DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2


def test_window_dpi_falls_back_to_base_off_windows():
    with patch.object(dpi.sys, "platform", "darwin"):
        assert dpi.window_dpi(123) == 96


def test_window_dpi_reads_get_dpi_for_window():
    user32 = MagicMock()
    user32.GetDpiForWindow.return_value = 144
    fake_ctypes = MagicMock()
    fake_ctypes.windll.user32 = user32

    with patch.object(dpi.sys, "platform", "win32"):
        with patch.dict("sys.modules", {"ctypes": fake_ctypes}):
            assert dpi.window_dpi(42) == 144
    user32.GetDpiForWindow.assert_called_once_with(42)


def test_dpi_at_point_falls_back_off_windows():
    with patch.object(dpi.sys, "platform", "linux"):
        assert dpi.dpi_at_point(10, 20) == 96


def test_max_monitor_dpi_falls_back_off_windows():
    with patch.object(dpi.sys, "platform", "darwin"):
        assert dpi.max_monitor_dpi() == 96


def test_force_window_client_size_sets_geometry_without_move_by_default():
    window = MagicMock()
    with patch.object(dpi, "toplevel_hwnd", return_value=None):
        with patch.object(dpi.sys, "platform", "linux"):
            dpi.force_window_client_size(window, 128, 128, 10, 20)
    window.geometry.assert_called_once_with("128x128")


def test_force_window_client_size_can_reposition_when_requested():
    window = MagicMock()
    with patch.object(dpi, "toplevel_hwnd", return_value=None):
        with patch.object(dpi.sys, "platform", "linux"):
            dpi.force_window_client_size(window, 128, 128, 10, 20, move=True)
    window.geometry.assert_called_once_with("128x128+10+20")


def test_force_window_client_size_uses_set_window_pos_on_windows():
    window = MagicMock()
    user32 = MagicMock()
    fake_ctypes = MagicMock()
    fake_ctypes.windll.user32 = user32

    with patch.object(dpi, "toplevel_hwnd", return_value=99):
        with patch.object(dpi.sys, "platform", "win32"):
            with patch.dict("sys.modules", {"ctypes": fake_ctypes}):
                dpi.force_window_client_size(window, 128, 140, 5, 6, move=True)

    window.geometry.assert_called_once_with("128x140+5+6")
    user32.SetWindowPos.assert_called_once()
    args = user32.SetWindowPos.call_args.args
    assert args[0] == 99
    assert args[2:6] == (5, 6, 128, 140)


def test_force_window_client_size_nomove_flag_on_windows():
    window = MagicMock()
    user32 = MagicMock()
    fake_ctypes = MagicMock()
    fake_ctypes.windll.user32 = user32

    with patch.object(dpi, "toplevel_hwnd", return_value=99):
        with patch.object(dpi.sys, "platform", "win32"):
            with patch.dict("sys.modules", {"ctypes": fake_ctypes}):
                dpi.force_window_client_size(window, 128, 140)

    window.geometry.assert_called_once_with("128x140")
    flags = user32.SetWindowPos.call_args.args[6]
    assert flags & 0x0002  # SWP_NOMOVE



@pytest.mark.parametrize(
    ("cur_w", "cur_h", "should_fix"),
    [
        (128, 128, False),
        (130, 126, False),
        (256, 256, True),
        (64, 64, True),
    ],
)
def test_ensure_consistent_window_scale_repairs_stretched_size(
    cur_w, cur_h, should_fix
):
    from kinito.app import FloatingAssistant

    app = FloatingAssistant.__new__(FloatingAssistant)
    app._running = True
    app._fixing_display_scale = False
    app._last_window_dpi = 96
    app._assistant_controls_extended = False
    app.is_dragging = False
    app._throwing = False
    app.moving = False
    app._sprite_draw_scale = 1.0
    app.SPRITE_BASE_DPI = 96
    app.x = 40
    app.y = 50
    app.img_normal = MagicMock(width=128, height=128, size=(128, 128))
    app.panel = MagicMock()
    app.panel.winfo_reqwidth.return_value = 128
    app.panel.winfo_reqheight.return_value = 128
    app.root = MagicMock()
    app.root.winfo_exists.return_value = True
    app.root.winfo_width.return_value = cur_w
    app.root.winfo_height.return_value = cur_h

    with (
        patch("kinito.dpi.toplevel_hwnd", return_value=1),
        patch("kinito.dpi.window_dpi", return_value=96),
        patch("kinito.dpi.force_window_client_size") as force_size,
        patch.object(app, "_build_tk_sprites"),
    ):
        app._ensure_consistent_window_scale()

    if should_fix:
        force_size.assert_called_once_with(app.root, 128, 128, move=False)
    else:
        force_size.assert_not_called()


def test_ensure_consistent_window_scale_never_rebuilds_for_dpi_hops():
    """Sprite pixels stay authored-size; only a wrong client size is repaired."""
    from kinito.app import FloatingAssistant

    app = FloatingAssistant.__new__(FloatingAssistant)
    app._running = True
    app._fixing_display_scale = False
    app._last_window_dpi = 96
    app._assistant_controls_extended = False
    app.is_dragging = False
    app._throwing = False
    app.moving = False
    app._sprite_draw_scale = 1.0
    app.SPRITE_BASE_DPI = 96
    app.x = 10
    app.y = 20
    app.img_normal = MagicMock(width=128, height=128, size=(128, 128))
    app.panel = MagicMock()
    app.panel.winfo_reqwidth.return_value = 128
    app.panel.winfo_reqheight.return_value = 128
    app.root = MagicMock()
    app.root.winfo_exists.return_value = True
    app.root.winfo_width.return_value = 128
    app.root.winfo_height.return_value = 128

    with (
        patch("kinito.dpi.toplevel_hwnd", return_value=1),
        patch("kinito.dpi.window_dpi", return_value=144),
        patch("kinito.dpi.force_window_client_size") as force_size,
        patch.object(app, "_build_tk_sprites") as rebuild,
    ):
        app._ensure_consistent_window_scale()

    rebuild.assert_not_called()
    force_size.assert_not_called()
    assert app._last_window_dpi == 144
    assert app._sprite_draw_scale == 1.0


def test_ensure_consistent_window_scale_skips_resize_while_surfing():
    from kinito.app import FloatingAssistant

    app = FloatingAssistant.__new__(FloatingAssistant)
    app._running = True
    app._fixing_display_scale = False
    app.is_dragging = False
    app._throwing = False
    app.moving = True
    app._sprite_draw_scale = 1.0
    app.img_normal = MagicMock(width=128, height=128)
    app.panel = MagicMock()
    app.panel.winfo_reqwidth.return_value = 128
    app.panel.winfo_reqheight.return_value = 128
    app.root = MagicMock()
    app.root.winfo_exists.return_value = True
    app.root.winfo_width.return_value = 256
    app.root.winfo_height.return_value = 256

    with (
        patch("kinito.dpi.toplevel_hwnd", return_value=1),
        patch("kinito.dpi.window_dpi", return_value=96),
        patch("kinito.dpi.force_window_client_size") as force_size,
    ):
        app._ensure_consistent_window_scale()

    force_size.assert_not_called()


def test_sprite_scale_for_dpi_grows_on_dense_displays():
    from kinito.app import FloatingAssistant

    app = FloatingAssistant.__new__(FloatingAssistant)
    app.SPRITE_BASE_DPI = 96
    assert app._sprite_scale_for_dpi(96) == pytest.approx(1.0)
    assert app._sprite_scale_for_dpi(144) == pytest.approx(1.5)
    assert app._sprite_scale_for_dpi(192) == pytest.approx(2.0)


def test_window_screen_size_ignores_dpi_inflated_winfo():
    from kinito.app import FloatingAssistant

    app = FloatingAssistant.__new__(FloatingAssistant)
    app.img_normal = MagicMock(width=128, height=128)
    app.panel = MagicMock()
    app.panel.winfo_reqwidth.return_value = 128
    app.panel.winfo_reqheight.return_value = 128
    app._assistant_controls_extended = False
    app.root = MagicMock()
    app.root.winfo_width.return_value = 256
    app.root.winfo_height.return_value = 256
    app.root.winfo_reqwidth.return_value = 256
    app.root.winfo_reqheight.return_value = 256

    assert app._window_screen_size() == (128, 128)
