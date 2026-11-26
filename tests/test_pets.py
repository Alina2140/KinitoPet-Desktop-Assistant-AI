import math
import time
from unittest.mock import MagicMock, patch

import pytest

from content import dialogue as dlg
from kinito.features.pets import (
    PET_STATE_DANCE,
    PET_STATE_FOLLOW,
    PET_STATE_HOPOUT,
    PET_STATE_LEAVE,
    PET_STATE_REST,
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
    photos = {
        key: MagicMock(width=lambda: 60, height=lambda: 50)
        for key in ("right", "left")
    }
    if with_sleep:
        photos["sleep"] = MagicMock(width=lambda: 60, height=lambda: 50)
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


def test_spawn_startup_pets_spawns_each_enabled_sprite_once(pets):
    pets._pets_spawn_at_startup = True
    pets._pets_max_count = 3
    photos_patch, create_patch = _patched_spawn(pets)
    with photos_patch, create_patch:
        pets._spawn_startup_pets()
    assert sorted(p.sprite_id for p in pets._pets) == ["jade", "kinito", "sam"]


def test_spawn_startup_pets_restores_last_lineup_with_duplicates(pets):
    pets._pets_spawn_at_startup = True
    pets._pets_max_count = 3
    pets._pet_startup_sprites = ["jade", "jade", "jade"]
    photos_patch, create_patch = _patched_spawn(pets)
    with photos_patch, create_patch:
        pets._spawn_startup_pets()
    assert [p.sprite_id for p in pets._pets] == ["jade", "jade", "jade"]


def test_spawn_startup_pets_filters_stored_by_enabled(pets):
    pets._pets_spawn_at_startup = True
    pets._pets_max_count = 3
    pets._pet_enabled_sprites = {"jade"}
    pets._pet_startup_sprites = ["sam", "jade", "kinito"]
    photos_patch, create_patch = _patched_spawn(pets)
    with photos_patch, create_patch:
        pets._spawn_startup_pets()
    assert [p.sprite_id for p in pets._pets] == ["jade"]


def test_stop_pets_persists_current_lineup(pets):
    pets._pets_max_count = 3
    pets._pets = [_fake_pet(pets, "jade"), _fake_pet(pets, "sam")]
    pets._settings = MagicMock()
    pets._stop_pets()
    pets._settings.set_pet_startup_sprites.assert_called_once_with(
        ["jade", "sam"]
    )


def test_stop_pets_lineup_skips_leaving_and_caps_at_max(pets):
    leaving = _fake_pet(pets, "jade")
    leaving.state = PET_STATE_LEAVE
    pets._pets = [_fake_pet(pets, "jade"), _fake_pet(pets, "sam"), leaving]
    pets._pets_max_count = 1
    pets._settings = MagicMock()
    pets._stop_pets()
    pets._settings.set_pet_startup_sprites.assert_called_once_with(["jade"])


def test_stop_pets_second_call_keeps_saved_lineup(pets):
    """Shutdown calls _stop_pets twice; the lineup must not be wiped."""
    pet = _fake_pet(pets, "jade")
    pets._pets = [pet]
    pets._settings = MagicMock()
    pets._stop_pets()
    pet.destroyed = True  # hop-out finished before root destroy
    pets._stop_pets()
    pets._settings.set_pet_startup_sprites.assert_called_once_with(["jade"])


def test_spawn_startup_pets_respects_max_count(pets):
    pets._pets_spawn_at_startup = True
    pets._pets_max_count = 1
    pets._pet_enabled_sprites = {"jade", "sam"}
    photos_patch, create_patch = _patched_spawn(pets)
    with photos_patch, create_patch:
        pets._spawn_startup_pets()
    assert len(pets._pets) == 1
    assert pets._pets[0].sprite_id == "jade"  # catalog order wins


def test_spawn_startup_pets_respects_toggle(pets):
    pets._pets_spawn_at_startup = False
    pets.spawn_pet = MagicMock()
    pets._spawn_startup_pets()
    pets.spawn_pet.assert_not_called()


def test_spawn_startup_pets_blocked_when_pets_disabled(pets):
    pets._pets_spawn_at_startup = True
    pets._pets_enabled = False
    pets.spawn_pet = MagicMock()
    pets._spawn_startup_pets()
    pets.spawn_pet.assert_not_called()


def test_persist_pet_settings_saves_startup_flag(pets):
    pets._pets_spawn_at_startup = True
    pets._settings = MagicMock()
    pets._settings.set_pet_enabled_sprites = MagicMock()
    pets._persist_pet_settings()
    pets._settings.update.assert_called_once_with(
        pets_max_count=1, pets_spawn_at_startup=True
    )


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


def test_sleep_spots_do_not_overlap_for_same_orbit(pets):
    pets._window_screen_size = lambda: (240, 180)
    pets._buddy_center = lambda: (620.0, 490.0)
    pets._pet_work_rect = lambda *_: (0, 0, 1920, 1080)
    pets._pets = [_fake_pet(pets) for _ in range(3)]
    for pet in pets._pets:
        pet.orbit_angle = 0.0
    spots = [pets._pet_sleep_spot_for(pet) for pet in pets._pets]
    assert all(y >= 580 for _, y in spots)
    assert all(spots[i + 1][0] - spots[i][0] >= 68 for i in range(2))
    assert spots == [pets._pet_sleep_spot_for(pet) for pet in pets._pets]


@pytest.mark.parametrize("count", [1, 2, 3])
@pytest.mark.parametrize("center", [(120, 90), (940, 690), (-1100, 690)])
def test_sleep_layout_fits_monitor_and_pet_sizes(pets, count, center):
    mx = -1200 if center[0] < 0 else 0
    pets._pet_work_rect = lambda *_: (mx, 0, 1000, 800)
    pets._window_screen_size = lambda: (200, 140)
    pets._buddy_center = lambda: center
    pets._pets = [_fake_pet(pets, with_sleep=i != 1) for i in range(count)]
    for i, pet in enumerate(pets._pets):
        if "sleep" in pet.photos:
            pet.photos["sleep"].width = MagicMock(return_value=90 + 10 * i)
            pet.photos["sleep"].height = MagicMock(return_value=70)
    boxes = []
    for pet in pets._pets:
        x, y = pets._pet_sleep_spot_for(pet)
        w = max(photo.width() for photo in pet.photos.values())
        h = max(photo.height() for photo in pet.photos.values())
        assert mx <= x <= mx + 1000 - w
        assert 0 <= y <= 800 - h
        boxes.append((x, y, w, h))
    for i, (x, y, w, h) in enumerate(boxes):
        for ox, oy, ow, oh in boxes[i + 1:]:
            assert x + w <= ox or ox + ow <= x or y + h <= oy or oy + oh <= y


def test_sleep_layout_wraps_on_narrow_monitor(pets):
    pets._pet_work_rect = lambda *_: (0, 0, 150, 800)
    pets._window_screen_size = lambda: (100, 100)
    pets._buddy_center = lambda: (75, 100)
    pets._pets = [_fake_pet(pets) for _ in range(3)]
    spots = [pets._pet_sleep_spot_for(pet) for pet in pets._pets]
    assert len(set(spots)) == 3
    assert len({y for _, y in spots}) > 1
    assert all(0 <= x <= 90 and 150 <= y <= 750 for x, y in spots)


def test_sleep_layout_ignores_leaving_and_destroyed_pets(pets):
    pets._pet_work_rect = lambda *_: (0, 0, 1920, 1080)
    pets._pets = [_fake_pet(pets) for _ in range(3)]
    first, leaving, destroyed = pets._pets
    leaving.state = PET_STATE_LEAVE
    destroyed.destroyed = True
    spot = pets._pet_sleep_spot_for(first)
    pets._pets = [first]
    assert pets._pet_sleep_spot_for(first) == spot
    extra = _fake_pet(pets)
    pets._pets.append(extra)
    assert pets._pet_sleep_spot_for(first) != pets._pet_sleep_spot_for(extra)
    pets._pets.remove(extra)
    assert pets._pet_sleep_spot_for(first) == spot


def test_sleep_arrival_stays_exact_and_retargets(pets):
    pets.paused = True
    pets._pet_work_rect = lambda *_: (0, 0, 1920, 1080)
    pet = _fake_pet(pets)
    pets._pets = [pet]
    target = pets._pet_sleep_spot_for(pet)
    pet.x, pet.y = target[0] - 2, target[1]
    for now in range(5):
        pet.tick(float(now))
        assert (pet.x, pet.y) == target
        assert pet.sleeping
        pet.label.config.assert_called_with(image=pet.photos["sleep"])
        pet.window.geometry.assert_called_with(f"+{int(target[0])}+{int(target[1])}")
    pets.x += 100
    pet.tick(10.0)
    assert not pet.sleeping
    assert pet.x > target[0]


def test_pet_resumes_if_woken_before_arrival(pets):
    pet = _fake_pet(pets)
    pet.state = PET_STATE_SLEEP
    pet.tick(1000.0)
    assert pet.state == PET_STATE_FOLLOW
    assert not pet.sleeping


def test_pet_sleep_walk_can_hurry(pets):
    pets.paused = True
    pets._pet_work_rect = lambda *_: (0, 0, 1920, 1080)
    pet = _fake_pet(pets)
    pets._pets = [pet]
    pet.x, pet.y = 0.0, 0.0  # far from the sleep spot
    with patch("kinito.features.pets.random.random", return_value=0.0):
        pet.tick(1000.0)
    assert pet.hurry_until > 1000.0
    assert math.hypot(pet.x - 0.0, pet.y - 0.0) > pets.PET_SPEED_PX


def test_pet_tick_sleep_when_kinito_paused(pets):
    pets.paused = True
    pet = _fake_pet(pets)
    pet.orbit_angle = 0.0  # sleep spot lands on +70 offset
    pet.x, pet.y = pets._pet_sleep_spot_for(pet)
    pet.tick(1000.0)
    assert pet.state == PET_STATE_SLEEP
    assert pet.sleeping is True


def test_pet_tick_wakes_after_pause(pets):
    pet = _fake_pet(pets)
    pet.sleeping = True
    pet.state = PET_STATE_SLEEP
    pet.idle_until = 99999.0
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


def test_pet_tick_far_wander_keeps_walking_when_recently_away(pets):
    """Distance alone must not recall the pet mid-walk."""
    pet = _fake_pet(pets)
    pet.state = "wander"
    pet.x, pet.y = pets.x + 1500.0, pets.y
    pet.target = (pets.x + 1800.0, pets.y)
    pet.away_since = 990.0
    pet.tick(1000.0)
    assert pet.state == "wander"
    assert pet.x > pets.x + 1500.0


def test_pet_tick_wander_arrival_rests_in_place(pets):
    pet = _fake_pet(pets)
    pet.state = "wander"
    pet.x, pet.y = pets.x + 800.0, pets.y
    pet.target = (pet.x + 5.0, pet.y)
    pet.away_since = 900.0
    pet.tick(1000.0)
    assert pet.state == PET_STATE_REST
    assert pet.rest_until >= 1000.0 + pets.PET_REST_SECONDS[0]
    assert pet.rest_until <= 1000.0 + pets.PET_REST_SECONDS[1]


def test_pet_tick_rest_stays_then_returns(pets):
    pet = _fake_pet(pets)
    pet.state = PET_STATE_REST
    pet.x, pet.y = pets.x + 800.0, pets.y
    pet.rest_until = 1100.0
    pet.away_since = 900.0
    pet.tick(1000.0)
    assert pet.state == PET_STATE_REST
    assert pet.x == pets.x + 800.0  # rests in place, does not walk back
    pet.tick(1100.0)
    assert pet.state == PET_STATE_FOLLOW


def test_pet_mouse_follow_rests_on_approach_side(pets):
    """A pet arriving from the left rests left of the cursor."""
    pets._pet_cursor_point = lambda: (1000.0, 500.0)
    pet = _fake_pet(pets)  # 60x50 sprite -> center offsets 30/25
    pet.state = "mouse"
    pet.mouse_until = 2000.0
    pet.x, pet.y = 700.0, 475.0  # approaching from the left
    pet.tick(1000.0)
    assert pet.target is not None
    tx, ty = pet.target
    center_x = tx + 30.0
    center_y = ty + 25.0
    assert center_x < 1000.0
    dist = ((center_x - 1000.0) ** 2 + (center_y - 500.0) ** 2) ** 0.5
    assert dist == pytest.approx(pets.PET_MOUSE_REST_OFFSET, abs=0.5)


def test_pet_mouse_follow_rests_below_when_from_below(pets):
    pets._pet_cursor_point = lambda: (1000.0, 500.0)
    pet = _fake_pet(pets)
    pet.state = "mouse"
    pet.mouse_until = 2000.0
    pet.x, pet.y = 970.0, 700.0  # approaching from below
    pet.tick(1000.0)
    tx, ty = pet.target
    assert ty + 25.0 > 500.0


def test_spawn_pet_avoids_overlapping_existing(pets):
    pets._pets_max_count = 3
    pets._pets.append(_fake_pet(pets))
    calls = []

    def _overlap(x, y, w, h, *, skip=None):
        calls.append((x, y))
        return len(calls) < 2  # first candidate overlaps, second is free

    pets._pet_box_overlaps = MagicMock(side_effect=_overlap)
    pets._pet_clamp_point = lambda x, y: (x, y)
    photos_patch, create_patch = _patched_spawn(pets)
    with photos_patch, create_patch:
        assert pets.spawn_pet() is True
    new_pet = pets._pets[1]
    assert (new_pet.x, new_pet.y) == calls[1]
    assert pets._pet_box_overlaps.call_count == 2


def test_separation_pass_splits_resting_overlap(pets):
    pets._pet_work_rect = lambda *_: (0, 0, 1920, 1080)
    pets.x, pets.y = 500, 470  # anchor lands at (590, 500) for orbit 0
    a = _fake_pet(pets)
    b = _fake_pet(pets)
    a.orbit_angle = b.orbit_angle = 0.0
    a.x, a.y = 590.0, 500.0  # 60x50 sprites, settled at the anchor
    b.x, b.y = 610.0, 510.0  # overlapping a, also settled
    pets._pets = [a, b]
    with patch("kinito.features.pets.random.random", return_value=1.0):
        pets._pets_tick()
    assert b.x >= a.x + 60 or b.x + 60 <= a.x or b.y >= a.y + 50 or b.y + 50 <= a.y


def test_separation_pass_keeps_pet_at_its_anchor(pets):
    """The pet already home stays; the blocker gets pushed aside instead."""
    pets._pet_work_rect = lambda *_: (0, 0, 1920, 1080)
    pets.x, pets.y = 500, 400
    home = _fake_pet(pets)
    blocker = _fake_pet(pets)
    home.orbit_angle = 0.0             # anchor (590, 430)
    blocker.orbit_angle = math.pi      # anchor (410, 430) — far away
    home.x, home.y = 590.0, 430.0      # exactly on its anchor
    blocker.x, blocker.y = 600.0, 435.0  # slightly overlapping, off-anchor
    blocker.state = PET_STATE_REST
    blocker.rest_until = time.monotonic() + 1000.0
    pets._pets = [home, blocker]
    with patch("kinito.features.pets.random.random", return_value=1.0):
        pets._pets_tick()
    assert (home.x, home.y) == (590.0, 430.0)
    assert blocker.x >= home.x + 60 or blocker.x + 60 <= home.x


def test_separation_pass_no_pingpong_when_boxed_in(pets):
    """A pet squeezed between neighbors on both sides is left alone."""
    pets._pet_work_rect = lambda *_: (0, 0, 1920, 1080)
    pets._pets = [_fake_pet(pets) for _ in range(4)]
    # Chain of resting 60px pets: [410][480] mid(535) [590] — mid overlaps both
    # inner neighbors and every escape side is taken as well.
    positions = (410.0, 480.0, 535.0, 590.0)
    for pet, x in zip(pets._pets, positions, strict=True):
        pet.state = PET_STATE_REST
        pet.rest_until = time.monotonic() + 1000.0
        pet.x, pet.y = x, 430.0
    mid = pets._pets[2]
    xs = [mid.x]
    for _ in range(4):
        pets._pets_tick()
        xs.append(mid.x)
    # No oscillation: once moved (or not), the position must stay stable.
    assert xs[-1] == xs[-2] == xs[-3]


def test_separation_pass_leaves_movers_alone(pets):
    pets._pet_work_rect = lambda *_: (0, 0, 1920, 1080)
    a = _fake_pet(pets)
    b = _fake_pet(pets)
    a.x, a.y = 500.0, 500.0
    b.x, b.y = 520.0, 510.0
    b.state = "wander"
    b.target = (1500.0, 510.0)  # mid-transit, may pass over a
    pets._pets = [a, b]
    pets._pets_tick()
    assert b.x > 520.0  # kept walking, was not pushed aside


def test_pet_follow_can_hurry_with_bigger_steps(pets):
    pets.x, pets.y = 1000, 500
    pet = _fake_pet(pets)
    pet.orbit_angle = 0.0  # anchor at (1090, 530)
    pet.x, pet.y = 500.0, 500.0  # far away -> follow triggers
    with patch("kinito.features.pets.random.random", return_value=0.0):
        pet.tick(1000.0)
    assert pet.hurry_until > 1000.0
    first_step = pet.x - 500.0
    assert first_step > pets.PET_SPEED_PX  # hurried pets cover more ground


def test_pet_follow_normal_speed_without_hurry(pets):
    pets.x, pets.y = 1000, 500
    pet = _fake_pet(pets)
    pet.orbit_angle = 0.0
    pet.x, pet.y = 500.0, 500.0
    with patch("kinito.features.pets.random.random", return_value=1.0):
        pet.tick(1000.0)
    assert pet.hurry_until == 0.0
    assert pet.x - 500.0 <= pets.PET_SPEED_PX + 0.01


def test_pet_circle_stroll_returns_without_rest(pets):
    pets.x, pets.y = 500, 400
    pet = _fake_pet(pets)
    pet.orbit_angle = 0.0  # anchor (590, 430)
    pet.x, pet.y = 590.0, 430.0
    roll = pets.PET_WANDER_CHANCE + pets.PET_CIRCLE_CHANCE / 2
    with patch("kinito.features.pets.random.random", return_value=roll):
        pet.tick(1000.0)
    assert pet.state == "wander"
    assert pet.rest_after_wander is False
    # Arriving at the orbit spot returns to follow, not a long rest.
    pet.x, pet.y = pet.target
    pet.tick(1001.0)
    assert pet.state == PET_STATE_FOLLOW


def test_pet_idle_hop_chance_starts_hopping(pets):
    pets.x, pets.y = 500, 400
    pet = _fake_pet(pets)
    pet.orbit_angle = 0.0
    pet.x, pet.y = 590.0, 430.0
    roll = (
        pets.PET_WANDER_CHANCE
        + pets.PET_CIRCLE_CHANCE
        + pets.PET_MOUSE_CHANCE
        + pets.PET_IDLE_HOP_CHANCE / 2
    )
    with patch("kinito.features.pets.random.random", return_value=roll):
        pet.tick(1000.0)
    assert pet.idle_hop_until > 1000.0
    assert pet.state == PET_STATE_FOLLOW


def test_pet_wander_can_hurry(pets):
    pets.x, pets.y = 1000, 500
    pet = _fake_pet(pets)
    pet.state = "wander"
    pet.x, pet.y = 500.0, 500.0
    pet.target = (1500.0, 500.0)
    pet.away_since = 999.0
    with patch("kinito.features.pets.random.random", return_value=0.0):
        pet.tick(1000.0)
    assert pet.hurry_until > 1000.0
    assert pet.x - 500.0 > pets.PET_SPEED_PX


def test_social_chase_assigns_chaser_and_fleer(pets):
    pets._pets = [_fake_pet(pets, "jade"), _fake_pet(pets, "sam")]
    with patch(
        "kinito.features.pets.random.choice",
        side_effect=[pets._pets[1], "chase"],
    ):
        assert pets._pet_try_social(pets._pets[0]) is True
    assert pets._pets[0].social["kind"] == "chase"
    assert pets._pets[1].social["kind"] == "flee"
    assert pets._pets[1].social["partner"] is pets._pets[0]


def test_social_chase_group_all_chase_fleer(pets):
    pets._pets = [_fake_pet(pets) for _ in range(3)]
    fleer = pets._pets[2]
    with patch(
        "kinito.features.pets.random.choice",
        side_effect=[fleer, "chase"],
    ):
        assert pets._pet_try_social(pets._pets[0]) is True
    assert fleer.social["kind"] == "flee"
    assert pets._pets[0].social["kind"] == "chase"
    assert pets._pets[1].social["kind"] == "chase"
    assert fleer.social["chasers"] == [pets._pets[0], pets._pets[1]]


def test_social_orbit_all_circle_kinito(pets):
    pets._pets = [_fake_pet(pets) for _ in range(3)]
    pets._buddy_center = lambda: (500.0, 400.0)
    with patch(
        "kinito.features.pets.random.choice",
        side_effect=[pets._pets[1], "orbit"],
    ):
        assert pets._pet_try_social(pets._pets[0]) is True
    assert all(p.social and p.social["kind"] == "orbit" for p in pets._pets)
    angles = [p.social["angle"] for p in pets._pets]
    assert angles[0] == 0.0 and angles[1] == pytest.approx(math.tau / 3)


def test_social_orbit_moves_pet_around_kinito(pets):
    a = _fake_pet(pets)
    a.x, a.y = 500.0, 300.0  # above the orbit point
    a.social = {
        "kind": "orbit",
        "point": (500.0, 400.0),
        "angle": 0.0,
        "until": 2000.0,
    }
    a.tick(1000.0)
    assert a.x > 500.0  # heading right along the ring


def test_social_together_rests_at_destination(pets):
    a = _fake_pet(pets)
    a.x, a.y = 300.0, 300.0
    a.social = {
        "kind": "together",
        "point": (300.0, 300.0),  # already there
        "until": 2000.0,
    }
    a.tick(1000.0)
    assert a.social is None
    assert a.state == "rest"
    assert a.rest_until > 1000.0


def test_social_piggy_assigns_throwers_and_middle(pets):
    pets._pets = [_fake_pet(pets) for _ in range(3)]
    piggy = pets._pets[1]
    with patch(
        "kinito.features.pets.random.choice",
        side_effect=[piggy, "piggy"],
    ):
        assert pets._pet_try_social(pets._pets[0]) is True
    assert piggy.social["kind"] == "piggy_mid"
    throwers = [pets._pets[0], pets._pets[2]]
    assert piggy.social["throwers"] == throwers
    assert piggy.social["active"] is pets._pets[0]
    assert all(t.social["kind"] == "piggy_throw" for t in throwers)
    assert all(t.social["piggy"] is piggy for t in throwers)


def test_social_piggy_shove_sends_middle_to_other_thrower(pets):
    a, b = _fake_pet(pets), _fake_pet(pets)
    piggy = _fake_pet(pets)
    a.x, a.y = 100.0, 200.0
    piggy.x, piggy.y = 140.0, 200.0  # within shove range of a
    b.x, b.y = 400.0, 200.0
    piggy.social = {
        "kind": "piggy_mid",
        "throwers": [a, b],
        "active": a,
        "until": 2000.0,
    }
    a.social = {"kind": "piggy_throw", "piggy": piggy, "until": 2000.0}
    a.tick(1000.0)
    assert piggy.social["kind"] == "piggy_fly"
    assert piggy.social["active"] is b
    tx, ty = piggy.social["target"]
    assert tx < b.x  # lands short of b
    piggy.tick(1000.1)
    assert piggy.x > 140.0  # flying toward b


def test_social_chaser_moves_toward_partner(pets):
    a, b = _fake_pet(pets), _fake_pet(pets)
    a.x, a.y = 0.0, 0.0
    b.x, b.y = 300.0, 0.0
    a.social = {"kind": "chase", "partner": b, "until": 2000.0}
    a.tick(1000.0)
    assert a.x > 0.0  # ran after b


def test_social_fleer_moves_away_from_partner(pets):
    a, b = _fake_pet(pets), _fake_pet(pets)
    a.x, a.y = 100.0, 0.0  # chaser close by
    b.x, b.y = 120.0, 0.0
    b.social = {"kind": "flee", "partner": a, "until": 2000.0}
    b.tick(1000.0)
    assert b.target is not None and b.target[0] > b.x


def test_social_visit_arrives_and_finishes(pets):
    a, b = _fake_pet(pets), _fake_pet(pets)
    b.x, b.y = 300.0, 300.0
    a.x, a.y = b.x + 50.0, b.y  # already next to b
    a.social = {"kind": "visit", "partner": b, "until": 2000.0}
    a.tick(1000.0)
    assert a.social is None  # interaction done -> back to normal
    assert a.idle_hop_until > 1000.0


def test_social_push_shoves_partner(pets):
    a, b = _fake_pet(pets), _fake_pet(pets)
    a.x, a.y = 300.0, 300.0
    b.x, b.y = a.x + 40.0, a.y
    a.social = {"kind": "push", "partner": b, "until": 2000.0}
    a.tick(1000.0)
    assert a.social is None
    assert b.social is not None and b.social["kind"] == "shoved"
    assert b.social["dir"][0] > 0  # shoved away from the pusher


def test_social_together_includes_all_free_pets(pets):
    pets._pets = [_fake_pet(pets) for _ in range(3)]
    pets._pet_virtual_rect = lambda: (0, 0, 1920, 1080)
    pets._pet_work_rect = lambda *_: (0, 0, 1920, 1080)
    with patch(
        "kinito.features.pets.random.choice",
        side_effect=[pets._pets[1], "together"],
    ):
        assert pets._pet_try_social(pets._pets[0]) is True
    assert all(p.social and p.social["kind"] == "together" for p in pets._pets)


def test_social_together_pets_travel_to_points(pets):
    a = _fake_pet(pets)
    a.x, a.y = 0.0, 0.0
    a.social = {"kind": "together", "point": (500.0, 0.0), "until": 2000.0}
    a.tick(1000.0)
    assert a.x > 0.0


def test_pet_tick_dances_to_music(pets):
    pets._is_background_music_playing.return_value = True
    pet = _fake_pet(pets)
    pet.state = PET_STATE_DANCE
    pet.dance_until = 2000.0
    pet.tick(1000.0)
    pet.window.geometry.assert_called()


def test_pets_tick_pushes_pet_above_taskbar(pets):
    """A pet that slipped under the work area is pushed back up each tick."""
    pets._pet_work_rect = lambda *_: (0, 0, 1920, 1030)
    pets.x, pets.y = 500, 1000
    pet = _fake_pet(pets)
    pet.idle_until = 99999.0
    pet.orbit_angle = 0.0  # anchor (590, 1030) -> pet stays settled
    pet.x, pet.y = 590.0, 1060.0  # resting inside the taskbar strip
    pets._pets = [pet]
    for _ in range(60):
        pets._pets_tick()  # walks up to its clamped anchor, then stays
    assert pet.y <= 1030 - 20 - 60  # work-area bottom minus margin and size
    pet.window.geometry.assert_called()


def test_pets_tick_does_not_clamp_moving_pet(pets):
    """A pet walking to another monitor must not be trapped at the edge."""
    pets._pet_work_rect = lambda *_: (0, 0, 1920, 1030)
    pet = _fake_pet(pets)
    pet.state = "wander"
    pet.x, pet.y = 1910.0, 500.0
    pet.target = (2200.0, 500.0)  # heading onto a second monitor
    pets._pets = [pet]
    pets._pets_tick()
    assert pet.x > 1910.0  # kept moving right, not pushed back


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


def test_stop_pets_hops_briefly_then_destroys(pets):
    pet = _fake_pet(pets)
    pet.sleeping = True
    pets._pets.append(pet)
    pets._stop_pets()
    assert not pet.destroyed
    assert pet.state == PET_STATE_HOPOUT
    assert not pet.sleeping
    remaining = pet.hop_until - time.monotonic()
    assert 0 <= remaining <= pets.PET_HOPOUT_SECONDS[1]
    pet.tick(pet.hop_until - 0.5)
    assert not pet.destroyed
    pet.tick(pet.hop_until + 0.01)
    assert pet.destroyed


def test_stop_pets_without_pets_cancels_tick(pets):
    pets._pet_tick_timer = "timer-id"
    pets._stop_pets()
    pets.root.after_cancel.assert_called_once_with("timer-id")


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
