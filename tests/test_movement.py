from unittest.mock import MagicMock, patch

import pytest

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
    event = MagicMock(x_root=50, y_root=60)
    movement.on_mouse_down(event)
    assert movement.is_dragging is True
    assert movement.moving is False
    assert movement._drag_moved is False
    movement.stop_background_music.assert_called_once()
    movement.play_sfx.assert_called_once()


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
    movement.root.winfo_rootx.side_effect = [0, 5, 10, 15, 20]
    movement.root.winfo_rooty.return_value = 0
    movement._running = True
    movement.move_towards(20, 0, speed=5)
    assert movement.root.geometry.called


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
