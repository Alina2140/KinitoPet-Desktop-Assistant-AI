"""Hug sprite animations during virtual hugs."""

import random
import tkinter as tk

from content.hug_lines import HUG_LINES


class HugMixin:
    """Swap Kinito to dedicated hug sprites during hug interactions."""

    HUG_DURATION_MS = 8000
    HUG_INTRO_SPRITE_SECONDS = 0.4
    HUG_SPRITE_SWAP_SECONDS = 1.0
    # Once the final frame (KinitoHug2) is held, occasionally squeeze back to
    # the first frame (KinitoHug1) and return — only on long hug lines, since
    # the held dwell means short lines end before a swap can happen.
    HUG_HOLD_SECONDS = (2.2, 3.6)
    HUG_SQUEEZE_SECONDS = 0.7
    HUG_SWAP_CHANCE = 0.4

    def _cancel_hug_timer(self):
        """Cancel the scheduled end of the current hug pose."""
        timer = getattr(self, "_hug_timer", None)
        if timer is not None:
            try:
                self.root.after_cancel(timer)
            except (tk.TclError, ValueError):
                pass
            self._hug_timer = None

    def _hug_sprite_frames(self):
        """Return the loaded hug frames, falling back to the original pair."""
        frames = tuple(getattr(self, "_hug_sprites", ()))
        if frames:
            return frames
        return tuple(
            sprite
            for sprite in (
                getattr(self, "tk_img_hug", None),
                getattr(self, "tk_img_hug2", None),
            )
            if sprite is not None
        )

    def _hug_sprite_delay(self):
        """Return how long the current hug frame should stay visible."""
        frames = self._hug_sprite_frames()
        frame = getattr(self, "_hug_frame", 0)
        if getattr(self, "_hug_squeezing", False):
            return self.HUG_SQUEEZE_SECONDS
        if len(frames) > 1 and frame >= len(frames) - 1:
            # Long, slightly random dwell on the final frame so an occasional
            # Hug1 squeeze reads as a squeeze, not flicker.
            return random.uniform(*self.HUG_HOLD_SECONDS)
        if frame < min(2, max(0, len(frames) - 1)):
            return self.HUG_INTRO_SPRITE_SECONDS
        return self.HUG_SPRITE_SWAP_SECONDS

    def _next_hug_sprite(self):
        """Return the next frame, holding on the final sprite with occasional squeezes."""
        frames = self._hug_sprite_frames()
        if not frames:
            return None
        frame = getattr(self, "_hug_frame", 0)
        last_frame = len(frames) - 1
        if getattr(self, "_hug_squeezing", False):
            self._hug_squeezing = False
            self._hug_frame = last_frame
            return frames[last_frame]
        if frame >= last_frame:
            if len(frames) > 1 and random.random() < self.HUG_SWAP_CHANCE:
                self._hug_squeezing = True
                self._hug_frame = 0
                return frames[0]
            return None
        self._hug_frame = frame + 1 if frame < 1 else last_frame
        return frames[self._hug_frame]

    def end_hug(self):
        """End the hug pose and restore the normal sprite when idle."""
        self._cancel_hug_timer()
        self._hug_mode = False
        self._hug_frame = 0
        self._hug_squeezing = False
        if not self.talking:
            self.change_sprite(self.tk_img_normal)

    def _schedule_hug_end(self, delay_ms: int | None = None):
        """Return to the normal sprite after *delay_ms* milliseconds."""
        self._cancel_hug_timer()
        delay = self.HUG_DURATION_MS if delay_ms is None else delay_ms
        self._hug_timer = self.root.after(delay, self.end_hug)

    def _enter_hug_pose(self):
        """Show hug sprites for the hug interaction."""
        self._cancel_hug_timer()
        self._hug_mode = True
        self._hug_frame = 0
        self._hug_squeezing = False
        frames = self._hug_sprite_frames()
        if frames:
            self.change_sprite(frames[0])

    def ask_for_hug(self):
        """Ask the user for a hug (yes/no); do not play thank-you hug lines alone."""
        from content import dialogue as dlg

        self.speak(dlg.pick_line(dlg.HUG_QUESTIONS), 45, True)

    def give_hug(self):
        """Show hug sprites and speak a hug line after the user accepts a hug."""
        from content import dialogue as dlg
        from content import llm_prompts as prompts
        from content.mood_lines import HUG_BY_MOOD, lines_for_mood

        if hasattr(self, "on_hug_accepted"):
            self.on_hug_accepted()
        mood = self.get_mood() if hasattr(self, "get_mood") else None
        intensity = self.get_mood_intensity() if hasattr(self, "get_mood_intensity") else 0.0
        mood_lines = lines_for_mood(HUG_BY_MOOD, mood) if mood else None
        line = dlg.pick_line_for_mood(
            HUG_LINES, mood=mood, intensity=intensity, mood_lines=mood_lines
        )
        self._begin_hug_after_speech = True
        self.speak(line, ai_hint=prompts.HUG_PROMPT)
