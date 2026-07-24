"""Spontaneous ambient wellness/creepy reminder nudges."""

import random
import time
import tkinter as tk
from tkinter import Label, Toplevel

from content.nudge_lines import pick_nudge_line
from kinito.window_icon import apply_window_icon


class NudgesMixin:
    """Occasionally remind the user via speech bubble or text popup."""

    NUDGE_CHANCE = 1 / 300
    NUDGE_COOLDOWN_SECONDS = 300
    NUDGE_POPUP_CHANCE = 0.5
    NUDGE_POPUP_WIDTH = 320
    NUDGE_POPUP_HEIGHT = 140
    NUDGE_POPUP_AUTO_CLOSE_MS = 8000

    def maybe_trigger_ambient_reminder(self) -> bool:
        """Roll for an ambient nudge; schedule on the Tk main thread if it hits."""
        if not getattr(self, "_ambient_reminders_enabled", True):
            return False
        if getattr(self, "_focus_mode", False):
            return False
        if getattr(self, "_is_game_active", lambda: False)():
            return False
        if self.paused or self.is_dragging or self._camera_active or self._browser_active:
            return False
        if getattr(self, "_is_busy_with_speech", lambda: False)():
            return False
        last_at = getattr(self, "_last_nudge_at", 0.0)
        if time.monotonic() - last_at < self.NUDGE_COOLDOWN_SECONDS:
            return False
        if random.random() >= self.NUDGE_CHANCE:
            return False
        self._last_nudge_at = time.monotonic()
        self.root.after(0, self._present_ambient_nudge)
        return True

    def toggle_ambient_reminders(self):
        """Enable or disable spontaneous ambient reminder nudges."""
        from content import dialogue as dlg

        self._ambient_reminders_enabled = not getattr(
            self, "_ambient_reminders_enabled", True
        )
        lines = (
            dlg.REMINDERS_ON_LINES
            if self._ambient_reminders_enabled
            else dlg.REMINDERS_OFF_LINES
        )
        self.speak(dlg.pick_line(lines))

    def _present_ambient_nudge(self):
        """Show one nudge line as a bubble or a text popup."""
        if not self._running:
            return
        if not getattr(self, "_ambient_reminders_enabled", True):
            return
        text = pick_nudge_line()
        if random.random() < self.NUDGE_POPUP_CHANCE:
            self.show_popup_text(text, title="KinitoPET")
        else:
            self.speak(text)

    def show_popup_text(
        self,
        text,
        *,
        width=None,
        height=None,
        x=None,
        y=None,
        title="KinitoPET",
        auto_close_ms=None,
    ):
        """Show *text* in a compact topmost popup window."""
        width = self.NUDGE_POPUP_WIDTH if width is None else width
        height = self.NUDGE_POPUP_HEIGHT if height is None else height
        auto_close_ms = (
            self.NUDGE_POPUP_AUTO_CLOSE_MS if auto_close_ms is None else auto_close_ms
        )

        popup = Toplevel(self.root)
        popup.title(title)
        apply_window_icon(popup)
        popup.wm_attributes("-topmost", True)
        popup.geometry(f"{width}x{height}")

        label = Label(
            popup,
            text=text,
            wraplength=width - 40,
            justify="center",
            padx=16,
            pady=16,
        )
        label.pack(fill="both", expand=True)

        if x is None or y is None:
            vroot_x = self.root.winfo_vrootx()
            vroot_y = self.root.winfo_vrooty()
            vroot_w = self.root.winfo_vrootwidth()
            vroot_h = self.root.winfo_vrootheight()
            x = vroot_x + (vroot_w - width) // 2
            y = vroot_y + (vroot_h - height) // 2
        popup.geometry(f"{width}x{height}+{int(x)}+{int(y)}")

        def _handle_close():
            try:
                popup.destroy()
            except tk.TclError:
                pass

        popup.protocol("WM_DELETE_WINDOW", _handle_close)
        if auto_close_ms > 0:
            popup.after(auto_close_ms, _handle_close)
