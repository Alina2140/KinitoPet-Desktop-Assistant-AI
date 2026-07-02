"""Hug sprite animations during virtual hugs."""

import random
import tkinter as tk

from content.hug_lines import HUG_LINES


class HugMixin:
    """Swap Kinito to dedicated hug sprites during hug interactions."""

    HUG_DURATION_MS = 8000

    def _cancel_hug_timer(self):
        """Cancel the scheduled end of the current hug pose."""
        timer = getattr(self, "_hug_timer", None)
        if timer is not None:
            try:
                self.root.after_cancel(timer)
            except (tk.TclError, ValueError):
                pass
            self._hug_timer = None

    def end_hug(self):
        """End the hug pose and restore the normal sprite when idle."""
        self._cancel_hug_timer()
        self._hug_mode = False
        if not self.talking:
            self.change_sprite(self.tk_img_normal)

    def _schedule_hug_end(self, delay_ms: int | None = None):
        """Return to the normal sprite after *delay_ms* milliseconds."""
        self._cancel_hug_timer()
        delay = self.HUG_DURATION_MS if delay_ms is None else delay_ms
        self._hug_timer = self.root.after(delay, self.end_hug)

    def give_hug(self):
        """Show hug sprites and speak a hug line."""
        self._hug_mode = True
        self.change_sprite(self.tk_img_hug)
        self._schedule_hug_end()
        self.speak(random.choice(HUG_LINES))
