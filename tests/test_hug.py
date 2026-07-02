from unittest.mock import MagicMock, patch

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
    stub.tk_img_normal = "normal"
    stub._hug_timer = None
    stub._hug_mode = False
    stub.talking = False
    stub.speak = MagicMock()
    stub.change_sprite = MagicMock()
    return stub


def test_give_hug_shows_hug_sprite_and_speaks(hug):
    with (
        patch("kinito.features.hug.random.choice", return_value=HUG_LINES[0]),
        patch.object(hug, "_schedule_hug_end") as schedule,
    ):
        hug.give_hug()
    hug.change_sprite.assert_called_once_with("hug")
    schedule.assert_called_once()
    assert hug._hug_mode is True
    hug.speak.assert_called_once_with(HUG_LINES[0])


def test_end_hug_restores_normal_sprite_when_idle(hug):
    hug._hug_mode = True
    hug.end_hug()
    assert hug._hug_mode is False
    hug.change_sprite.assert_called_once_with("normal")


def test_end_hug_keeps_sprite_while_talking(hug):
    hug._hug_mode = True
    hug.talking = True
    hug.end_hug()
    assert hug._hug_mode is False
    hug.change_sprite.assert_not_called()
