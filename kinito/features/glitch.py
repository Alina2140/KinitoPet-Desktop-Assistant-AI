"""Rare fullscreen static glitch overlay and blue-screen flashes."""

import os
import random
import tkinter as tk
from tkinter import Toplevel

from PIL import Image, ImageTk

from kinito.assets import crash_image_path


class GlitchMixin:
    """Brief screen static/distortion flashes during autonomous movement."""

    GLITCH_CHANCE = 1 / 5000
    GLITCH_DURATION_MS = 250
    GLITCH_NOISE_SCALE = 6
    BLUE_SCREEN_CHANCE = 1 / 5000
    BLUE_SCREEN_DURATION_MS = 250

    def maybe_trigger_screen_glitch(self) -> bool:
        """Roll for a rare screen glitch; schedule on the Tk main thread if it hits."""
        if not getattr(self, "_screen_effects_enabled", True):
            return False
        if getattr(self, "_focus_mode", False):
            return False
        if self.paused or self.is_dragging or self._camera_active or self._browser_active:
            return False
        if random.random() >= self.GLITCH_CHANCE:
            return False
        self.root.after(0, self._flash_screen_glitch)
        return True

    def maybe_trigger_blue_screen(self) -> bool:
        """Roll for an extremely rare fullscreen blue-screen flash."""
        if not getattr(self, "_screen_effects_enabled", True):
            return False
        if getattr(self, "_focus_mode", False):
            return False
        if self.paused or self.is_dragging or self._camera_active or self._browser_active:
            return False
        if not os.path.isfile(crash_image_path):
            return False
        if random.random() >= self.BLUE_SCREEN_CHANCE:
            return False
        self.root.after(0, self._flash_blue_screen)
        return True

    def toggle_screen_effects(self):
        """Enable or disable rare screen glitch effects."""
        from content import dialogue as dlg

        self._screen_effects_enabled = not self._screen_effects_enabled
        lines = (
            dlg.SCREEN_EFFECTS_ON_LINES
            if self._screen_effects_enabled
            else dlg.SCREEN_EFFECTS_OFF_LINES
        )
        self.speak(dlg.pick_line(lines))

    def _has_glitch_overlay(self) -> bool:
        window = getattr(self, "_glitch_window", None)
        try:
            return window is not None and window.winfo_exists()
        except tk.TclError:
            return False

    def _has_blue_screen_overlay(self) -> bool:
        window = getattr(self, "_crash_window", None)
        try:
            return window is not None and window.winfo_exists()
        except tk.TclError:
            return False

    def _cancel_glitch_hide_timer(self):
        timer = getattr(self, "_glitch_hide_timer", None)
        if timer is not None:
            try:
                self.root.after_cancel(timer)
            except (tk.TclError, ValueError):
                pass
        self._glitch_hide_timer = None

    def _cancel_blue_screen_hide_timer(self):
        timer = getattr(self, "_crash_hide_timer", None)
        if timer is not None:
            try:
                self.root.after_cancel(timer)
            except (tk.TclError, ValueError):
                pass
        self._crash_hide_timer = None

    def hide_screen_glitch(self):
        """Close the glitch overlay immediately."""
        self._cancel_glitch_hide_timer()
        window = getattr(self, "_glitch_window", None)
        if window is not None:
            try:
                window.destroy()
            except tk.TclError:
                pass
            self._glitch_window = None
        self._glitch_tk_image = None

    def hide_blue_screen(self):
        """Close the blue-screen overlay immediately."""
        self._cancel_blue_screen_hide_timer()
        window = getattr(self, "_crash_window", None)
        if window is not None:
            try:
                window.destroy()
            except tk.TclError:
                pass
            self._crash_window = None
        self._crash_tk_image = None

    def _flash_screen_glitch(self):
        """Show a short-lived static overlay across the virtual screen."""
        if not self._running or not getattr(self, "_screen_effects_enabled", True):
            return
        if self._has_glitch_overlay():
            return

        self.root.update_idletasks()
        x = self.root.winfo_vrootx()
        y = self.root.winfo_vrooty()
        width = self.root.winfo_vrootwidth()
        height = self.root.winfo_vrootheight()
        if width < 1 or height < 1:
            return

        noise_w = max(width // self.GLITCH_NOISE_SCALE, 1)
        noise_h = max(height // self.GLITCH_NOISE_SCALE, 1)
        noise = Image.effect_noise((noise_w, noise_h), random.randint(40, 70)).convert("RGB")
        noise = noise.resize((width, height), Image.NEAREST)

        self._glitch_window = Toplevel(self.root)
        self._glitch_window.overrideredirect(True)
        self._glitch_window.geometry(f"{width}x{height}+{x}+{y}")
        self._glitch_window.configure(bg="black")
        self._glitch_window.wm_attributes("-topmost", True)
        try:
            self._glitch_window.attributes("-alpha", 0.28)
        except tk.TclError:
            pass

        self._glitch_tk_image = ImageTk.PhotoImage(noise)
        label = tk.Label(
            self._glitch_window, image=self._glitch_tk_image, bd=0, highlightthickness=0
        )
        label.pack(fill="both", expand=True)

        self._glitch_hide_timer = self.root.after(
            self.GLITCH_DURATION_MS,
            self.hide_screen_glitch,
        )

    def _flash_blue_screen(self):
        """Cover the screen briefly with the blue-screen crash image."""
        if not self._running or not getattr(self, "_screen_effects_enabled", True):
            return
        if self._has_blue_screen_overlay():
            return

        try:
            crash_img = Image.open(crash_image_path).convert("RGB")
        except OSError:
            return

        self.root.update_idletasks()
        x = self.root.winfo_vrootx()
        y = self.root.winfo_vrooty()
        width = self.root.winfo_vrootwidth()
        height = self.root.winfo_vrootheight()
        if width < 1 or height < 1:
            return

        if crash_img.size != (width, height):
            crash_img = crash_img.resize((width, height), Image.Resampling.LANCZOS)

        self._crash_window = Toplevel(self.root)
        self._crash_window.overrideredirect(True)
        self._crash_window.geometry(f"{width}x{height}+{x}+{y}")
        self._crash_window.configure(bg="black")
        self._crash_window.wm_attributes("-topmost", True)

        self._crash_tk_image = ImageTk.PhotoImage(crash_img)
        label = tk.Label(
            self._crash_window, image=self._crash_tk_image, bd=0, highlightthickness=0
        )
        label.pack(fill="both", expand=True)

        self._crash_hide_timer = self.root.after(
            self.BLUE_SCREEN_DURATION_MS,
            self.hide_blue_screen,
        )
