"""Tests for ambient window-grab feature."""

from unittest.mock import MagicMock, patch

import pytest

from content import dialogue as dlg
from kinito.features.window_grab import WindowGrabMixin
from kinito.window_targets import WindowRect, hand_tuck_geometry


class WindowGrabStub(WindowGrabMixin):
    pass


@pytest.fixture
def grabber():
    stub = WindowGrabStub()
    stub._running = True
    stub._window_grab_enabled = True
    stub._last_window_grab_at = 0.0
    stub._window_grab_active = False
    stub._window_grab_state = None
    stub._window_grab_timer = None
    stub._hand_window = None
    stub.paused = False
    stub.is_dragging = False
    stub._camera_active = False
    stub._browser_active = False
    stub._focus_mode = False
    stub.root = MagicMock()
    stub.root.after = MagicMock()
    stub.root.after_cancel = MagicMock()
    stub.root.winfo_rootx.return_value = 100
    stub.root.winfo_rooty.return_value = 100
    stub.root.winfo_width.return_value = 120
    stub.root.winfo_height.return_value = 120
    stub.tk_img_hand_left = MagicMock()
    stub.tk_img_hand_left.width.return_value = 40
    stub.tk_img_hand_left.height.return_value = 30
    stub.tk_img_hand_right = MagicMock()
    stub.tk_img_hand_right.width.return_value = 40
    stub.tk_img_hand_right.height.return_value = 30
    stub.speak = MagicMock()
    stub._is_busy_with_speech = MagicMock(return_value=False)
    stub._is_game_active = MagicMock(return_value=False)
    stub._is_position_locked_by_user = MagicMock(return_value=False)
    stub._query_virtual_screen_rect = MagicMock(return_value=(0, 0, 1920, 1080))
    return stub


def test_maybe_trigger_respects_disabled(grabber):
    grabber._window_grab_enabled = False
    with patch("kinito.features.window_grab.sys.platform", "win32"):
        assert grabber.maybe_trigger_window_grab() is False
    grabber.root.after.assert_not_called()


def test_maybe_trigger_noop_on_non_windows(grabber):
    with patch("kinito.features.window_grab.sys.platform", "linux"):
        assert grabber.maybe_trigger_window_grab() is False


def test_maybe_trigger_respects_focus(grabber):
    grabber._focus_mode = True
    with patch("kinito.features.window_grab.sys.platform", "win32"):
        assert grabber.maybe_trigger_window_grab() is False


def test_maybe_trigger_respects_cooldown(grabber):
    with (
        patch("kinito.features.window_grab.sys.platform", "win32"),
        patch("kinito.features.window_grab.time.monotonic", return_value=1000.0),
        patch("kinito.features.window_grab.random.random", return_value=0.0),
    ):
        grabber._last_window_grab_at = 1000.0 - 60.0
        assert grabber.maybe_trigger_window_grab() is False
    grabber.root.after.assert_not_called()


def test_maybe_trigger_schedules_on_hit(grabber):
    with (
        patch("kinito.features.window_grab.sys.platform", "win32"),
        patch("kinito.features.window_grab.time.monotonic", return_value=5000.0),
        patch("kinito.features.window_grab.random.random", return_value=0.0),
    ):
        assert grabber.maybe_trigger_window_grab() is True
        assert grabber._last_window_grab_at == 5000.0
    grabber.root.after.assert_called_once_with(0, grabber._run_window_grab)


def test_hand_tuck_geometry_helper_matches_mixin_usage():
    win = WindowRect(hwnd=7, left=400, top=200, right=900, bottom=700)
    x, y = hand_tuck_geometry("left", win, 48, 36)
    assert x < win.left
    assert win.left < x + 48
    assert win.top <= y <= win.bottom - 36


def test_drag_tick_aborts_when_user_moves_window(grabber):
    grabber._window_grab_active = True
    grabber._window_grab_state = {
        "hwnd": 42,
        "side": "left",
        "last_set": (100, 100),
        "drag_path": [(110, 100), (120, 100)],
        "drag_index": 0,
        "win_w": 400,
        "win_h": 300,
    }
    moved = WindowRect(hwnd=42, left=250, top=180, right=650, bottom=480)
    with (
        patch("kinito.features.window_grab.get_window_rect", return_value=moved),
        patch("kinito.features.window_grab.set_window_pos") as set_pos,
    ):
        grabber._window_grab_drag_tick()
    set_pos.assert_not_called()
    assert grabber._window_grab_active is False


def test_drag_tick_moves_then_continues(grabber):
    grabber._window_grab_active = True
    grabber._hand_window = MagicMock()
    grabber._window_grab_state = {
        "hwnd": 42,
        "side": "left",
        "last_set": (100, 100),
        "drag_path": [(110, 105), (120, 110)],
        "drag_index": 0,
        "win_w": 400,
        "win_h": 300,
    }
    current = WindowRect(hwnd=42, left=100, top=100, right=500, bottom=400)
    after_move = WindowRect(hwnd=42, left=110, top=105, right=510, bottom=405)

    def _rect(_hwnd):
        return after_move if set_pos.called else current

    with (
        patch("kinito.features.window_grab.get_window_rect", side_effect=_rect),
        patch("kinito.features.window_grab.set_window_pos", return_value=True) as set_pos,
        patch("kinito.features.window_grab.collect_own_hwnds", return_value=set()),
        patch.object(grabber, "_hand_size", return_value=(40, 30)),
        patch.object(grabber, "_place_hand") as place_hand,
    ):
        grabber._window_grab_drag_tick()

    set_pos.assert_called_once_with(42, 110, 105)
    assert grabber._window_grab_state["drag_index"] == 1
    assert grabber._window_grab_state["last_set"] == (110, 105)
    assert grabber._window_grab_active is True
    place_hand.assert_called()
    grabber.root.after.assert_called()


def test_drag_tick_stops_on_silent_refusal(grabber):
    grabber._window_grab_active = True
    grabber._window_grab_state = {
        "hwnd": 42,
        "side": "left",
        "last_set": (100, 100),
        "drag_path": [(200, 100)],
        "drag_index": 0,
        "win_w": 400,
        "win_h": 300,
    }
    stuck = WindowRect(hwnd=42, left=100, top=100, right=500, bottom=400)
    with (
        patch("kinito.features.window_grab.get_window_rect", return_value=stuck),
        patch("kinito.features.window_grab.set_window_pos", return_value=True),
        patch("kinito.features.window_grab.minimize_window") as minimize,
    ):
        grabber._window_grab_drag_tick()
    assert grabber._window_grab_active is False
    minimize.assert_called_once_with(42)

def test_prepare_drag_path_falls_back_when_no_room(grabber):
    state: dict = {}
    rect = WindowRect(hwnd=1, left=10, top=10, right=1910, bottom=1070)
    with patch(
        "kinito.features.window_grab.choose_drag_end",
        return_value=None,
    ):
        assert grabber._prepare_window_grab_drag_path(state, rect) is False


def test_fly_end_restores_maximized_before_drag(grabber):
    grabber._window_grab_active = True
    grabber._hand_window = MagicMock()
    grabber._window_grab_state = {
        "hwnd": 42,
        "side": "left",
        "frame": grabber.WINDOW_GRAB_FLY_FRAMES,
        "start": (0, 0),
        "tuck": (100, 100),
        "minimize": False,
        "last_set": (0, 0),
        "drag_index": 0,
        "drag_path": [],
        "was_maximized": True,
    }
    maximized = WindowRect(
        hwnd=42, left=0, top=0, right=1920, bottom=1080, maximized=True
    )
    restored = WindowRect(
        hwnd=42, left=100, top=80, right=900, bottom=700, maximized=False
    )
    with (
        patch("kinito.features.window_grab.get_window_rect", return_value=maximized),
        patch(
            "kinito.features.window_grab.restore_window", return_value=restored
        ) as restore,
        patch.object(grabber, "_hand_size", return_value=(40, 30)),
        patch.object(grabber, "_place_hand"),
        patch(
            "kinito.features.window_grab.collect_own_hwnds", return_value=set()
        ),
        patch.object(grabber, "_prepare_window_grab_drag_path", return_value=True) as prep,
    ):
        grabber._window_grab_fly_tick()
    restore.assert_called_once_with(42)
    prep.assert_called_once()
    assert prep.call_args[0][1] == restored
    grabber.root.after.assert_called()


def test_toggle_window_grab(grabber):
    grabber.toggle_window_grab()
    assert grabber._window_grab_enabled is False
    assert grabber.speak.call_args[0][0] in dlg.WINDOW_PLAY_OFF_LINES
    grabber.toggle_window_grab()
    assert grabber._window_grab_enabled is True
    assert grabber.speak.call_args[0][0] in dlg.WINDOW_PLAY_ON_LINES


def test_pick_skips_immovable_windows(grabber):
    movable = WindowRect(hwnd=2, left=400, top=100, right=700, bottom=400)
    stuck = WindowRect(hwnd=1, left=150, top=100, right=350, bottom=300)

    def _probe(hwnd):
        return hwnd == 2

    with (
        patch(
            "kinito.features.window_grab.list_movable_windows",
            return_value=[stuck, movable],
        ),
        patch(
            "kinito.features.window_grab.probe_window_movable",
            side_effect=_probe,
        ),
        patch(
            "kinito.features.window_grab.get_window_rect",
            return_value=movable,
        ),
    ):
        picked = grabber._pick_window_grab_target()
    assert picked is not None
    assert picked[0].hwnd == 2


def test_run_window_grab_skips_without_target(grabber):
    with (
        patch("kinito.features.window_grab.sys.platform", "win32"),
        patch.object(grabber, "_pick_window_grab_target", return_value=None),
    ):
        grabber._run_window_grab()
    assert grabber._window_grab_active is False
