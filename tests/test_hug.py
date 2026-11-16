from unittest.mock import ANY, MagicMock, patch

import pytest

from content.hug_lines import HUG_LINES
from kinito.features.hug import HugMixin


class HugStub(HugMixin):
    pass


@pytest.fixture
def hug():
    stub = HugStub()
    stub.root = MagicMock()
    stub.root.after = MagicMock()
    stub.root.after_cancel = MagicMock()
    stub.tk_img_hug = "hug"
    stub.tk_img_hug2 = "hug2"
    stub._hug_sprites = ("hug", "hug2", "hug3")
    stub._hug_frame = 0
    stub.tk_img_normal = "normal"
    stub._hug_timer = None
    stub._hug_mode = False
    stub.talking = False
    stub.speak = MagicMock()
    stub.change_sprite = MagicMock()
    return stub


def test_ask_for_hug_asks_yes_no(hug):
    from content import dialogue as dlg

    with patch("content.dialogue.pick_line", return_value=dlg.HUG_QUESTIONS[0]):
        hug.ask_for_hug()
    hug.speak.assert_called_once_with(dlg.HUG_QUESTIONS[0], 45, True)
    assert getattr(hug, "_begin_hug_after_speech", False) is False


def test_give_hug_defers_pose_until_speech(hug):
    with patch("content.dialogue.pick_line_for_mood", return_value=HUG_LINES[0]):
        hug.give_hug()
    hug.change_sprite.assert_not_called()
    assert hug._begin_hug_after_speech is True
    hug.speak.assert_called_once_with(HUG_LINES[0], ai_hint=ANY)


def test_enter_hug_pose_shows_sprite(hug):
    with patch.object(hug, "_schedule_hug_end") as schedule:
        hug._enter_hug_pose()
    hug.change_sprite.assert_called_once_with("hug")
    schedule.assert_not_called()
    assert hug._hug_mode is True
    assert hug._hug_frame == 0


def test_next_hug_sprite_advances_to_final_frame_and_holds(hug):
    assert hug._next_hug_sprite() == "hug2"
    assert hug._next_hug_sprite() == "hug3"
    assert hug._next_hug_sprite() is None
    assert hug._hug_frame == 2


def test_next_hug_sprite_falls_back_to_pair(hug):
    hug._hug_sprites = ()
    hug._hug_frame = 0
    assert hug._next_hug_sprite() == "hug2"
    assert hug._next_hug_sprite() is None


def test_hug_sprite_delay_is_faster_for_intro_frames(hug):
    assert hug._hug_sprite_delay() == 0.4
    hug._hug_frame = 1
    assert hug._hug_sprite_delay() == 0.4
    hug._hug_frame = 2
    assert hug._hug_sprite_delay() == 1.0


def test_end_hug_restores_normal_sprite_when_idle(hug):
    hug._hug_mode = True
    hug.end_hug()
    assert hug._hug_mode is False
    hug.change_sprite.assert_called_once_with("normal")
    assert hug._hug_frame == 0


def test_end_hug_keeps_sprite_while_talking(hug):
    hug._hug_mode = True
    hug.talking = True
    hug.end_hug()
    assert hug._hug_mode is False
    hug.change_sprite.assert_not_called()
