"""Tests for window geometry helpers used by window grab."""

import random
from unittest.mock import patch

from kinito.window_targets import (
    SIDE_LEFT,
    SIDE_RIGHT,
    WindowRect,
    centered_origin_on_rect,
    choose_grab_side,
    clamp_window_origin,
    hand_sprite_for_side,
    hand_tuck_geometry,
    pick_window_target,
    position_diverged,
    primary_monitor_rect,
    random_fully_visible_origin,
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
