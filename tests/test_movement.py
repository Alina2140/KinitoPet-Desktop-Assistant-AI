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
    movement._start_drag_tracking = MagicMock()
    movement._sync_kinito_screen_position = MagicMock()
    movement.x = 100
    movement.y = 200
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


def test_stop_audio_for_drag_keeps_speech_accompaniment(movement):
    movement._speech_accompaniment_active = True
    movement.stop_speech_accompaniment_music = MagicMock()
    movement.stop_background_music = MagicMock()

    movement._stop_audio_for_drag()

    movement.stop_speech_accompaniment_music.assert_not_called()
    movement.stop_background_music.assert_not_called()


def test_setup_mouse_bindings_drags_sprite_only(movement):
    movement.panel = MagicMock()
    movement.root = MagicMock()
    movement.root.winfo_rootx.return_value = 100
    movement.root.winfo_rooty.return_value = 200
    movement.setup_mouse_bindings()
    movement.panel.bind.assert_called_once_with("<Button-1>", movement.on_mouse_down)
    movement.root.bind.assert_called_once_with("<Configure>", movement._on_root_moved)
    assert movement.x == 100
    assert movement.y == 200


def test_on_mouse_down_starts_global_drag_tracking(movement):
    movement._start_drag_tracking = MagicMock()
    movement._sync_kinito_screen_position = MagicMock()
    movement.x = 100
    movement.y = 200
    event = MagicMock(x_root=50, y_root=60, widget=movement.panel)
    movement.on_mouse_down(event)
    movement._start_drag_tracking.assert_called_once()


def test_on_mouse_up_stops_global_drag_tracking(movement):
    movement.is_dragging = True
    movement._drag_moved = False
    movement._stop_drag_tracking = MagicMock()
    movement._follow_speech_bubble_to_kinito = MagicMock()
    movement.on_mouse_up(MagicMock())
    movement._stop_drag_tracking.assert_called_once()


def test_on_mouse_up_plays_bomp_after_drag(movement):
    movement.is_dragging = True
    movement._drag_moved = True
    movement._stop_drag_tracking = MagicMock()
    movement._follow_speech_bubble_to_kinito = MagicMock()
    movement.on_mouse_up(MagicMock())
    assert movement.is_dragging is False
    movement.play_sfx.assert_called_once()


def test_on_mouse_up_skips_bomp_without_drag(movement):
    movement.is_dragging = True
    movement._drag_moved = False
    movement._stop_drag_tracking = MagicMock()
    movement._follow_speech_bubble_to_kinito = MagicMock()
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


def test_on_mouse_move_repositions_speech_bubble(movement):
    movement.is_dragging = True
    movement.mouse_click_offset_x = 0
    movement.mouse_click_offset_y = 0
    movement._follow_speech_bubble_to_kinito = MagicMock()
    movement.on_mouse_move(MagicMock(x_root=300, y_root=400))
    movement._follow_speech_bubble_to_kinito.assert_called_once_with(300, 400)


def test_on_mouse_down_captures_bubble_offset(movement):
    movement._start_drag_tracking = MagicMock()
    movement._sync_kinito_screen_position = MagicMock()
    movement._capture_speech_bubble_drag_offset = MagicMock()
    movement.x = 100
    movement.y = 200
    movement.on_mouse_down(MagicMock(x_root=50, y_root=60, widget=movement.panel))
    movement._capture_speech_bubble_drag_offset.assert_called_once()


def test_on_root_moved_follows_speech_bubble(movement):
    movement.x = 100
    movement.y = 200

    def sync():
        movement.x = 150
        movement.y = 250

    movement._sync_kinito_screen_position = sync
    movement._follow_speech_bubble_to_kinito = MagicMock()
    movement._on_root_moved(MagicMock(widget=movement.root))
    movement._follow_speech_bubble_to_kinito.assert_called_once_with(150, 250)


def test_on_root_moved_ignores_surf_bobbing(movement):
    movement.moving = True
    movement._sync_kinito_screen_position = MagicMock()
    movement._follow_speech_bubble_to_kinito = MagicMock()
    movement._on_root_moved(MagicMock(widget=movement.root))
    movement._sync_kinito_screen_position.assert_not_called()
    movement._follow_speech_bubble_to_kinito.assert_not_called()


def test_apply_surf_geometry_repositions_speech_bubble(movement):
    movement._follow_speech_bubble_to_kinito = MagicMock()
    movement._apply_surf_geometry(120, 200, math.pi / 2)
    movement._follow_speech_bubble_to_kinito.assert_not_called()


def test_change_sprite_skipped_while_dragging(movement):
    movement.is_dragging = True
    movement.change_sprite("sprite")
    movement.panel.config.assert_not_called()


def test_move_towards_stops_when_speech_starts(movement):
    movement.x = 0
    movement.y = 0
    movement.root.winfo_rootx.return_value = 0
    movement.root.winfo_rooty.return_value = 0
    movement._running = True
    busy_checks = {"count": 0}

    def busy():
        busy_checks["count"] += 1
        return busy_checks["count"] > 1

    movement._is_busy_with_speech = busy
    with (
        patch.object(movement, "_render_surf_sprite"),
        patch.object(movement, "_finish_surf_movement") as finish,
        patch.object(movement, "_realign_speech_bubble_after_move") as realign,
    ):
        movement.move_towards(100, 0, speed=5)

    finish.assert_called()
    realign.assert_called_once()
    assert movement.x < 100


def test_stop_roaming_clears_moving_flag(movement):
    movement.moving = True
    movement._finish_surf_movement = MagicMock()

    movement._stop_roaming()

    assert movement.moving is False
    movement._finish_surf_movement.assert_called_once()


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
    movement._is_game_active = MagicMock(return_value=False)
    movement._should_use_ai_idle_line = MagicMock(return_value=True)
    movement.speak_ai_idle_line = MagicMock(side_effect=lambda: setattr(movement, "_running", False))
    movement.speak_memory_question_idle = MagicMock()
    movement.perform_random_menu_action = MagicMock()
    movement.speak_random_question = MagicMock()
    movement._idle_wait_before_next_action = MagicMock(return_value=0)

    with (
        patch("kinito.movement.random.random", side_effect=[0.1, 0.5, 0.9]),
        patch("kinito.movement.time.sleep"),
    ):
        movement.smooth_movement()

    movement.speak_ai_idle_line.assert_called_once()
    movement.speak_memory_question_idle.assert_not_called()
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
    movement.change_sprite = MagicMock()
    movement._reading_idle_active = True
    movement._reading_idle_session = 1
    movement._is_reading_idle_active = MagicMock(return_value=True)

    with (
        patch("kinito.movement.random.random", return_value=0.0),
        patch("kinito.movement.time.sleep") as sleep,
    ):
        assert (
            movement._maybe_play_reading_page_turn(
                1,
                page_sprites=("page1", "page2"),
                restore_sprite="idle2",
            )
            is True
        )

    movement.play_sfx.assert_called_once()
    assert movement.change_sprite.call_args_list == [
        (("page1",),),
        (("page2",),),
        (("idle2",),),
    ]
    assert sleep.call_count == 3
    sleep.assert_any_call(movement.READING_PAGE_TURN_SOUND_LEAD_SECONDS)


def test_maybe_play_reading_page_turn_without_page_sprites_still_plays_sound(movement):
    movement.play_sfx = MagicMock()
    movement.change_sprite = MagicMock()
    movement._reading_idle_active = True
    movement._reading_idle_session = 1

    with patch("kinito.movement.random.random", return_value=0.0):
        assert movement._maybe_play_reading_page_turn(1) is True

    movement.play_sfx.assert_called_once()
    movement.change_sprite.assert_not_called()


def test_pick_normal_idle_sprite_prefers_default(movement):
    movement.tk_img_normal = "default"
    movement._standing_look_sprites = ("left", "right")
    movement._look_around_ready_at = 0.0
    with patch("kinito.movement.random.random", return_value=0.1):
        assert movement._pick_normal_idle_sprite(crouch=False) == "default"


def test_pick_normal_idle_sprite_can_look_around(movement):
    movement.tk_img_normal = "default"
    movement._standing_look_sprites = ("left", "right")
    movement._look_around_ready_at = 0.0
    with (
        patch("kinito.movement.time.monotonic", return_value=100.0),
        patch("kinito.movement.random.random", return_value=0.9),
        patch("kinito.movement.random.choice", return_value="left") as choose,
    ):
        assert movement._pick_normal_idle_sprite(crouch=False) == "left"
    choose.assert_called_once_with(("left", "right"))
    assert movement._look_around_ready_at == 100.0 + movement.LOOK_AROUND_COOLDOWN_SECONDS


def test_pick_normal_idle_sprite_respects_look_around_cooldown(movement):
    movement.tk_img_normal = "default"
    movement._standing_look_sprites = ("left", "right")
    movement._look_around_ready_at = 200.0
    with (
        patch("kinito.movement.time.monotonic", return_value=150.0),
        patch("kinito.movement.random.random", return_value=0.99) as roll,
    ):
        assert movement._pick_normal_idle_sprite(crouch=False) == "default"
    roll.assert_not_called()


def test_pick_normal_idle_sprite_crouch_uses_standing2_pool(movement):
    movement.tk_img_normal_2 = "crouch-default"
    movement._standing2_look_sprites = ("crouch-left",)
    movement._look_around_ready_at = 0.0
    with patch("kinito.movement.random.random", return_value=0.1):
        assert movement._pick_normal_idle_sprite(crouch=True) == "crouch-default"


def test_run_reading_idle_can_use_glasses_sprites(movement):
    movement.tk_img_idle = "idle"
    movement.tk_img_idle_2 = "idle2"
    movement._reading_sprites = ("idle", "idle2")
    movement._reading_glasses_sprites = ("glasses", "glasses2")
    movement.change_sprite = MagicMock()
    movement._is_reading_idle_active = MagicMock(return_value=False)
    movement.offer_random_story = MagicMock()
    movement.say_random_wisdom = MagicMock()

    with (
        patch("kinito.movement.random.random", side_effect=[0.0, 1.0, 1.0]),
        patch("kinito.movement.random.randint", return_value=1),
        patch("kinito.movement.time.sleep"),
    ):
        movement._run_reading_idle()

    movement.change_sprite.assert_called_with("glasses")


def test_run_reading_idle_uses_normal_sprites_when_glasses_miss(movement):
    movement.tk_img_idle = "idle"
    movement._reading_sprites = ("idle", "idle2")
    movement._reading_glasses_sprites = ("glasses", "glasses2")
    movement.change_sprite = MagicMock()
    movement._is_reading_idle_active = MagicMock(return_value=False)
    movement.offer_random_story = MagicMock()
    movement.say_random_wisdom = MagicMock()

    with (
        patch("kinito.movement.random.random", side_effect=[0.99, 1.0, 1.0]),
        patch("kinito.movement.random.randint", return_value=1),
        patch("kinito.movement.time.sleep"),
    ):
        movement._run_reading_idle()

    movement.change_sprite.assert_called_with("idle")


def _configure_mouse_attention(movement):
    movement._startup_complete = True
    movement._running = True
    movement.paused = False
    movement.is_dragging = False
    movement.moving = False
    movement.talking = False
    movement._fancy_mode = False
    movement._reading_idle_active = False
    movement._hug_mode = False
    movement._preserve_sprite = False
    movement._ai_generating = False
    movement._focus_mode = False
    movement._chat_mode = False
    movement._awaiting_response = False
    movement._mouse_look_active = False
    movement._mouse_follow_state = "idle"
    movement._mouse_follow_ready_at = 0.0
    movement._mouse_look_direction = "center"
    movement.x = 100
    movement.y = 200
    movement._window_screen_size = MagicMock(return_value=(40, 80))
    movement._standing_dir_sprites = {
        "center": "look_center",
        "left": "look_left",
        "right": "look_right",
        "top": "look_top",
        "bottom": "look_bottom",
        "top_left": "look_top_left",
        "top_right": "look_top_right",
        "bottom_left": "look_bottom_left",
        "bottom_right": "look_bottom_right",
    }
    movement.change_sprite = MagicMock()
    movement._schedule_mouse_attention_poll = MagicMock()
    movement._is_busy_with_speech = MagicMock(return_value=False)
    movement._is_game_active = MagicMock(return_value=False)


def test_can_look_at_mouse_blocked_during_fancy(movement):
    _configure_mouse_attention(movement)
    movement._fancy_mode = True
    assert movement._can_look_at_mouse() is False


def test_can_look_at_mouse_blocked_during_reading(movement):
    _configure_mouse_attention(movement)
    movement._reading_idle_active = True
    assert movement._can_look_at_mouse() is False


def test_can_look_at_mouse_allowed_in_chat(movement):
    _configure_mouse_attention(movement)
    movement._chat_mode = True
    movement.talking = True
    assert movement._can_look_at_mouse() is True
    assert movement._can_follow_mouse() is False


def test_update_mouse_attention_looks_right(movement):
    _configure_mouse_attention(movement)
    # Outside follow radius (180) but inside look radius (280).
    movement.root.winfo_pointerx.return_value = 340
    movement.root.winfo_pointery.return_value = 240
    movement._update_mouse_attention()
    assert movement._mouse_look_active is True
    assert movement._mouse_look_direction == "right"
    movement.change_sprite.assert_called_with("look_right")
    assert movement._mouse_follow_state == "idle"


def test_update_mouse_attention_skips_busy_modes(movement):
    _configure_mouse_attention(movement)
    movement._fancy_mode = True
    movement.root.winfo_pointerx.return_value = 120
    movement.root.winfo_pointery.return_value = 240
    movement._update_mouse_attention()
    assert movement._mouse_look_active is False
    movement.change_sprite.assert_not_called()


def test_finish_mouse_think_declines_follow(movement):
    _configure_mouse_attention(movement)
    movement._mouse_follow_state = "thinking"
    with (
        patch("kinito.movement.random.random", return_value=0.99),
        patch("kinito.movement.random.uniform", return_value=20.0),
    ):
        movement._finish_mouse_think(150, 240)
    assert movement._mouse_follow_state == "idle"
    assert movement._mouse_follow_ready_at > 0
    movement.play_sfx.assert_not_called()


def test_finish_mouse_think_starts_chase(movement):
    _configure_mouse_attention(movement)
    movement._mouse_follow_state = "thinking"
    movement.move_towards = MagicMock()
    movement._finish_surf_movement = MagicMock()
    movement._on_mouse_chase_finished = MagicMock()

    with (
        patch("kinito.movement.random.random", return_value=0.0),
        patch("kinito.movement.threading.Thread") as mock_thread,
    ):
        mock_thread.return_value = MagicMock()
        movement._finish_mouse_think(250, 240)

    assert movement._mouse_follow_state == "chasing"
    assert movement.moving is True
    mock_thread.assert_called_once()
    worker = mock_thread.call_args.kwargs["target"]
    worker()
    movement.move_towards.assert_called_once()
    movement.play_sfx.assert_called_once()


def test_idle_skips_sprite_when_mouse_look_active(movement):
    _configure_mouse_attention(movement)
    movement._mouse_look_active = True
    movement._running = True
    calls = {"n": 0}

    def stop_after_one_sleep(_seconds):
        calls["n"] += 1
        if calls["n"] >= 1:
            movement._running = False

    with patch("kinito.movement.time.sleep", side_effect=stop_after_one_sleep):
        movement.idle_animation()

    movement.change_sprite.assert_not_called()
