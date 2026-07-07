import math
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from kinito.movement import MovementMixin


class MovementStub(MovementMixin):
    pass


@pytest.fixture
def movement():
    stub = MovementStub()
    stub._running = True
    stub.paused = False
    stub.is_dragging = False
    stub._drag_moved = False
    stub._startup_complete = True
    stub._allow_random_questions = False
    stub.talking = False
    stub.moving = False
    stub.root = MagicMock()
    stub.root.winfo_x.return_value = 100
    stub.root.winfo_y.return_value = 100
    stub.root.winfo_rootx.return_value = 100
    stub.root.winfo_rooty.return_value = 200
    stub.panel = MagicMock()
    stub.tk_img_surf_left = "surf_left"
    stub.tk_img_surf_right = "surf_right"
    stub.tk_img_normal = "normal"
    stub.img_surf_left = Image.new("RGBA", (24, 48), (255, 255, 255, 0))
    stub.img_surf_right = Image.new("RGBA", (24, 48), (255, 255, 255, 0))
    stub._surf_render_cache = {}
    stub._surf_facing = "right"
    stub.play_sfx = MagicMock()
    stub.clamp_position = MagicMock(side_effect=lambda x, y: (x, y))
    stub._should_skip_drag_sounds = MagicMock(return_value=False)
    stub._has_active_speech_bubble = MagicMock(return_value=False)
    stub._is_busy_with_speech = MagicMock(return_value=False)
    stub._is_background_music_playing = MagicMock(return_value=False)
    stub.ensure_on_screen = MagicMock()
    stub.position_speech_bubble = MagicMock()
    return stub


def test_on_mouse_down_stops_moving_and_plays_bomp(movement):
    movement.moving = True
    movement.stop_background_music = MagicMock()
    movement._stop_audio_for_drag = MagicMock()
    event = MagicMock(x_root=50, y_root=60, widget=movement.panel)
    movement.on_mouse_down(event)
    assert movement.is_dragging is True
    assert movement.moving is False
    assert movement._drag_moved is False
    movement._stop_audio_for_drag.assert_called_once()
    movement.play_sfx.assert_called_once()


def test_stop_audio_for_drag_keeps_user_music(movement):
    movement._user_music_path = "song.mp3"
    movement.stop_background_music = MagicMock()
    movement.stop_speech_accompaniment_music = MagicMock()

    movement._stop_audio_for_drag()

    movement.stop_background_music.assert_not_called()
    movement.stop_speech_accompaniment_music.assert_not_called()


def test_stop_audio_for_drag_stops_speech_accompaniment(movement):
    movement._speech_accompaniment_active = True
    movement.stop_speech_accompaniment_music = MagicMock()

    movement._stop_audio_for_drag()

    movement.stop_speech_accompaniment_music.assert_called_once()


def test_setup_mouse_bindings_drags_sprite_only(movement):
    movement.panel = MagicMock()
    movement.root = MagicMock()
    movement.setup_mouse_bindings()
    movement.panel.bind.assert_called_once_with("<Button-1>", movement.on_mouse_down)
    movement.root.bind.assert_any_call("<B1-Motion>", movement.on_mouse_move)
    movement.root.bind.assert_any_call("<ButtonRelease-1>", movement.on_mouse_up)


def test_on_mouse_up_plays_bomp_after_drag(movement):
    movement.is_dragging = True
    movement._drag_moved = True
    movement.on_mouse_up(MagicMock())
    assert movement.is_dragging is False
    movement.play_sfx.assert_called_once()


def test_on_mouse_up_skips_bomp_without_drag(movement):
    movement.is_dragging = True
    movement._drag_moved = False
    movement.on_mouse_up(MagicMock())
    movement.play_sfx.assert_not_called()


def test_on_mouse_move_clamps_position(movement):
    movement.is_dragging = True
    movement.mouse_click_offset_x = 10
    movement.mouse_click_offset_y = 20
    event = MagicMock(x_root=300, y_root=400)
    movement.on_mouse_move(event)
    movement.clamp_position.assert_called_once()
    movement.root.geometry.assert_called()


def test_change_sprite_skipped_while_dragging(movement):
    movement.is_dragging = True
    movement.change_sprite("sprite")
    movement.panel.config.assert_not_called()


def test_move_towards_reaches_target(movement):
    movement.x = 0
    movement.y = 0
    movement._running = True
    with patch.object(movement, "_render_surf_sprite"):
        movement.move_towards(20, 0, speed=5)
    assert movement.root.geometry.called
    assert movement.x == 20
    assert movement.y == 0


def test_surf_wave_offset_oscillates():
    assert MovementMixin._surf_wave_offset(0) == 0
    assert MovementMixin._surf_wave_offset(math.pi / 2) == pytest.approx(
        MovementMixin.SURF_WAVE_AMPLITUDE
    )
    assert MovementMixin._surf_wave_offset(math.pi) == pytest.approx(0, abs=1e-6)


def test_apply_surf_geometry_bobs_display_y(movement):
    movement._apply_surf_geometry(120, 200, math.pi / 2)
    movement.clamp_position.assert_called_once_with(120, 200 + MovementMixin.SURF_WAVE_AMPLITUDE)
    movement.root.geometry.assert_called_once_with(
        f"+120+{int(200 + MovementMixin.SURF_WAVE_AMPLITUDE)}"
    )
    assert movement.x == 120
    assert movement.y == 200


def test_move_towards_geometry_y_varies_with_wave(movement):
    movement.x = 100
    movement.y = 100
    geometries = []
    movement.root.geometry = lambda geometry: geometries.append(geometry)
    with patch.object(movement, "_render_surf_sprite"):
        movement.move_towards(100, 160, speed=20)
    ys = {int(geometry.split("+")[2]) for geometry in geometries}
    assert len(ys) > 1
    assert movement.x == 100
    assert movement.y == 160


def test_surf_tilt_follows_wave_rise_and_fall(movement):
    movement._surf_facing = "right"
    rising = movement._surf_tilt_degrees(0)
    falling = movement._surf_tilt_degrees(math.pi)
    assert rising > 0
    assert falling < 0


def test_surf_tilt_flips_when_facing_left(movement):
    movement._surf_facing = "right"
    right_tilt = movement._surf_tilt_degrees(0)
    movement._surf_facing = "left"
    left_tilt = movement._surf_tilt_degrees(0)
    assert right_tilt * left_tilt < 0


def test_rotate_sprite_padded_keeps_white_corners():
    sprite = Image.new("RGBA", (40, 40), (255, 255, 255, 0))
    for x in range(14, 26):
        sprite.putpixel((x, 20), (255, 0, 0, 255))
    rotated = MovementMixin._rotate_sprite_padded(sprite, 8)
    assert rotated.getpixel((0, 0)) == (255, 255, 255)
    assert rotated.getpixel((39, 39)) == (255, 255, 255)


def test_snap_soft_edges_preserves_opaque_pixels():
    sprite = Image.new("RGBA", (6, 6), (255, 255, 255, 0))
    sprite.putpixel((2, 2), (0, 0, 0, 255))
    sprite.putpixel((3, 2), (255, 240, 245, 80))
    flat = MovementMixin._flatten_sprite_on_white(sprite)
    assert flat.getpixel((2, 2)) == (0, 0, 0)
    assert flat.getpixel((3, 2)) == (255, 255, 255)


def test_render_surf_sprite_caches_rotated_frames(movement):
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    movement.root = root
    movement._render_surf_sprite(40, math.pi / 4)
    movement._render_surf_sprite(40, math.pi / 4)
    assert len(movement._surf_render_cache) == 1
    movement.panel.config.assert_called()
    root.destroy()


def test_finish_surf_movement_clears_cache_and_restores_sprite(movement):
    movement._surf_render_cache[("right", 4.0)] = "cached"
    movement._finish_surf_movement()
    assert movement._surf_render_cache == {}
    movement.panel.config.assert_called_with(image="normal")


def test_surf_sprite_for_movement_uses_direction(movement):
    assert movement._surf_sprite_for_movement(-5) == "surf_left"
    assert movement._surf_facing == "left"
    assert movement._surf_sprite_for_movement(5) == "surf_right"
    assert movement._surf_facing == "right"
    assert movement._surf_sprite_for_movement(0) == "surf_right"


def test_talking_sprite_pair_switches_with_mode(movement):
    movement.tk_img_talking = "talk_a"
    movement.tk_img_talking2 = "talk_b"
    movement.tk_img_thinking = "think_a"
    movement.tk_img_thinking2 = "think_b"
    movement._talk_sprite_mode = "talking"
    assert movement._talking_sprite_pair() == ("talk_a", "talk_b")
    movement._talk_sprite_mode = "thinking"
    assert movement._talking_sprite_pair() == ("think_a", "think_b")


def test_idle_wait_before_next_action_in_valid_ranges(movement):
    with patch("kinito.movement.random.random", return_value=0.1):
        wait = movement._idle_wait_before_next_action()
        assert MovementMixin.IDLE_WAIT_SHORT[0] <= wait <= MovementMixin.IDLE_WAIT_SHORT[1]

    with patch("kinito.movement.random.random", return_value=0.5):
        wait = movement._idle_wait_before_next_action()
        assert MovementMixin.IDLE_WAIT_NORMAL[0] <= wait <= MovementMixin.IDLE_WAIT_NORMAL[1]

    with patch("kinito.movement.random.random", return_value=0.95):
        wait = movement._idle_wait_before_next_action()
        assert MovementMixin.IDLE_WAIT_LONG[0] <= wait <= MovementMixin.IDLE_WAIT_LONG[1]


def test_smooth_movement_calls_ai_idle_line(movement):
    movement._startup_complete = True
    movement._allow_random_questions = True
    movement._focus_mode = False
    movement._should_use_ai_idle_line = MagicMock(return_value=True)
    movement.speak_ai_idle_line = MagicMock(side_effect=lambda: setattr(movement, "_running", False))
    movement.perform_random_menu_action = MagicMock()
    movement.speak_random_question = MagicMock()
    movement._idle_wait_before_next_action = MagicMock(return_value=0)

    with (
        patch("kinito.movement.random.random", side_effect=[0.1, 0.5]),
        patch("kinito.movement.time.sleep"),
    ):
        movement.smooth_movement()

    movement.speak_ai_idle_line.assert_called_once()
    movement.speak_random_question.assert_not_called()


def test_smooth_movement_waits_while_reading_idle(movement):
    movement._reading_idle_active = True
    movement.move_towards = MagicMock()
    movement.play_sfx = MagicMock()

    def stop_after_wait(*_args, **_kwargs):
        movement._running = False

    with patch("kinito.movement.time.sleep", side_effect=stop_after_wait) as sleep_mock:
        movement.smooth_movement()

    movement.move_towards.assert_not_called()
    movement.play_sfx.assert_not_called()
    sleep_mock.assert_called_once_with(0.1)


def test_is_reading_idle_active_requires_uninterrupted_state(movement):
    movement._reading_idle_active = True
    movement._focus_mode = False
    assert movement._is_reading_idle_active() is True

    movement.moving = True
    assert movement._is_reading_idle_active() is False

    movement.moving = False
    movement.talking = True
    assert movement._is_reading_idle_active() is False

    movement.talking = False
    movement._fancy_mode = True
    assert movement._is_reading_idle_active() is False


def test_maybe_play_reading_page_turn_skips_when_interrupted(movement):
    movement.play_sfx = MagicMock()
    movement._reading_idle_active = True
    movement._reading_idle_session = 1
    movement.talking = True

    movement._maybe_play_reading_page_turn(1)

    movement.play_sfx.assert_not_called()


def test_maybe_play_reading_page_turn_skips_when_fancy_mode(movement):
    movement.play_sfx = MagicMock()
    movement._reading_idle_active = True
    movement._reading_idle_session = 1
    movement._fancy_mode = True

    with patch("kinito.movement.random.random", return_value=0.0):
        movement._maybe_play_reading_page_turn(1)

    movement.play_sfx.assert_not_called()


def test_maybe_play_reading_page_turn_skips_stale_session(movement):
    movement.play_sfx = MagicMock()
    movement._reading_idle_active = True
    movement._reading_idle_session = 2

    with patch("kinito.movement.random.random", return_value=0.0):
        movement._maybe_play_reading_page_turn(1)

    movement.play_sfx.assert_not_called()


def test_maybe_play_reading_page_turn_plays_when_active(movement):
    movement.play_sfx = MagicMock()
    movement._reading_idle_active = True
    movement._reading_idle_session = 1

    with patch("kinito.movement.random.random", return_value=0.0):
        movement._maybe_play_reading_page_turn(1)

    movement.play_sfx.assert_called_once()
