"""Tests for Kinito's mood system."""

from __future__ import annotations

import random
import time
from unittest.mock import MagicMock

from content import dialogue as dlg
from content import llm_prompts as prompts
from content.memory_keys import ALLOWED_FACT_KEYS, EXTRA_FACT_KEYS, PROTECTED_FACT_KEYS
from content.mood_lines import (
    DECLINED_BY_MOOD,
    HUG_BY_MOOD,
    IDLE_SNIPPETS_BY_MOOD,
    STATUS_BY_MOOD,
)
from kinito.features.mood import (
    GAME_KINITO_WIN,
    GAME_PLAYER_WIN,
    KINITO_MOOD_FACT_KEY,
    MOOD_ANGRY,
    MOOD_ANNOYED,
    MOOD_BORED,
    MOOD_HAPPY,
    MOOD_NEUTRAL,
    MOOD_SAD,
    MOOD_TIRED,
    MoodMixin,
    blend_action_weights,
    clamp_intensity,
    format_mood_fact,
    parse_mood_fact,
)
from kinito.memory.store import MemoryStore
from kinito.settings_store import DEFAULT_BOOL_SETTINGS


class _MoodHost(MoodMixin):
    def __init__(self, memory=None):
        self._memory = memory
        self._init_mood()


def test_kinito_mood_fact_is_allowed_and_protected():
    assert KINITO_MOOD_FACT_KEY in EXTRA_FACT_KEYS
    assert KINITO_MOOD_FACT_KEY in ALLOWED_FACT_KEYS
    assert KINITO_MOOD_FACT_KEY in PROTECTED_FACT_KEYS


def test_clamp_and_parse_mood_fact():
    assert clamp_intensity(2) == 1.0
    assert clamp_intensity(-1) == 0.0
    raw = format_mood_fact(MOOD_TIRED, 0.7, timestamp=1_700_000_000)
    parsed = parse_mood_fact(raw)
    assert parsed is not None
    mood, intensity, ts = parsed
    assert mood == MOOD_TIRED
    assert abs(intensity - 0.7) < 0.001
    assert ts == 1_700_000_000
    assert parse_mood_fact("nope") is None


def test_blend_weights_tired_prefers_nap():
    tired = blend_action_weights(MOOD_TIRED, 1.0)
    neutral = blend_action_weights(MOOD_NEUTRAL, 0.0)
    assert tired["nap"] > neutral["nap"]
    assert tired["games"] < neutral["games"]
    assert tired["speech_chance_mult"] < 1.0


def test_blend_weights_bored_prefers_play():
    bored = blend_action_weights(MOOD_BORED, 1.0)
    neutral = blend_action_weights(MOOD_NEUTRAL, 0.0)
    assert bored["games"] > neutral["games"]
    assert bored["browser"] > neutral["browser"]
    assert bored["window_grab_mult"] > neutral["window_grab_mult"]
    assert bored["nudge_mult"] > neutral["nudge_mult"]


def test_blend_weights_annoyed_reduces_nudges():
    annoyed = blend_action_weights(MOOD_ANNOYED, 1.0)
    neutral = blend_action_weights(MOOD_NEUTRAL, 0.0)
    assert annoyed["nudge_mult"] < neutral["nudge_mult"]
    assert annoyed["games"] < neutral["games"]


def test_shift_mood_does_not_hard_reset():
    host = _MoodHost()
    host.set_mood(MOOD_SAD, 0.8)
    host.soften_mood(0.2)
    assert host.get_mood() in {MOOD_SAD, MOOD_NEUTRAL, MOOD_HAPPY}
    # Soften should not wipe intensity to a brand-new full happy every time.
    if host.get_mood() == MOOD_SAD:
        assert host.get_mood_intensity() < 0.8


def test_hug_accepted_softens_sad():
    host = _MoodHost()
    host.set_mood(MOOD_SAD, 0.7)
    random.seed(0)
    host.on_hug_accepted()
    assert host.get_mood() in {MOOD_SAD, MOOD_NEUTRAL, MOOD_HAPPY}


def test_hug_declined_can_sour_mood():
    host = _MoodHost()
    host.set_mood(MOOD_NEUTRAL, 0.0)
    random.seed(1)
    # Run a few times; at least one decline should move off neutral with this seed space.
    changed = False
    for seed in range(20):
        host.set_mood(MOOD_NEUTRAL, 0.0)
        random.seed(seed)
        host.on_hug_declined()
        if host.get_mood() in {MOOD_SAD, MOOD_ANNOYED}:
            changed = True
            break
    assert changed


def test_wake_from_tired_often_improves():
    host = _MoodHost()
    host.set_mood(MOOD_TIRED, 0.8)
    host._mood_sleep_started_as = MOOD_TIRED
    random.seed(2)
    host.on_wake(spontaneous=True)
    # Should not jump to angry; tired wake tends to soften.
    assert host.get_mood() != MOOD_ANGRY


def test_wake_from_bored_may_stay_or_annoy():
    host = _MoodHost()
    host.set_mood(MOOD_BORED, 0.7)
    host._mood_sleep_started_as = MOOD_BORED
    random.seed(3)
    before = host.get_mood()
    host.on_wake(spontaneous=True)
    assert host.get_mood() in {MOOD_BORED, MOOD_ANNOYED, MOOD_NEUTRAL, before}


def test_mood_tone_hint_mentions_mood():
    host = _MoodHost()
    host.set_mood(MOOD_ANNOYED, 0.9)
    hint = host.mood_tone_hint()
    assert "annoyed" in hint.lower()
    assert prompts.append_mood_context("Hello.", hint).endswith(hint)


def test_speak_current_mood_uses_status_pool():
    host = _MoodHost()
    host.set_mood(MOOD_BORED, 0.8)
    host.speak = MagicMock()
    host.speak_current_mood()
    host.speak.assert_called_once()
    spoken = host.speak.call_args.args[0]
    assert spoken in STATUS_BY_MOOD["bored"]
    assert "bored" in host.speak.call_args.kwargs["ai_hint"].lower()


def test_pick_line_for_mood_can_use_mood_pool():
    mood_lines = HUG_BY_MOOD["sad"]
    random.seed(0)
    # High intensity should often prefer mood lines.
    picks = {
        dlg.pick_line_for_mood(
            ["generic hug"],
            mood=MOOD_SAD,
            intensity=1.0,
            mood_lines=mood_lines,
        )
        for _ in range(30)
    }
    assert picks & set(mood_lines)


def test_pick_declined_line_annoyed():
    random.seed(0)
    picks = {
        dlg.pick_declined_line(["specific no"], mood=MOOD_ANNOYED, intensity=1.0)
        for _ in range(40)
    }
    assert picks & set(DECLINED_BY_MOOD["annoyed"])


def test_persist_and_load_mood(tmp_path):
    store = MemoryStore(directory=str(tmp_path))
    host = _MoodHost(memory=store)
    host.set_mood(MOOD_HAPPY, 0.6)
    assert store.get_fact(KINITO_MOOD_FACT_KEY)
    host2 = _MoodHost(memory=store)
    assert host2.get_mood() == MOOD_HAPPY
    assert host2.get_mood_intensity() >= 0.2


def test_stale_mood_decays_to_neutral(tmp_path):
    store = MemoryStore(directory=str(tmp_path))
    old_ts = time.time() - (6 * 3600)
    store.set_fact(KINITO_MOOD_FACT_KEY, format_mood_fact(MOOD_ANGRY, 0.9, timestamp=old_ts))
    host = _MoodHost(memory=store)
    assert host.get_mood() == MOOD_NEUTRAL


def test_drift_can_leave_neutral():
    host = _MoodHost()
    host.set_mood(MOOD_NEUTRAL, 0.0)
    left = False
    for seed in range(80):
        host.set_mood(MOOD_NEUTRAL, 0.0)
        host._mood_idle_ticks = 1  # next tick triggers drift check
        host.maybe_drift_mood(rng=random.Random(seed))
        if host.get_mood() != MOOD_NEUTRAL:
            left = True
            break
    assert left


def test_floating_assistant_includes_mood_mixin():
    from kinito.app import FloatingAssistant

    assert issubclass(FloatingAssistant, MoodMixin)
    assert hasattr(FloatingAssistant, "mood_action_weights")
    assert hasattr(FloatingAssistant, "on_hug_accepted")


def test_on_game_outcome_player_win_sours_mood():
    host = _MoodHost()
    host.set_mood(MOOD_NEUTRAL, 0.0)
    random.seed(0)
    host.on_game_outcome(GAME_PLAYER_WIN)
    assert host.get_mood() in {MOOD_ANNOYED, MOOD_SAD}


def test_on_game_outcome_kinito_win_can_happy():
    host = _MoodHost()
    host.set_mood(MOOD_NEUTRAL, 0.0)
    random.seed(0)
    host.on_game_outcome(GAME_KINITO_WIN)
    assert host.get_mood() in {MOOD_HAPPY, MOOD_NEUTRAL}


def test_on_throw_escalates_with_streak():
    host = _MoodHost()
    host.set_mood(MOOD_NEUTRAL, 0.0)
    random.seed(0)
    host.on_throw()
    first = host.get_mood()
    assert first in {MOOD_ANNOYED, MOOD_SAD}
    host.on_throw()
    host.on_throw()
    assert host.get_mood() == MOOD_ANGRY


def test_neglect_shifts_when_ignored():
    host = _MoodHost()
    host.set_mood(MOOD_NEUTRAL, 0.0)
    host.paused = False
    host._focus_mode = False
    host._is_game_active = lambda: False
    host._is_busy_with_speech = lambda: False
    host._last_user_attention_at = time.monotonic() - (host.MOOD_NEGLECT_SECONDS + 1)
    host._last_neglect_mood_at = 0.0
    random.seed(0)
    host.maybe_neglect_mood(rng=random.Random(0))
    assert host.get_mood() in {MOOD_BORED, MOOD_SAD}


def test_mood_system_toggle_disables_shifts():
    host = _MoodHost()
    host.speak = MagicMock()
    host._persist_settings = MagicMock()
    host.set_mood(MOOD_HAPPY, 0.8)
    host.toggle_mood_system()
    assert host.is_mood_system_enabled() is False
    assert host.get_mood() == MOOD_NEUTRAL
    host.on_game_outcome(GAME_PLAYER_WIN)
    assert host.get_mood() == MOOD_NEUTRAL
    weights = host.mood_action_weights()
    assert abs(weights["games"] - 1.0) < 0.001


def test_reset_mood_sets_neutral():
    host = _MoodHost()
    host.speak = MagicMock()
    host.set_mood(MOOD_ANGRY, 0.9)
    host.reset_mood()
    assert host.get_mood() == MOOD_NEUTRAL
    assert host.get_mood_intensity() == 0.0
    host.speak.assert_called_once()


def test_idle_snippets_have_depth_per_mood():
    for mood, lines in IDLE_SNIPPETS_BY_MOOD.items():
        assert len(lines) >= 6, mood


def test_mood_system_setting_default_exists():
    assert DEFAULT_BOOL_SETTINGS["mood_system_enabled"] is True
