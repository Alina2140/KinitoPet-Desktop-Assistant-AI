from unittest.mock import MagicMock, patch

import pytest

from content import dialogue as dlg
from kinito.features.glitch import GlitchMixin


class GlitchStub(GlitchMixin):
    pass


@pytest.fixture
def glitch():
    stub = GlitchStub()
    stub._running = True
    stub._screen_effects_enabled = True
    stub.paused = False
    stub.is_dragging = False
    stub._camera_active = False
    stub._browser_active = False
    stub._glitch_window = None
    stub._glitch_hide_timer = None
    stub._glitch_tk_image = None
    stub.root = MagicMock()
    stub.root.after = MagicMock()
    stub.root.after_cancel = MagicMock()
    stub.root.update_idletasks = MagicMock()
    stub.root.winfo_vrootx.return_value = 0
    stub.root.winfo_vrooty.return_value = 0
    stub.root.winfo_vrootwidth.return_value = 1920
    stub.root.winfo_vrootheight.return_value = 1080
    stub.speak = MagicMock()
    return stub


def test_maybe_trigger_screen_glitch_respects_disabled(glitch):
    glitch._screen_effects_enabled = False
    assert glitch.maybe_trigger_screen_glitch() is False
    glitch.root.after.assert_not_called()


def test_maybe_trigger_screen_glitch_respects_paused(glitch):
    glitch.paused = True
    assert glitch.maybe_trigger_screen_glitch() is False
    glitch.root.after.assert_not_called()


def test_maybe_trigger_screen_glitch_schedules_on_hit(glitch):
    with patch("kinito.features.glitch.random.random", return_value=0.0):
        assert glitch.maybe_trigger_screen_glitch() is True
    glitch.root.after.assert_called_once_with(0, glitch._flash_screen_glitch)


def test_maybe_trigger_screen_glitch_skips_on_miss(glitch):
    with patch("kinito.features.glitch.random.random", return_value=0.99):
        assert glitch.maybe_trigger_screen_glitch() is False
    glitch.root.after.assert_not_called()


def test_maybe_trigger_blue_screen_schedules_on_hit(glitch):
    with (
        patch("kinito.features.glitch.os.path.isfile", return_value=True),
        patch("kinito.features.glitch.random.random", return_value=0.0),
    ):
        assert glitch.maybe_trigger_blue_screen() is True
    glitch.root.after.assert_called_once_with(0, glitch._flash_blue_screen)


def test_maybe_trigger_blue_screen_skips_when_image_missing(glitch):
    with patch("kinito.features.glitch.os.path.isfile", return_value=False):
        assert glitch.maybe_trigger_blue_screen() is False
    glitch.root.after.assert_not_called()


def test_toggle_screen_effects_disables(glitch):
    glitch.toggle_screen_effects()
    assert glitch._screen_effects_enabled is False
    glitch.speak.assert_called_once()
    assert glitch.speak.call_args[0][0] in dlg.SCREEN_EFFECTS_OFF_LINES


def test_toggle_screen_effects_enables(glitch):
    glitch._screen_effects_enabled = False
    glitch.toggle_screen_effects()
    assert glitch._screen_effects_enabled is True
    assert glitch.speak.call_args[0][0] in dlg.SCREEN_EFFECTS_ON_LINES
