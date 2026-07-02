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
        yield


def test_get_screen_bounds_respects_margin(geometry_app):
    min_x, min_y, max_x, max_y = geometry_app.get_screen_bounds(100, 100)
    assert min_x == 10
    assert min_y == 10
    assert max_x == 1920 - 100 - 10
    assert max_y == 1080 - 100 - 10


def test_clamp_position_inside_bounds(geometry_app):
    x, y = geometry_app.clamp_position(-100, 5000)
    min_x, min_y, max_x, max_y = geometry_app.get_screen_bounds()
    assert x == min_x
    assert y == max_y


def test_random_position_on_screen_within_bounds(geometry_app):
    for _ in range(20):
        x, y = geometry_app.random_position_on_screen()
        min_x, min_y, max_x, max_y = geometry_app.get_screen_bounds()
        assert min_x <= x <= max_x
        assert min_y <= y <= max_y


def test_center_position_on_screen_is_middle_of_bounds(geometry_app):
    x, y = geometry_app.center_position_on_screen()
    min_x, min_y, max_x, max_y = geometry_app.get_screen_bounds()
    assert x == (min_x + max_x) // 2
    assert y == (min_y + max_y) // 2


def test_ensure_on_screen_repositions_when_outside_bounds(geometry_app):
    geometry_app.root.winfo_rootx.return_value = -500
    geometry_app.root.winfo_rooty.return_value = 5000
    geometry_app.ensure_on_screen()
    min_x, min_y, max_x, max_y = geometry_app.get_screen_bounds()
    geometry_app.root.geometry.assert_called_once_with(f"+{min_x}+{max_y}")
    assert geometry_app.x == min_x
    assert geometry_app.y == max_y


def test_ensure_on_screen_repositions_when_far_right_off_screen(geometry_app):
    geometry_app.root.winfo_vrootwidth.return_value = 1280
    geometry_app.root.winfo_rootx.return_value = 3000
    geometry_app.root.winfo_rooty.return_value = 400
    geometry_app.x = 3000
    geometry_app.y = 400
    geometry_app.ensure_on_screen()
    min_x, min_y, max_x, max_y = geometry_app.get_screen_bounds()
    geometry_app.root.geometry.assert_called_once_with(f"+{max_x}+{400}")
    assert geometry_app.x == max_x


def test_ensure_on_screen_skips_when_already_visible(geometry_app):
    geometry_app.root.winfo_rootx.return_value = 100
    geometry_app.root.winfo_rooty.return_value = 100
    geometry_app.x = 100
    geometry_app.y = 100
    geometry_app.ensure_on_screen()
    geometry_app.root.geometry.assert_not_called()


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
            geometry_app._watch_screen_geometry()
    ensure.assert_called()
    assert geometry_app._last_virtual_screen_rect == (0, 0, 1920, 1080)
