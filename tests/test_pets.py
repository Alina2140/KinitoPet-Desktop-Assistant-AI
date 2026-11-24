from unittest.mock import MagicMock, patch

import pytest

from content import dialogue as dlg
from kinito.features.pets import (
    PET_STATE_DANCE,
    PET_STATE_FOLLOW,
    PET_STATE_LEAVE,
    PET_STATE_SLEEP,
    MiniPet,
    PetsMixin,
)


class PetsStub(PetsMixin):
    pass


CATALOG = [
    {"id": "kinito", "name": "Kinito", "path": "p1", "sleep_path": ""},
    {"id": "jade", "name": "Jade", "path": "p2", "sleep_path": ""},
    {"id": "sam", "name": "Sam", "path": "p3", "sleep_path": ""},
]


@pytest.fixture
def pets():
    stub = PetsStub()
    stub._pets = []
    stub._pets_enabled = True
    stub._pets_max_count = 1
    stub._pet_enabled_sprites = None
    stub._pet_sprite_catalog = list(CATALOG)
    stub._pet_tick_timer = None
    stub._pet_settings_window = None
    stub._last_pet_spawn_at = 0.0
    stub._last_pet_dismiss_at = 0.0
    stub._running = True
    stub._startup_complete = True
    stub._focus_mode = False
    stub._is_game_active = MagicMock(return_value=False)
    stub._is_busy_with_speech = MagicMock(return_value=False)
    stub._is_background_music_playing = MagicMock(return_value=False)
    stub.paused = False
    stub.x = 500
    stub.y = 400
    stub.root = MagicMock()
    stub.speak = MagicMock()
    return stub


def _fake_pet(app, sprite_id="jade", *, with_sleep=True):
    photos = {"right": MagicMock(), "left": MagicMock()}
    if with_sleep:
        photos["sleep"] = MagicMock()
    sprite = {"id": sprite_id, "name": sprite_id.capitalize(),
              "path": "p", "sleep_path": ""}
    pet = MiniPet(app, sprite, photos)
    pet.window = MagicMock()
    pet.label = MagicMock()
    return pet


def _patched_spawn(stub):
    """Patch photo loading + window creation so spawn_pet needs no real Tk."""
    def _create(pet, x, y):
        pet.x, pet.y = x, y
        pet.window = MagicMock()
        pet.label = MagicMock()

    return patch.multiple(
        "kinito.features.pets",
        _load_pet_photos=MagicMock(
            return_value={"right": MagicMock(), "left": MagicMock()}
        ),
    ), patch.object(MiniPet, "create_window", _create)


def test_spawn_pet_respects_max_count(pets):
    pets._pets.append(_fake_pet(pets))
    assert pets._pet_max_count() == 1
    assert pets.spawn_pet() is False
    assert len(pets._pets) == 1


def test_spawn_pet_no_enabled_sprites_speaks_hint(pets):
    pets._pet_enabled_sprites = set()
    assert pets.spawn_pet() is False
    pets.speak.assert_called_once()
    assert pets.speak.call_args[0][0] == dlg.PET_NO_SPRITES_LINE


def test_spawn_pet_only_enabled_sprite_picked(pets):
    pets._pet_enabled_sprites = {"jade"}
    pets._pets_max_count = 3
    photos_patch, create_patch = _patched_spawn(pets)
    with photos_patch, create_patch:
        for _ in range(3):
            assert pets.spawn_pet() is True
    assert len(pets._pets) == 3
    assert all(p.sprite_id == "jade" for p in pets._pets)


def test_spawn_pet_may_speak_summon_line(pets):
    photos_patch, create_patch = _patched_spawn(pets)
    with photos_patch, create_patch, patch(
        "kinito.features.pets.random.random", return_value=0.0
    ):
        assert pets.spawn_pet() is True
    pets.speak.assert_called_once()
    assert pets.speak.call_args[0][0] in dlg.PET_SUMMON_LINES


def test_maybe_trigger_pet_blocked_when_not_running(pets):
    pets._running = False
    assert pets.maybe_trigger_pet() is False


def test_maybe_trigger_pet_blocked_in_focus_mode(pets):
    pets._focus_mode = True
    assert pets.maybe_trigger_pet() is False


def test_maybe_trigger_pet_blocked_at_max_count(pets):
    pets._pets.append(_fake_pet(pets))
    assert pets.maybe_trigger_pet() is False


def test_maybe_trigger_pet_blocked_without_sprites(pets):
    pets._pet_enabled_sprites = set()
    assert pets.maybe_trigger_pet() is False


def test_maybe_trigger_pet_blocked_during_cooldown(pets):
    pets._last_pet_spawn_at = 1e12
    with patch("kinito.features.pets.random.random", return_value=0.0):
        assert pets.maybe_trigger_pet() is False


def test_maybe_trigger_pet_blocked_when_weight_zero(pets):
    pets._activity_chance_mult = MagicMock(return_value=0.0)
    with patch("kinito.features.pets.random.random", return_value=0.0):
        assert pets.maybe_trigger_pet() is False


def test_maybe_trigger_pet_hit_schedules_spawn(pets):
    with patch("kinito.features.pets.random.random", return_value=0.0):
        assert pets.maybe_trigger_pet() is True
    assert pets._last_pet_spawn_at > 0
    pets.root.after.assert_called_once_with(0, pets._start_random_pet_spawn)


def test_maybe_dismiss_pet_without_pets(pets):
    assert pets.maybe_dismiss_pet() is False


def test_maybe_dismiss_pet_blocked_while_speaking(pets):
    pets._pets.append(_fake_pet(pets))
    pets._is_busy_with_speech.return_value = True
    with patch("kinito.features.pets.random.random", return_value=0.0):
        assert pets.maybe_dismiss_pet() is False


def test_maybe_dismiss_pet_hit_speaks_line_and_sends_away(pets):
    pet = _fake_pet(pets)
    pets._pets.append(pet)
    pets._pet_screen_rect = MagicMock(return_value=(0, 0, 1920, 1080))
    with patch("kinito.features.pets.random.random", return_value=0.0):
        assert pets.maybe_dismiss_pet() is True
    pets._kinito_dismiss_pet()
    pets.speak.assert_called_once()
    assert pets.speak.call_args[0][0] in dlg.PET_SEND_AWAY_LINES
    assert pet.state == PET_STATE_LEAVE


def test_pet_tick_sleep_when_kinito_paused(pets):
    pets.paused = True
    pet = _fake_pet(pets)
    pet.orbit_angle = 0.0  # sleep spot lands on +70 offset
    pet.x, pet.y = pets.x + 70.0, pets.y + 40.0
    pet.tick(1000.0)
    assert pet.state == PET_STATE_SLEEP
    assert pet.sleeping is True


def test_pet_tick_wakes_after_pause(pets):
    pet = _fake_pet(pets)
    pet.sleeping = True
    pet.state = PET_STATE_SLEEP
    pet.x, pet.y = pets.x, pets.y + 30.0
    pet.tick(1000.0)
    assert pet.sleeping is False
    assert pet.state == PET_STATE_FOLLOW


def test_pet_tick_returns_when_too_far(pets):
    pet = _fake_pet(pets)
    pet.state = "wander"
    pet.x, pet.y = pets.x + 2000.0, pets.y
    pet.away_since = 0.0
    pet.tick(1000.0)
    assert pet.state == PET_STATE_FOLLOW


def test_pet_tick_dances_to_music(pets):
    pets._is_background_music_playing.return_value = True
    pet = _fake_pet(pets)
    pet.state = PET_STATE_DANCE
    pet.dance_until = 2000.0
    pet.tick(1000.0)
    pet.window.geometry.assert_called()


def test_pet_leave_reaches_edge_and_destroys(pets):
    pets._pet_screen_rect = MagicMock(return_value=(0, 0, 1920, 1080))
    pet = _fake_pet(pets)
    pet.x, pet.y = -70.0, 500.0  # just inside the left-edge exit point
    window = pet.window
    pet.state = PET_STATE_LEAVE
    for _ in range(3):
        pet.tick(1000.0)
    assert pet.destroyed is True
    window.destroy.assert_called_once()


def test_pet_leave_target_stays_fixed(pets):
    """A leaving pet must not re-pick its edge each tick (seam ping-pong)."""
    pets._pet_screen_rect = MagicMock(return_value=(0, 0, 1920, 1080))
    pet = _fake_pet(pets)
    pet.x, pet.y = 960.0, 540.0
    pet.state = PET_STATE_LEAVE
    pet.tick(1000.0)
    first_target = pet.target
    pet.tick(1001.0)
    pet.tick(1002.0)
    assert pet.target == first_target


def test_pet_leave_retargets_exit_after_drag(pets):
    pets._pet_screen_rect = MagicMock(return_value=(0, 0, 1920, 1080))
    pet = _fake_pet(pets)
    pet.x, pet.y = 960.0, 540.0
    pet.state = PET_STATE_LEAVE
    pet.tick(1000.0)
    first_target = pet.target
    pet.dragging = True
    pet.x, pet.y = 1800.0, 540.0  # user dragged it elsewhere
    pet._on_drag_end()
    assert pet.target != first_target
    assert pet.target[0] > 1900  # now exits via the right edge
    pet.dragging = True
    pet.x, pet.y = 100.0, 540.0  # dragged left -> exits left, not up
    pet._on_drag_end()
    assert pet.target[0] < 0
    assert pet.target[1] == 540.0


def test_dismiss_pet_removes_from_list_when_not_animated(pets):
    pet = _fake_pet(pets)
    pets._pets.append(pet)
    pets.dismiss_pet(pet, animate=False)
    assert pet not in pets._pets
    assert pet.destroyed is True


def test_dismiss_all_pets_destroys_everything(pets):
    pets._pets.extend([_fake_pet(pets), _fake_pet(pets, "sam")])
    pets.dismiss_all_pets(destroy=True)
    assert pets._pets == []


def test_pet_drag_moves_window_and_pauses_tick(pets):
    pet = _fake_pet(pets)
    pet.x, pet.y = 100.0, 100.0
    pet._on_drag_start(MagicMock(x_root=110, y_root=110))
    assert pet.dragging is True
    pet._on_drag_move(MagicMock(x_root=300, y_root=250))
    assert pet.x == 300.0 - 10
    assert pet.y == 250.0 - 10
    pet.window.geometry.assert_called()
    # While held, the state machine stays frozen (no auto-move).
    pet._move_toward = MagicMock()
    pet.tick(1000.0)
    pet._move_toward.assert_not_called()
    pet._on_drag_end()
    assert pet.dragging is False


def test_pet_drag_flips_facing(pets):
    pet = _fake_pet(pets)
    pet.x, pet.y = 200.0, 100.0
    pet._on_drag_start(MagicMock(x_root=200, y_root=100))
    pet._on_drag_move(MagicMock(x_root=100, y_root=100))
    assert pet.facing_left is True


def test_send_away_button_dismisses_pet(pets):
    pet = _fake_pet(pets)
    pets._pets.append(pet)
    pets.dismiss_pet = MagicMock()
    pet._send_away_clicked()
    pets.dismiss_pet.assert_called_once_with(pet)


def test_sprite_toggle_all_enabled_resets_to_default(pets):
    pets._persist_pet_settings = MagicMock()
    var = MagicMock()
    var.get.return_value = 1
    sprite_vars = {"kinito": var, "jade": var, "sam": var}
    save = pets._pet_sprites_toggled(sprite_vars, CATALOG)
    save()
    assert pets._pet_enabled_sprites is None
    pets._persist_pet_settings.assert_called_once()


def test_pet_lines_do_not_match_dialog_specs():
    """Pet lines must not contain dialog markers (e.g. "settings!")."""
    from content.dialog_registry import find_dialog_spec

    for line in (
        dlg.PET_SUMMON_LINES
        + dlg.PET_SEND_AWAY_LINES
        + dlg.PETS_SETTINGS_OPEN_LINES
        + dlg.PETS_ON_LINES
        + dlg.PETS_OFF_LINES
        + [dlg.PET_NO_SPRITES_LINE, dlg.PET_DISABLED_LINE]
    ):
        assert find_dialog_spec(line) is None, line


def test_sprite_toggle_partial_selection_persists(pets):
    pets._persist_pet_settings = MagicMock()
    on, off = MagicMock(), MagicMock()
    on.get.return_value = 1
    off.get.return_value = 0
    sprite_vars = {"kinito": off, "jade": on, "sam": off}
    save = pets._pet_sprites_toggled(sprite_vars, CATALOG)
    save()
    assert pets._pet_enabled_sprites == {"jade"}


def test_toggle_pets_off_dismisses_all(pets):
    pet = _fake_pet(pets)
    pets._pets.append(pet)
    pets._persist_settings = MagicMock()
    pets.toggle_pets()
    assert pets._pets_enabled is False
    assert pet.state == PET_STATE_LEAVE
    pets.speak.assert_called_once()
    assert pets.speak.call_args[0][0] in dlg.PETS_OFF_LINES
    pets._persist_settings.assert_called_once()


def test_toggle_pets_on_speaks_line(pets):
    pets._pets_enabled = False
    pets._persist_settings = MagicMock()
    pets.toggle_pets()
    assert pets._pets_enabled is True
    pets.speak.assert_called_once()
    assert pets.speak.call_args[0][0] in dlg.PETS_ON_LINES


def test_spawn_pet_blocked_when_disabled(pets):
    pets._pets_enabled = False
    assert pets.spawn_pet() is False
    pets.speak.assert_called_once()
    assert pets.speak.call_args[0][0] == dlg.PET_DISABLED_LINE
    assert pets._pets == []


def test_maybe_trigger_pet_blocked_when_disabled(pets):
    pets._pets_enabled = False
    assert pets.maybe_trigger_pet() is False
