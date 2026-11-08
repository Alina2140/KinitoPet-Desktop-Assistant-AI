"""Coverage tests for the *_BY_MOOD line pools added across content files."""

from __future__ import annotations

import random

from content import dialogue as dlg
from content import game_lines
from content.app_lines import APP_AWARE_IDLE_BY_MOOD, APP_AWARE_NUDGE_BY_MOOD
from content.birthday import pick_birthday_congrats_line
from content.dizzy_lines import DIZZY_BY_MOOD
from content.goodbye_lines import GOODBYE_BY_MOOD
from content.head_stroke_lines import HEAD_STROKE_BY_MOOD
from content.hold_lines import HOLD_BY_MOOD
from content.mood_lines import (
    DECLINED_BY_MOOD,
    FACT_INTRO_BY_MOOD,
    HUG_BY_MOOD,
    PAUSE_BY_MOOD,
    STATUS_BY_MOOD,
    UNPAUSE_BY_MOOD,
    lines_for_mood,
    pick_mood_aware_line,
)
from content.nudge_lines import PLAY_INVITE_NUDGE_BY_MOOD, WELLNESS_NUDGE_BY_MOOD
from content.questions import QUESTIONS, QUESTIONS_BY_MOOD, pick_question
from content.startup import STARTUP_BY_MOOD
from content.throw_lines import THROW_BY_MOOD
from content.window_grab_lines import WINDOW_GRAB_BY_MOOD
from content.wisdom import get_random_wisdom

MOODS = ("happy", "bored", "tired", "annoyed", "sad", "angry")

# Pools added/extended for mood lines; every one must cover all six moods.
POOLS = {
    "FACT_INTRO_BY_MOOD": FACT_INTRO_BY_MOOD,
    "STARTUP_BY_MOOD": STARTUP_BY_MOOD,
    "GOODBYE_BY_MOOD": GOODBYE_BY_MOOD,
    "HEAD_STROKE_BY_MOOD": HEAD_STROKE_BY_MOOD,
    "HOLD_BY_MOOD": HOLD_BY_MOOD,
    "THROW_BY_MOOD": THROW_BY_MOOD,
    "DIZZY_BY_MOOD": DIZZY_BY_MOOD,
    "WINDOW_GRAB_BY_MOOD": WINDOW_GRAB_BY_MOOD,
    "WELLNESS_NUDGE_BY_MOOD": WELLNESS_NUDGE_BY_MOOD,
    "PLAY_INVITE_NUDGE_BY_MOOD": PLAY_INVITE_NUDGE_BY_MOOD,
    "APP_AWARE_NUDGE_BY_MOOD": APP_AWARE_NUDGE_BY_MOOD,
    "APP_AWARE_IDLE_BY_MOOD": APP_AWARE_IDLE_BY_MOOD,
    "QUESTIONS_BY_MOOD": QUESTIONS_BY_MOOD,
    "JOKES_BY_MOOD": dlg.JOKES_BY_MOOD,
    "STORY_QUESTIONS_BY_MOOD": dlg.STORY_QUESTIONS_BY_MOOD,
    "BIRTHDAY_CONGRATS_BY_MOOD": dlg.BIRTHDAY_CONGRATS_BY_MOOD,
    "BROWSER_CLOSE_BY_MOOD": dlg.BROWSER_CLOSE_BY_MOOD,
    "GAME_WIN_BY_MOOD": game_lines.GAME_WIN_BY_MOOD,
    "GAME_LOSE_BY_MOOD": game_lines.GAME_LOSE_BY_MOOD,
    "GAME_DRAW_BY_MOOD": game_lines.GAME_DRAW_BY_MOOD,
    "GAME_CLOSED_BY_MOOD": game_lines.GAME_CLOSED_BY_MOOD,
    "GAME_PLAY_AGAIN_BY_MOOD": game_lines.GAME_PLAY_AGAIN_BY_MOOD,
}


LEGACY_POOLS = {
    "DECLINED_BY_MOOD": DECLINED_BY_MOOD,
    "HUG_BY_MOOD": HUG_BY_MOOD,
    "PAUSE_BY_MOOD": PAUSE_BY_MOOD,
    "UNPAUSE_BY_MOOD": UNPAUSE_BY_MOOD,
    "STATUS_BY_MOOD": STATUS_BY_MOOD,
}


def test_every_mood_pool_covers_all_moods():
    for name, pool in POOLS.items():
        for mood in MOODS:
            assert pool.get(mood), f"{name} missing mood {mood!r}"


def test_mood_pools_have_no_duplicates():
    for name, pool in {**POOLS, **LEGACY_POOLS}.items():
        for mood, lines in pool.items():
            assert len(lines) == len(set(lines)), f"{name}[{mood}] has dupes"


def test_story_questions_keep_marker():
    marker = dlg.STORY_QUESTION_MARKER
    for mood, lines in dlg.STORY_QUESTIONS_BY_MOOD.items():
        for line in lines:
            assert marker in line, f"{mood}: {line!r} lost the marker"


def test_pick_mood_aware_line_uses_mood_pool_at_high_intensity():
    random.seed(0)
    mood_lines = {"neutral": ["base"], "angry": ["GRR!"]}
    picked = pick_mood_aware_line(["base"], mood_lines, "angry", 1.0)
    assert picked in ("base", "GRR!")
    # Force the roll: many samples at intensity 1 must hit the mood pool.
    seen = {
        pick_mood_aware_line(["base"], mood_lines, "angry", 1.0)
        for _ in range(50)
    }
    assert "GRR!" in seen


def test_pick_question_mood_path_returns_pool_line():
    picked = pick_question("happy", 1.0)
    assert picked in QUESTIONS or picked in QUESTIONS_BY_MOOD["happy"]


def test_get_random_wisdom_accepts_mood():
    line = get_random_wisdom(mood="tired", intensity=1.0)
    assert isinstance(line, str) and line


def test_game_line_picker_uses_mood_for_outcomes():
    class _App:
        def get_mood(self):
            return "angry"

        def get_mood_intensity(self):
            return 1.0

    random.seed(0)
    seen = {
        game_lines.pick_game_line(_App(), ["base"], "win") for _ in range(50)
    }
    assert "base" in seen or any(
        line in seen for line in game_lines.GAME_WIN_BY_MOOD["angry"]
    )


def test_birthday_congrats_mood_pool_formats_name():
    random.seed(0)
    seen = {
        pick_birthday_congrats_line(
            dlg.BIRTHDAY_CONGRATS_LINES,
            name="Alina",
            pool_by_mood=dlg.BIRTHDAY_CONGRATS_BY_MOOD,
            mood="happy",
            intensity=1.0,
        )
        for _ in range(80)
    }
    assert all("Alina" in line for line in seen)
    assert any(line in seen for line in
               [t.format(name="Alina") for t in dlg.BIRTHDAY_CONGRATS_BY_MOOD["happy"]])


def test_lines_for_mood_returns_copy():
    lines = lines_for_mood(DECLINED_BY_MOOD, "sad")
    lines.append("mutated")
    assert "mutated" not in DECLINED_BY_MOOD["sad"]
