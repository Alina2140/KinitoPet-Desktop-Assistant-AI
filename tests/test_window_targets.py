"""Tests for window geometry helpers used by window grab."""

import random
from unittest.mock import patch

from kinito.window_targets import (
    SIDE_LEFT,
    SIDE_RIGHT,
    WindowRect,
    centered_origin_on_rect,
    choose_grab_side,
    clamp_origin_for_movement,
    clamp_origin_onto_monitors,
    clamp_window_origin,
    hand_sprite_for_side,
    hand_tuck_geometry,
    monitor_rect_for_point,
    movement_allows_void_transit,
    origin_bounds_on_rect,
    origin_fully_on_any_monitor,
    pick_window_target,
    point_on_any_monitor,
    position_diverged,
    primary_monitor_rect,
    random_fully_visible_origin,
    window_center_on_any_monitor,
)


def test_clamp_window_origin_keeps_title_strip_on_dual_monitor():
    # Dual monitor virtual desktop: secondary left of primary.
    virtual = (-1920, 0, 3840, 1080)
    x, y = clamp_window_origin(-5000, -100, 800, 600, virtual, title_keep_px=40)
    assert x == -1920 - 800 + 40
    assert y == 0

    x2, y2 = clamp_window_origin(10000, 10000, 800, 600, virtual, title_keep_px=40)
    assert x2 == -1920 + 3840 - 40
    assert y2 == 0 + 1080 - 40


def test_clamp_window_origin_inside_stays():
    virtual = (0, 0, 1920, 1080)
    assert clamp_window_origin(100, 200, 400, 300, virtual) == (100, 200)


def test_random_fully_visible_origin_stays_on_chosen_monitor():
    monitors = [(-1920, 0, 1920, 1080), (0, 0, 1920, 1080)]
    rng = random.Random(7)
    for _ in range(40):
        x, y = random_fully_visible_origin(320, 140, monitors=monitors, margin=16, rng=rng)
        on_left = -1920 + 16 <= x <= -1920 + 1920 - 320 - 16 and 16 <= y <= 1080 - 140 - 16
        on_right = 16 <= x <= 1920 - 320 - 16 and 16 <= y <= 1080 - 140 - 16
        assert on_left or on_right


def test_random_fully_visible_origin_handles_oversized_window():
    x, y = random_fully_visible_origin(
        5000,
        5000,
        monitors=[(0, 0, 800, 600)],
        margin=10,
        rng=random.Random(1),
    )
    assert (x, y) == (10, 10)


def test_primary_monitor_rect_prefers_origin_monitor():
    with patch("kinito.window_targets.list_monitor_rects") as listed:
        listed.return_value = [
            (-1920, 105, 1536, 960),
            (0, 0, 2560, 1440),
            (2560, 0, 2560, 1440),
        ]
        assert primary_monitor_rect() == (0, 0, 2560, 1440)


def test_centered_origin_on_rect():
    assert centered_origin_on_rect(200, 100, (0, 0, 2560, 1440)) == (1180, 670)
    assert centered_origin_on_rect(400, 300, (-1920, 0, 1920, 1080)) == (-1920 + 760, 390)


def test_monitor_rect_for_point_prefers_containing_display():
    monitors = [(0, 0, 2560, 1440), (2560, 360, 1280, 720)]
    assert monitor_rect_for_point(2800, 500, monitors=monitors) == monitors[1]
    assert monitor_rect_for_point(100, 100, monitors=monitors) == monitors[0]


def test_monitor_rect_for_point_falls_back_to_nearest():
    monitors = [(0, 0, 2560, 1440), (2560, 360, 1280, 720)]
    # Above the short secondary — still nearer to that display's center.
    assert monitor_rect_for_point(2800, 50, monitors=monitors) == monitors[1]


def test_clamp_origin_onto_monitors_pulls_center_out_of_void():
    monitors = [(0, 0, 2560, 1440), (2560, 360, 1280, 720)]
    # Center at y=104 is above the short secondary → project onto y=360.
    x, y = clamp_origin_onto_monitors(
        2800, 40, 128, 128, margin=10, monitors=monitors
    )
    assert x == 2800
    assert y == 360 - 64  # center on top edge, origin = center - half height
    assert window_center_on_any_monitor(x, y, 128, 128, monitors=monitors)


def test_clamp_origin_allows_straddling_monitor_seam():
    """Full-window fit would reject this; center-based clamp must keep it."""
    monitors = [(0, 0, 2560, 1440), (2560, 0, 1920, 1080)]
    # Window spans the seam; center is still on the left display.
    x, y = 2500, 200
    assert not origin_fully_on_any_monitor(x, y, 128, 128, margin=10, monitors=monitors)
    assert window_center_on_any_monitor(x, y, 128, 128, monitors=monitors)
    assert clamp_origin_onto_monitors(x, y, 128, 128, monitors=monitors) == (2500, 200)


def test_clamp_origin_onto_monitors_preserves_valid_cross_monitor_position():
    """Already-visible centers on either screen must not be pulled back."""
    monitors = [(0, 0, 2560, 1440), (2560, 360, 1280, 720)]
    assert clamp_origin_onto_monitors(
        2800, 500, 128, 128, margin=10, monitors=monitors
    ) == (2800, 500)
    assert clamp_origin_onto_monitors(
        100, 100, 128, 128, margin=10, monitors=monitors
    ) == (100, 100)


def test_origin_fully_on_any_monitor_rejects_virtual_void():
    monitors = [(0, 0, 2560, 1440), (2560, 360, 1280, 720)]
    assert not origin_fully_on_any_monitor(
        2800, 40, 128, 128, margin=10, monitors=monitors
    )
    assert not point_on_any_monitor(2864, 104, monitors=monitors)


def test_void_transit_allows_throw_toward_short_secondary():
    """From the large screen toward the short one, the gap is a bridge."""
    monitors = [(0, 0, 2560, 1440), (2560, 360, 1280, 720)]
    # Center just past the large monitor, above the short secondary.
    cx, cy = 2600.0, 164.0
    assert not point_on_any_monitor(cx, cy, monitors=monitors)
    assert movement_allows_void_transit(
        cx, cy, vx=800.0, vy=0.0, monitors=monitors
    )
    # Keep origin during transit (caller applies virtual fence only).
    assert clamp_origin_for_movement(
        2600 - 64, 164 - 64, 128, 128, vx=800.0, vy=0.0, monitors=monitors
    ) == (2536, 100)


def test_void_transit_blocks_dead_end_above_short_screen():
    """Thrown off the top of the short screen must still bounce."""
    monitors = [(0, 0, 2560, 1440), (2560, 360, 1280, 720)]
    cx, cy = 2864.0, 300.0  # just above secondary
    assert not movement_allows_void_transit(
        cx, cy, vx=0.0, vy=-900.0, monitors=monitors
    )
    x, y = clamp_origin_for_movement(
        2800, 236, 128, 128, vx=0.0, vy=-900.0, monitors=monitors
    )
    assert window_center_on_any_monitor(x, y, 128, 128, monitors=monitors)


def test_void_transit_allows_surf_when_target_on_other_monitor():
    monitors = [(0, 0, 2560, 1440), (2560, 360, 1280, 720)]
    assert movement_allows_void_transit(
        2600.0,
        164.0,
        vx=0.0,
        vy=0.0,
        target=(3000.0, 500.0),
        monitors=monitors,
    )


def test_origin_bounds_on_rect():
    assert origin_bounds_on_rect(128, 128, (2560, 360, 1280, 720), margin=10) == (
        2570,
        370,
        2560 + 1280 - 128 - 10,
        360 + 720 - 128 - 10,
    )


def test_choose_grab_side_prefers_nearer_edge():
    assert choose_grab_side(50, 100, 500) == SIDE_LEFT
    assert choose_grab_side(480, 100, 500) == SIDE_RIGHT


def test_hand_sprite_for_side():
    assert hand_sprite_for_side(SIDE_LEFT) == "HandToRight"
    assert hand_sprite_for_side(SIDE_RIGHT) == "HandToLeft"


def test_hand_tuck_geometry_left_edge():
    win = WindowRect(hwnd=1, left=200, top=100, right=600, bottom=500)
    # Hand 40 wide; 50% tuck → hand_x = 200 - 20 = 180
    x, y = hand_tuck_geometry(SIDE_LEFT, win, 40, 30, tuck_fraction=0.5)
    assert x == 180
    assert y == 100 + (400 - 30) // 2


def test_hand_tuck_geometry_right_edge():
    win = WindowRect(hwnd=1, left=200, top=100, right=600, bottom=500)
    # Hand 40 wide; 50% tuck → hand_x = 600 - 20 = 580
    x, y = hand_tuck_geometry(SIDE_RIGHT, win, 40, 30, tuck_fraction=0.5)
    assert x == 580
    assert y == 100 + (400 - 30) // 2


def test_minimize_button_center_fallback_top_right():
    from kinito.window_targets import minimize_button_center

    win = WindowRect(hwnd=1, left=0, top=0, right=1920, bottom=1080, maximized=True)
    with patch("kinito.window_targets.sys.platform", "linux"):
        cx, cy = minimize_button_center(win)
    assert cx > win.right - 200
    assert cx < win.right
    assert 0 <= cy <= 40


def test_hand_minimize_geometry_points_at_caption():
    from kinito.window_targets import hand_minimize_geometry

    win = WindowRect(hwnd=1, left=100, top=50, right=900, bottom=700)
    with patch(
        "kinito.window_targets.minimize_button_center",
        return_value=(860, 66),
    ):
        x, y = hand_minimize_geometry(win, 40, 30)
    assert x < 860
    assert y < 66
    # Fingers of HandToRight reach near the button center.
    assert x + 40 >= 860 - 8


def test_position_diverged_tolerance():
    assert position_diverged((100, 100), (100, 100)) is False
    assert position_diverged((100, 100), (105, 100), tolerance_px=12) is False
    assert position_diverged((100, 100), (120, 100), tolerance_px=12) is True


def test_pick_window_target_uses_nearer_pool():
    near = WindowRect(hwnd=1, left=100, top=0, right=300, bottom=200)
    far = WindowRect(hwnd=2, left=2000, top=0, right=2200, bottom=200)
    picked = pick_window_target(
        [near, far],
        kinito_center=(0.0, 100.0),
        max_distance=400,
        rng=lambda items: items[0],
    )
    assert picked is not None
    win, side = picked
    assert win.hwnd == 1
    assert side == SIDE_LEFT


def test_pick_window_target_empty():
    assert pick_window_target([], kinito_center=(0.0, 0.0)) is None


def test_choose_drag_end_finds_room_for_midsize_window():
    from kinito.window_targets import choose_drag_end

    virtual = (0, 0, 1920, 1080)
    end = choose_drag_end(200, 200, 600, 400, virtual, distance_range=(160, 360))
    assert end is not None
    assert (abs(end[0] - 200) ** 2 + abs(end[1] - 200) ** 2) ** 0.5 >= 80


def test_choose_drag_end_returns_none_on_degenerate_virtual_desktop():
    from kinito.window_targets import choose_drag_end

    # Tiny virtual desktop: after clamp, origin barely moves.
    virtual = (0, 0, 50, 50)
    end = choose_drag_end(0, 0, 40, 40, virtual, distance_range=(160, 360), min_move_px=80)
    assert end is None
