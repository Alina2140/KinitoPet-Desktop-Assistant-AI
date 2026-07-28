from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

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
    stub._crash_window = None
    stub._crash_blackout_window = None
    stub._crash_hide_timer = None
    stub._crash_tk_image = None
    stub.root = MagicMock()
    stub.root.after = MagicMock()
    stub.root.after_cancel = MagicMock()
    stub.root.update_idletasks = MagicMock()
    stub.root.winfo_vrootx.return_value = -1920
    stub.root.winfo_vrooty.return_value = 0
    stub.root.winfo_vrootwidth.return_value = 3840
    stub.root.winfo_vrootheight.return_value = 1080
    stub.root.winfo_screenwidth.return_value = 1920
    stub.root.winfo_screenheight.return_value = 1080
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


def test_raise_screen_effect_overlays_lifts_active_windows(glitch):
    overlay = MagicMock()
    overlay.winfo_exists.return_value = True
    blackout = MagicMock()
    blackout.winfo_exists.return_value = True
    crash = MagicMock()
    crash.winfo_exists.return_value = True
    glitch._glitch_window = overlay
    glitch._crash_blackout_window = blackout
    glitch._crash_window = crash
    glitch._force_window_topmost = MagicMock()

    glitch._raise_screen_effect_overlays()

    overlay.wm_attributes.assert_called_with("-topmost", True)
    overlay.lift.assert_called_once()
    blackout.lift.assert_called_once()
    crash.lift.assert_called_once()
    # Blackout is raised before the BSOD so the crash image stays on top.
    assert glitch._force_window_topmost.call_args_list == [
        ((overlay,),),
        ((blackout,),),
        ((crash,),),
    ]


def test_schedule_raise_screen_effect_overlays_debounces(glitch):
    glitch._glitch_window = MagicMock()
    glitch._glitch_window.winfo_exists.return_value = True
    glitch._raise_screen_effect_overlays = MagicMock()

    glitch._schedule_raise_screen_effect_overlays()
    glitch._schedule_raise_screen_effect_overlays()

    assert glitch.root.after.call_count == 1
    callback = glitch.root.after.call_args[0][1]
    callback()
    glitch._raise_screen_effect_overlays.assert_called_once()
    assert glitch._raise_overlay_pending is False


def test_flash_blue_screen_primary_only_with_virtual_blackout(glitch):
    crash_img = Image.new("RGB", (100, 50), color=(0, 0, 255))
    blackout = MagicMock()
    primary = MagicMock()
    overlays = iter([blackout, primary])

    glitch._overlay_virtual_screen_rect = MagicMock(return_value=(-1920, 0, 3840, 1080))
    glitch._overlay_primary_screen_rect = MagicMock(return_value=(0, 0, 1920, 1080))
    glitch._raise_screen_effect_overlays = MagicMock()

    with (
        patch("kinito.features.glitch.Image.open", return_value=crash_img),
        patch("kinito.features.glitch.ImageTk.PhotoImage", return_value=MagicMock()),
        patch("kinito.features.glitch.tk.Label", return_value=MagicMock()),
        patch.object(glitch, "_make_overlay_window", side_effect=lambda **kwargs: next(overlays)) as make,
    ):
        glitch._flash_blue_screen()

    assert make.call_args_list[0].kwargs == {
        "x": -1920,
        "y": 0,
        "width": 3840,
        "height": 1080,
    }
    assert make.call_args_list[1].kwargs == {
        "x": 0,
        "y": 0,
        "width": 1920,
        "height": 1080,
    }
    assert glitch._crash_blackout_window is blackout
    assert glitch._crash_window is primary
    glitch.root.after.assert_called_once_with(
        glitch.BLUE_SCREEN_DURATION_MS,
        glitch.hide_blue_screen,
    )


def test_hide_blue_screen_destroys_blackout_and_crash(glitch):
    crash = MagicMock()
    blackout = MagicMock()
    glitch._crash_window = crash
    glitch._crash_blackout_window = blackout
    glitch._crash_hide_timer = "timer"
    glitch._crash_tk_image = MagicMock()

    glitch.hide_blue_screen()

    crash.destroy.assert_called_once()
    blackout.destroy.assert_called_once()
    assert glitch._crash_window is None
    assert glitch._crash_blackout_window is None
    assert glitch._crash_tk_image is None
