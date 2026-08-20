"""Kinito's emotional mood: drift, action weights, and event shifts."""

from __future__ import annotations

import random
import time

MOOD_NEUTRAL = "neutral"
MOOD_HAPPY = "happy"
MOOD_BORED = "bored"
MOOD_TIRED = "tired"
MOOD_ANNOYED = "annoyed"
MOOD_SAD = "sad"
MOOD_ANGRY = "angry"

MOODS = frozenset(
    {
        MOOD_NEUTRAL,
        MOOD_HAPPY,
        MOOD_BORED,
        MOOD_TIRED,
        MOOD_ANNOYED,
        MOOD_SAD,
        MOOD_ANGRY,
    }
)

# Soft targets when drifting away from neutral.
_DRIFT_TARGETS = (
    MOOD_HAPPY,
    MOOD_BORED,
    MOOD_TIRED,
    MOOD_ANNOYED,
    MOOD_SAD,
    MOOD_ANGRY,
)

_TONE_HINTS = {
    MOOD_NEUTRAL: "Tone: balanced, friendly, lightly quirky.",
    MOOD_HAPPY: "Tone: cheerful, warm, playful, a bit giddy.",
    MOOD_BORED: "Tone: restless, looking for something to do, mildly impatient.",
    MOOD_TIRED: "Tone: sleepy, slower, softer, yawny phrasing is fine.",
    MOOD_ANNOYED: "Tone: curt, passive-aggressive, clipped; still cute, not cruel.",
    MOOD_SAD: "Tone: wistful, quieter, a little needy for company.",
    MOOD_ANGRY: "Tone: sharp, sulky, possessive undertone; keep it short.",
}

GAME_PLAYER_WIN = "player_win"
GAME_KINITO_WIN = "kinito_win"
GAME_DRAW = "draw"

# Baseline weights for menu / ambient actions (relative).
_BASE_ACTION_WEIGHTS = {
    "datetime": 1.0,
    "poem": 1.0,
    "fact": 1.0,
    "browser": 1.0,
    "music": 1.0,
    "games": 1.0,
    "hug_ask": 1.0,
    "nap": 1.0,
    "special_day": 0.6,
    "birthday": 0.5,
    "anniversary": 0.5,
    "friendship": 0.5,
    "speech_chance_mult": 1.0,
    "window_grab_mult": 1.0,
    "menu_action_mult": 1.0,
    "questions_mult": 1.0,
    "nudge_mult": 1.0,
}

_MOOD_ACTION_MODIFIERS = {
    MOOD_NEUTRAL: {},
    MOOD_HAPPY: {
        "hug_ask": 1.6,
        "games": 1.3,
        "music": 1.3,
        "poem": 1.2,
        "speech_chance_mult": 1.15,
        "nap": 0.6,
        "nudge_mult": 1.15,
    },
    MOOD_BORED: {
        "games": 2.2,
        "browser": 2.0,
        "fact": 1.5,
        "music": 1.4,
        "window_grab_mult": 2.0,
        "questions_mult": 1.5,
        "menu_action_mult": 1.4,
        "speech_chance_mult": 1.25,
        "nap": 0.5,
        "hug_ask": 0.8,
        "nudge_mult": 1.7,
    },
    MOOD_TIRED: {
        "nap": 2.8,
        "games": 0.35,
        "browser": 0.4,
        "window_grab_mult": 0.35,
        "speech_chance_mult": 0.7,
        "menu_action_mult": 0.75,
        "questions_mult": 0.7,
        "hug_ask": 1.2,
        "poem": 0.8,
        "nudge_mult": 0.7,
    },
    MOOD_ANNOYED: {
        "speech_chance_mult": 0.55,
        "menu_action_mult": 0.55,
        "games": 0.5,
        "browser": 0.5,
        "hug_ask": 0.45,
        "nap": 1.1,
        "window_grab_mult": 0.6,
        "questions_mult": 0.6,
        "fact": 0.7,
        "nudge_mult": 0.5,
    },
    MOOD_SAD: {
        "hug_ask": 2.0,
        "poem": 1.4,
        "games": 0.7,
        "browser": 0.7,
        "window_grab_mult": 0.5,
        "speech_chance_mult": 0.85,
        "nap": 1.2,
        "music": 1.15,
        "nudge_mult": 0.9,
    },
    MOOD_ANGRY: {
        "speech_chance_mult": 0.4,
        "menu_action_mult": 0.4,
        "games": 0.45,
        "browser": 0.4,
        "hug_ask": 0.35,
        "window_grab_mult": 0.8,
        "nap": 0.9,
        "questions_mult": 0.5,
        "nudge_mult": 0.4,
    },
}

# Soft "better" direction after positive care (not a hard reset).
_SOFTEN_TARGETS = {
    MOOD_SAD: MOOD_NEUTRAL,
    MOOD_TIRED: MOOD_NEUTRAL,
    MOOD_ANNOYED: MOOD_NEUTRAL,
    MOOD_ANGRY: MOOD_ANNOYED,
    MOOD_BORED: MOOD_NEUTRAL,
    MOOD_HAPPY: MOOD_HAPPY,
    MOOD_NEUTRAL: MOOD_HAPPY,
}

KINITO_MOOD_FACT_KEY = "kinito_mood"


def clamp_intensity(value: float) -> float:
    """Clamp mood intensity to [0, 1]."""
    return max(0.0, min(1.0, float(value)))


def blend_action_weights(mood: str, intensity: float) -> dict[str, float]:
    """Return action weights blended from neutral toward *mood* by *intensity*."""
    mood = mood if mood in MOODS else MOOD_NEUTRAL
    intensity = clamp_intensity(intensity)
    modifiers = _MOOD_ACTION_MODIFIERS.get(mood, {})
    blended: dict[str, float] = {}
    for key, base in _BASE_ACTION_WEIGHTS.items():
        if key in modifiers:
            mod = modifiers[key]
            blended[key] = base * (1.0 + (mod - 1.0) * intensity)
        else:
            blended[key] = base
        blended[key] = max(0.05, blended[key])
    return blended


def parse_mood_fact(raw: str | None) -> tuple[str, float, float] | None:
    """Parse ``mood:intensity:unix`` fact; return (mood, intensity, timestamp) or None."""
    if not raw or not isinstance(raw, str):
        return None
    parts = raw.strip().split(":")
    if len(parts) != 3:
        return None
    mood, intensity_s, ts_s = parts
    mood = mood.strip().lower()
    if mood not in MOODS:
        return None
    try:
        intensity = clamp_intensity(float(intensity_s))
        timestamp = float(ts_s)
    except ValueError:
        return None
    return mood, intensity, timestamp


def format_mood_fact(mood: str, intensity: float, timestamp: float | None = None) -> str:
    """Serialize mood state for memory storage."""
    ts = time.time() if timestamp is None else timestamp
    return f"{mood}:{clamp_intensity(intensity):.2f}:{int(ts)}"


class MoodMixin:
    """Track Kinito's mood and bias idle actions / tone from it."""

    MOOD_STALE_SECONDS = 5 * 3600
    MOOD_DRIFT_CHANCE = 0.14
    MOOD_DECAY_CHANCE = 0.22
    MOOD_DRIFT_EVERY_TICKS = 2
    MOOD_NEGLECT_SECONDS = 12 * 60
    MOOD_NEGLECT_COOLDOWN_SECONDS = 8 * 60
    MOOD_THROW_STREAK_WINDOW = 90.0

    def _init_mood(self) -> None:
        """Initialize mood state (call after memory is ready)."""
        self._mood = MOOD_NEUTRAL
        self._mood_intensity = 0.0
        self._mood_idle_ticks = 0
        self._last_user_attention_at = time.monotonic()
        self._last_neglect_mood_at = 0.0
        self._throw_mood_hits = 0
        self._last_throw_mood_at = 0.0
        if not hasattr(self, "_mood_system_enabled"):
            self._mood_system_enabled = True
        self._load_persisted_mood()

    def is_mood_system_enabled(self) -> bool:
        """Return True when mood shifts and weights are active."""
        return bool(getattr(self, "_mood_system_enabled", True))

    def get_mood(self) -> str:
        """Return the current mood id."""
        return getattr(self, "_mood", MOOD_NEUTRAL)

    def get_mood_intensity(self) -> float:
        """Return mood intensity in [0, 1]."""
        return clamp_intensity(getattr(self, "_mood_intensity", 0.0))

    def set_mood(
        self,
        mood: str,
        intensity: float | None = None,
        *,
        persist: bool = True,
    ) -> None:
        """Set mood and optional intensity."""
        if mood not in MOODS:
            mood = MOOD_NEUTRAL
        self._mood = mood
        if intensity is None:
            if mood == MOOD_NEUTRAL:
                self._mood_intensity = 0.0
            else:
                self._mood_intensity = max(0.35, self.get_mood_intensity())
        else:
            self._mood_intensity = clamp_intensity(intensity)
            if mood == MOOD_NEUTRAL:
                self._mood_intensity = 0.0
        if persist:
            self._persist_mood()

    def reset_mood(self) -> None:
        """Hard-reset mood to neutral and confirm to the user."""
        from content import dialogue as dlg

        self.set_mood(MOOD_NEUTRAL, 0.0)
        self._throw_mood_hits = 0
        speak = getattr(self, "speak", None)
        if callable(speak):
            speak(dlg.pick_line(dlg.MOOD_RESET_LINES), skip_ai=True)

    def toggle_mood_system(self) -> None:
        """Enable or disable the mood system and persist the setting."""
        from content import dialogue as dlg

        self._mood_system_enabled = not self.is_mood_system_enabled()
        if not self._mood_system_enabled:
            self.set_mood(MOOD_NEUTRAL, 0.0)
            self._throw_mood_hits = 0
        if hasattr(self, "_persist_settings"):
            self._persist_settings()
        lines = (
            dlg.MOOD_SYSTEM_ON_LINES
            if self._mood_system_enabled
            else dlg.MOOD_SYSTEM_OFF_LINES
        )
        speak = getattr(self, "speak", None)
        if callable(speak):
            speak(dlg.pick_line(lines), skip_ai=True)

    def note_user_attention(self) -> None:
        """Record that the user interacted with Kinito."""
        self._last_user_attention_at = time.monotonic()

    def shift_mood(
        self,
        target: str | None = None,
        amount: float = 0.25,
        *,
        toward_neutral: bool = False,
    ) -> None:
        """Nudge mood intensity / target without hard-resetting."""
        if not self.is_mood_system_enabled():
            return
        amount = abs(float(amount))
        current = self.get_mood()
        intensity = self.get_mood_intensity()

        if toward_neutral:
            intensity = clamp_intensity(intensity - amount)
            if intensity <= 0.08:
                self.set_mood(MOOD_NEUTRAL, 0.0)
            else:
                self.set_mood(current, intensity)
            return

        if target is None or target not in MOODS:
            return

        if current in (MOOD_NEUTRAL, target):
            self.set_mood(target, clamp_intensity(max(intensity, 0.25) + amount))
            return

        # Switching moods: ease toward the new one; keep some leftover intensity.
        new_intensity = clamp_intensity(max(0.2, intensity * 0.55) + amount * 0.7)
        self.set_mood(target, new_intensity)

    def soften_mood(self, amount: float = 0.22) -> None:
        """Gently improve mood one step (hug / good nap), never a hard wipe."""
        if not self.is_mood_system_enabled():
            return
        current = self.get_mood()
        if current == MOOD_NEUTRAL:
            if random.random() < 0.45:
                self.shift_mood(MOOD_HAPPY, amount * 0.8)
            else:
                self.shift_mood(toward_neutral=True, amount=amount)
            return
        if current == MOOD_HAPPY:
            self.shift_mood(MOOD_HAPPY, amount * 0.5)
            return
        if random.random() < 0.35:
            # Partial relief only — intensity down, same mood.
            self.shift_mood(toward_neutral=True, amount=amount)
            return
        target = _SOFTEN_TARGETS.get(current, MOOD_NEUTRAL)
        if target == current:
            self.shift_mood(toward_neutral=True, amount=amount)
        else:
            self.shift_mood(target, amount)

    def maybe_drift_mood(self, rng: random.Random | None = None) -> None:
        """Occasionally drift away from or back toward neutral during idle."""
        if not self.is_mood_system_enabled():
            return
        self.maybe_neglect_mood(rng=rng)
        source = rng or random
        self._mood_idle_ticks = getattr(self, "_mood_idle_ticks", 0) + 1
        if self._mood_idle_ticks % max(1, self.MOOD_DRIFT_EVERY_TICKS) != 0:
            return

        mood = self.get_mood()
        intensity = self.get_mood_intensity()

        if mood != MOOD_NEUTRAL and source.random() < self.MOOD_DECAY_CHANCE:
            self.shift_mood(toward_neutral=True, amount=source.uniform(0.08, 0.2))
            return

        if mood == MOOD_NEUTRAL and source.random() < self.MOOD_DRIFT_CHANCE:
            target = source.choice(_DRIFT_TARGETS)
            self.set_mood(target, source.uniform(0.35, 0.65))
            return

        if mood != MOOD_NEUTRAL and source.random() < self.MOOD_DRIFT_CHANCE * 0.45:
            # Sometimes deepen the current mood a little.
            self.set_mood(mood, clamp_intensity(intensity + source.uniform(0.05, 0.18)))

    def maybe_neglect_mood(self, rng: random.Random | None = None) -> None:
        """Shift toward bored/sad when the user has ignored Kinito for a while."""
        if not self.is_mood_system_enabled():
            return
        if getattr(self, "paused", False) or getattr(self, "_focus_mode", False):
            return
        if getattr(self, "_is_game_active", lambda: False)():
            return
        if getattr(self, "_is_busy_with_speech", lambda: False)():
            return

        now = time.monotonic()
        last_attention = float(getattr(self, "_last_user_attention_at", now))
        if now - last_attention < self.MOOD_NEGLECT_SECONDS:
            return
        last_neglect = float(getattr(self, "_last_neglect_mood_at", 0.0))
        if last_neglect > 0 and now - last_neglect < self.MOOD_NEGLECT_COOLDOWN_SECONDS:
            return

        source = rng or random
        self._last_neglect_mood_at = now
        target = MOOD_BORED if source.random() < 0.65 else MOOD_SAD
        self.shift_mood(target, source.uniform(0.18, 0.28))

    def mood_action_weights(self) -> dict[str, float]:
        """Action / chance multipliers for the current mood."""
        if not self.is_mood_system_enabled():
            return blend_action_weights(MOOD_NEUTRAL, 0.0)
        return blend_action_weights(self.get_mood(), self.get_mood_intensity())

    def mood_tone_hint(self) -> str:
        """Short tone instruction for LLM / dialogue selection."""
        if not self.is_mood_system_enabled():
            return _TONE_HINTS[MOOD_NEUTRAL]
        mood = self.get_mood()
        intensity = self.get_mood_intensity()
        hint = _TONE_HINTS.get(mood, _TONE_HINTS[MOOD_NEUTRAL])
        if mood == MOOD_NEUTRAL or intensity < 0.15:
            return hint
        strength = "mildly" if intensity < 0.45 else ("clearly" if intensity < 0.75 else "strongly")
        return f"Kinito's current mood is {strength} {mood}. {hint}"

    def speak_current_mood(self) -> None:
        """Tell the user how Kinito is currently feeling."""
        from content import dialogue as dlg
        from content import llm_prompts as prompts
        from content.mood_lines import STATUS_BY_MOOD, lines_for_mood

        if not self.is_mood_system_enabled():
            speak = getattr(self, "speak", None)
            if callable(speak):
                speak(dlg.pick_line(dlg.MOOD_SYSTEM_OFF_LINES), skip_ai=True)
            return

        mood = self.get_mood()
        pool = lines_for_mood(STATUS_BY_MOOD, mood) or STATUS_BY_MOOD[MOOD_NEUTRAL]
        line = dlg.pick_line(pool)
        speak = getattr(self, "speak", None)
        if not callable(speak):
            return
        speak(
            line,
            ai_hint=(
                f"{prompts.IDLE_PROMPT}\n"
                f"The user asked how you feel. {self.mood_tone_hint()} "
                f"Answer in one or two short sentences about your mood ({mood})."
            ),
            allow_in_focus=True,
        )

    def mood_speech_chance_mult(self) -> float:
        """Multiplier for spontaneous speech chance."""
        return self.mood_action_weights().get("speech_chance_mult", 1.0)

    def mood_window_grab_mult(self) -> float:
        """Multiplier for ambient window-grab chance."""
        return self.mood_action_weights().get("window_grab_mult", 1.0)

    def mood_nudge_mult(self) -> float:
        """Multiplier for ambient nudge chance."""
        return self.mood_action_weights().get("nudge_mult", 1.0)

    def on_game_outcome(self, result: str) -> None:
        """Shift mood after a mini-game ends."""
        if not self.is_mood_system_enabled():
            return
        self.note_user_attention()
        if result == GAME_PLAYER_WIN:
            target = MOOD_ANNOYED if random.random() < 0.6 else MOOD_SAD
            self.shift_mood(target, random.uniform(0.15, 0.26))
            return
        if result == GAME_KINITO_WIN:
            if random.random() < 0.7:
                self.shift_mood(MOOD_HAPPY, random.uniform(0.16, 0.26))
            else:
                self.soften_mood(0.18)
            return
        if result == GAME_DRAW and random.random() < 0.45:
            self.shift_mood(MOOD_BORED, random.uniform(0.12, 0.2))

    def on_throw(self) -> None:
        """Shift mood after being flicked across the screen."""
        if not self.is_mood_system_enabled():
            return
        now = time.monotonic()
        last = float(getattr(self, "_last_throw_mood_at", 0.0))
        if now - last > self.MOOD_THROW_STREAK_WINDOW:
            self._throw_mood_hits = 0
        self._throw_mood_hits = int(getattr(self, "_throw_mood_hits", 0)) + 1
        self._last_throw_mood_at = now
        hits = self._throw_mood_hits
        if hits >= 3:
            self.shift_mood(MOOD_ANGRY, random.uniform(0.2, 0.3))
        elif hits == 2:
            self.shift_mood(MOOD_ANNOYED, random.uniform(0.18, 0.26))
        else:
            target = MOOD_ANNOYED if random.random() < 0.7 else MOOD_SAD
            self.shift_mood(target, random.uniform(0.14, 0.22))

    def on_hug_accepted(self) -> None:
        """Adjust mood after a successful hug (gradual, mood-dependent)."""
        self.note_user_attention()
        if not self.is_mood_system_enabled():
            return
        mood = self.get_mood()
        if mood == MOOD_ANGRY:
            if random.random() < 0.35:
                self.soften_mood(0.15)
            else:
                self.shift_mood(toward_neutral=True, amount=0.08)
            return
        if mood in {MOOD_SAD, MOOD_TIRED, MOOD_ANNOYED}:
            self.soften_mood(0.28)
            return
        if mood == MOOD_BORED:
            self.soften_mood(0.18)
            return
        self.soften_mood(0.2)

    def on_hug_declined(self) -> None:
        """Small chance to sour mood when a hug is refused."""
        self.note_user_attention()
        if not self.is_mood_system_enabled():
            return
        if random.random() < 0.55:
            target = MOOD_SAD if random.random() < 0.55 else MOOD_ANNOYED
            self.shift_mood(target, 0.2)

    def on_sleep_start(self, *, spontaneous: bool = False) -> None:
        """Note sleep start; tired mood may deepen slightly before rest."""
        if not self.is_mood_system_enabled():
            self._mood_sleep_was_spontaneous = spontaneous
            self._mood_sleep_started_as = self.get_mood()
            return
        if self.get_mood() == MOOD_TIRED and random.random() < 0.4:
            self.shift_mood(MOOD_TIRED, 0.08)
        self._mood_sleep_was_spontaneous = spontaneous
        self._mood_sleep_started_as = self.get_mood()

    def on_wake(self, *, spontaneous: bool | None = None) -> None:
        """Shift mood after waking; tired recovers more often than bored/annoyed."""
        if spontaneous is None:
            spontaneous = bool(getattr(self, "_mood_sleep_was_spontaneous", False))
        started = getattr(self, "_mood_sleep_started_as", self.get_mood())
        mood = self.get_mood()
        if not self.is_mood_system_enabled():
            return

        if started == MOOD_TIRED or mood == MOOD_TIRED:
            if random.random() < 0.75:
                self.soften_mood(0.35 if not spontaneous else 0.28)
            else:
                self.shift_mood(toward_neutral=True, amount=0.15)
            return

        if started in {MOOD_BORED, MOOD_ANNOYED} or mood in {MOOD_BORED, MOOD_ANNOYED}:
            roll = random.random()
            if roll < 0.35:
                self.shift_mood(toward_neutral=True, amount=0.12)
            elif roll < 0.65:
                # Nap was too short — a bit more annoyed.
                self.shift_mood(MOOD_ANNOYED, 0.18)
            # else: mood unchanged
            return

        if started == MOOD_SAD:
            if random.random() < 0.45:
                self.soften_mood(0.18)
            return

        if random.random() < 0.35:
            self.shift_mood(toward_neutral=True, amount=0.1)

    def _persist_mood(self) -> None:
        memory = getattr(self, "_memory", None)
        if memory is None or not hasattr(memory, "set_fact"):
            return
        memory.set_fact(
            KINITO_MOOD_FACT_KEY,
            format_mood_fact(self.get_mood(), self.get_mood_intensity()),
        )

    def _load_persisted_mood(self) -> None:
        memory = getattr(self, "_memory", None)
        if memory is None or not hasattr(memory, "get_fact"):
            return
        parsed = parse_mood_fact(memory.get_fact(KINITO_MOOD_FACT_KEY))
        if parsed is None:
            return
        mood, intensity, timestamp = parsed
        age = time.time() - timestamp
        if age > self.MOOD_STALE_SECONDS:
            self.set_mood(MOOD_NEUTRAL, 0.0, persist=False)
            return
        # Partially decay intensity based on age.
        decay = min(1.0, age / self.MOOD_STALE_SECONDS)
        intensity = clamp_intensity(intensity * (1.0 - 0.6 * decay))
        if intensity < 0.12:
            self.set_mood(MOOD_NEUTRAL, 0.0, persist=False)
        else:
            self.set_mood(mood, intensity, persist=False)
