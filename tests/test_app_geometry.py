from unittest.mock import MagicMock, patch

import pytest

from kinito.app import FloatingAssistant


@pytest.fixture
def geometry_app():
    root = MagicMock()
    root.winfo_vrootx.return_value = 0
    root.winfo_vrooty.return_value = 0
    root.winfo_vrootwidth.return_value = 1920
    root.winfo_vrootheight.return_value = 1080
    root.winfo_width.return_value = 200
    root.winfo_height.return_value = 200
    root.winfo_reqwidth.return_value = 200
    root.winfo_reqheight.return_value = 200
    root.update_idletasks = MagicMock()

    app = FloatingAssistant.__new__(FloatingAssistant)
    app.root = root
    app.panel = MagicMock()
    app.panel.winfo_reqwidth.return_value = 200
    app.panel.winfo_reqheight.return_value = 200
    app._running = True
    app.is_dragging = False
    app.x = 100
    app.y = 100
    app.position_speech_bubble = MagicMock()
    app._has_active_speech_bubble = MagicMock(return_value=False)
    app._last_virtual_screen_rect = None
    return app


@pytest.fixture(autouse=True)
def disable_windows_virtual_screen_query():
    with patch.object(FloatingAssistant, "_windows_virtual_screen_rect", return_value=None):
        # Single-monitor layout matching the geometry fixture virtual desktop.
        with patch(
            "kinito.window_targets.list_monitor_rects",
            return_value=[(0, 0, 1920, 1080)],
        ):
            yield


def test_get_screen_bounds_respects_margin(geometry_app):
    min_x, min_y, max_x, max_y = geometry_app.get_screen_bounds(100, 100)
    assert min_x == 10
    assert min_y == 10
    assert max_x == 1920 - 100 - 10
    assert max_y == 1080 - 100 - 10


def test_clamp_position_inside_bounds(geometry_app):
    x, y = geometry_app.clamp_position(-100, 5000)
    assert geometry_app._is_position_on_a_monitor(x, y)
    assert x == 10
    assert y == 1080 - 200 - 10


def test_clamp_position_allows_other_monitors_but_not_voids(geometry_app):
    monitors = [(0, 0, 2560, 1440), (2560, 360, 1280, 720)]
    geometry_app.img_normal = MagicMock(width=128, height=128)
    geometry_app.panel.winfo_reqwidth.return_value = 128
    geometry_app.panel.winfo_reqheight.return_value = 128
    geometry_app.root.winfo_width.return_value = 128
    geometry_app.root.winfo_height.return_value = 128
    geometry_app.root.winfo_reqwidth.return_value = 128
    geometry_app.root.winfo_reqheight.return_value = 128
    # Virtual desktop covers both monitors (with empty band above secondary).
    with patch.object(
        geometry_app,
        "_query_virtual_screen_rect",
        return_value=(0, 0, 3840, 1440),
    ):
        with patch("kinito.window_targets.list_monitor_rects", return_value=monitors):
            # Valid on secondary — keep.
            assert geometry_app.clamp_position(2800, 500) == (2800, 500)
            # Straddle the seam — must not snap back.
            assert geometry_app.clamp_position(2500, 500) == (2500, 500)
            # Void above secondary — pull center onto that screen.
            x, y = geometry_app.clamp_position(2800, 40)
            assert y == 360 - 64
            assert geometry_app._is_position_on_a_monitor(x, y)


def test_random_position_on_screen_within_bounds(geometry_app):
    for _ in range(20):
        x, y = geometry_app.random_position_on_screen()
        assert geometry_app._is_position_on_a_monitor(x, y)


def test_center_position_on_screen_uses_primary_monitor(geometry_app):
    geometry_app.root.winfo_width.return_value = 200
    geometry_app.root.winfo_height.return_value = 200
    geometry_app.root.winfo_reqwidth.return_value = 200
    geometry_app.root.winfo_reqheight.return_value = 200
    geometry_app.panel.winfo_reqwidth.return_value = 200
    geometry_app.panel.winfo_reqheight.return_value = 200
    with patch.object(
        geometry_app,
        "_query_primary_screen_rect",
        return_value=(0, 0, 2560, 1440),
    ):
        # Virtual desktop is wider; primary-centered origin must ignore it.
        with patch.object(
            geometry_app,
            "_query_virtual_screen_rect",
            return_value=(-1920, 0, 7040, 1440),
        ):
            x, y = geometry_app.center_position_on_screen()
    assert x == (2560 - 200) // 2
    assert y == (1440 - 200) // 2


def test_centered_origin_on_primary_helper(geometry_app):
    with patch.object(
        geometry_app,
        "_query_primary_screen_rect",
        return_value=(0, 0, 2560, 1440),
    ):
        assert geometry_app._centered_origin_on_primary(400, 300) == (1080, 570)


def test_ensure_on_screen_repositions_when_outside_bounds(geometry_app):
    geometry_app.root.winfo_rootx.return_value = -500
    geometry_app.root.winfo_rooty.return_value = 5000
    geometry_app.x = -500
    geometry_app.y = 5000
    geometry_app.ensure_on_screen()
    assert geometry_app.x == 10
    assert geometry_app.y == 1080 - 200 - 10
    geometry_app.root.geometry.assert_called_once_with(
        f"+{geometry_app.x}+{geometry_app.y}"
    )


def test_ensure_on_screen_repositions_when_far_right_off_screen(geometry_app):
    geometry_app.root.winfo_rootx.return_value = 3000
    geometry_app.root.winfo_rooty.return_value = 400
    geometry_app.x = 3000
    geometry_app.y = 400
    geometry_app.ensure_on_screen()
    assert geometry_app.x == 1920 - 200 - 10
    assert geometry_app.y == 400
    geometry_app.root.geometry.assert_called_once_with(f"+{geometry_app.x}+{400}")


def test_ensure_on_screen_pulls_back_from_virtual_desktop_void():
    """Shorter secondary monitors leave empty bands inside the virtual desktop."""
    root = MagicMock()
    root.winfo_width.return_value = 128
    root.winfo_height.return_value = 128
    root.winfo_reqwidth.return_value = 128
    root.winfo_reqheight.return_value = 128
    root.update_idletasks = MagicMock()
    # Above the short secondary, still inside the tall virtual desktop.
    root.winfo_rootx.return_value = 2800
    root.winfo_rooty.return_value = 40

    app = FloatingAssistant.__new__(FloatingAssistant)
    app.root = root
    app.panel = MagicMock()
    app.panel.winfo_reqwidth.return_value = 128
    app.panel.winfo_reqheight.return_value = 128
    app.img_normal = MagicMock(width=128, height=128)
    app._running = True
    app.is_dragging = False
    app._throwing = False
    app.x = 2800
    app.y = 40
    app.position_speech_bubble = MagicMock()
    app._has_active_speech_bubble = MagicMock(return_value=False)
    app.SCREEN_EDGE_MARGIN = 10

    monitors = [(0, 0, 2560, 1440), (2560, 360, 1280, 720)]
    with patch.object(app, "_query_virtual_screen_rect", return_value=(0, 0, 3840, 1440)):
        with patch("kinito.window_targets.list_monitor_rects", return_value=monitors):
            app.ensure_on_screen()
            assert app.y == 360 - 64
            assert app._is_position_on_a_monitor(app.x, app.y)
    root.geometry.assert_called_once_with(f"+{app.x}+{app.y}")


def test_ensure_on_screen_skips_when_already_visible(geometry_app):
    geometry_app.root.winfo_rootx.return_value = 100
    geometry_app.root.winfo_rooty.return_value = 100
    geometry_app.x = 100
    geometry_app.y = 100
    geometry_app.ensure_on_screen()
    geometry_app.root.geometry.assert_not_called()


def test_ensure_on_screen_skips_while_throwing(geometry_app):
    geometry_app._throwing = True
    geometry_app.root.winfo_rootx.return_value = -500
    geometry_app.root.winfo_rooty.return_value = 5000
    geometry_app.x = -500
    geometry_app.y = 5000
    geometry_app.ensure_on_screen()
    geometry_app.root.geometry.assert_not_called()


def test_ensure_on_screen_skips_while_surfing(geometry_app):
    geometry_app.moving = True
    geometry_app.root.winfo_rootx.return_value = -500
    geometry_app.root.winfo_rooty.return_value = 5000
    geometry_app.x = -500
    geometry_app.y = 5000
    geometry_app.ensure_on_screen()
    geometry_app.root.geometry.assert_not_called()


def test_get_current_monitor_bounds_uses_short_secondary(geometry_app):
    monitors = [(0, 0, 2560, 1440), (2560, 360, 1280, 720)]
    with patch("kinito.window_targets.list_monitor_rects", return_value=monitors):
        min_x, min_y, max_x, max_y = geometry_app.get_current_monitor_bounds(
            128, 128, x=2800, y=500
        )
    assert min_x == 2560 + 10
    assert min_y == 360 + 10
    assert max_x == 2560 + 1280 - 128 - 10
    assert max_y == 360 + 720 - 128 - 10


def test_keep_assistant_on_top_reasserts_topmost(geometry_app):
    geometry_app.root.winfo_exists.return_value = True
    geometry_app._has_active_speech_bubble = MagicMock(return_value=False)
    geometry_app._force_window_topmost = MagicMock()
    geometry_app._raise_screen_effect_overlays = MagicMock()

    geometry_app._keep_assistant_on_top()

    geometry_app.root.wm_attributes.assert_called_with("-topmost", True)
    geometry_app.root.lift.assert_called_once()
    geometry_app._force_window_topmost.assert_called_once_with(geometry_app.root)
    geometry_app._raise_screen_effect_overlays.assert_called_once()


def test_query_virtual_screen_rect_prefers_windows_metrics(geometry_app):
    with patch.object(
        FloatingAssistant,
        "_windows_virtual_screen_rect",
        return_value=(-1920, 0, 3840, 1080),
    ):
        assert geometry_app._query_virtual_screen_rect() == (-1920, 0, 3840, 1080)


def test_watch_screen_geometry_repositions_on_desktop_shrink(geometry_app):
    geometry_app.root.after = MagicMock()
    geometry_app._last_virtual_screen_rect = (0, 0, 3840, 1080)
    with patch.object(geometry_app, "_query_virtual_screen_rect", return_value=(0, 0, 1920, 1080)):
        with patch.object(geometry_app, "ensure_on_screen") as ensure:
            with patch.object(geometry_app, "_ensure_consistent_window_scale"):
                geometry_app._watch_screen_geometry()
    ensure.assert_called()
    assert geometry_app._last_virtual_screen_rect == (0, 0, 1920, 1080)
