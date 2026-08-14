"""Rare fullscreen static glitch overlay and blue-screen flashes."""

import os
import random
import sys
import time
import tkinter as tk
from tkinter import Toplevel

from PIL import Image, ImageTk

from kinito.assets import crash_image_path


class GlitchMixin:
    """Brief screen static/distortion flashes during autonomous movement."""

    GLITCH_CHANCE = 1 / 1000
    GLITCH_DURATION_MS = 2000
    GLITCH_NOISE_SCALE = 6
    GLITCH_COOLDOWN_SECONDS = 180
    BLUE_SCREEN_CHANCE = 1 / 1000
    BLUE_SCREEN_DURATION_MS = 2000
    BLUE_SCREEN_COOLDOWN_SECONDS = 300

    def _overlay_virtual_screen_rect(self):
        """Return (x, y, width, height) covering the full virtual desktop."""
        if hasattr(self, "_query_virtual_screen_rect"):
            return self._query_virtual_screen_rect()
        self.root.update_idletasks()
        x = self.root.winfo_vrootx()
        y = self.root.winfo_vrooty()
        width = self.root.winfo_vrootwidth()
        height = self.root.winfo_vrootheight()
        return x, y, width, height

    def _overlay_primary_screen_rect(self):
        """Return (x, y, width, height) of the primary monitor.

        On Windows the primary display origin is always (0, 0).
        """
        if sys.platform == "win32":
            try:
                import ctypes

                user32 = ctypes.windll.user32
                width = int(user32.GetSystemMetrics(0))  # SM_CXSCREEN
                height = int(user32.GetSystemMetrics(1))  # SM_CYSCREEN
                if width > 0 and height > 0:
                    return 0, 0, width, height
            except (OSError, AttributeError, ValueError):
                pass

        self.root.update_idletasks()
        return 0, 0, self.root.winfo_screenwidth(), self.root.winfo_screenheight()

    def _make_overlay_window(self, *, x, y, width, height, bg="black"):
        """Create a borderless topmost overlay covering the given rectangle."""
        window = Toplevel(self.root)
        window.overrideredirect(True)
        window.geometry(f"{width}x{height}+{x}+{y}")
        window.configure(bg=bg)
        window.wm_attributes("-topmost", True)
        return window

    def maybe_trigger_screen_glitch(self) -> bool:
        """Roll for a rare screen glitch; schedule on the Tk main thread if it hits."""
        if not getattr(self, "_screen_effects_enabled", True):
            return False
        if getattr(self, "_focus_mode", False):
            return False
        if getattr(self, "_is_game_active", lambda: False)():
            return False
        if self.paused or getattr(self, "_is_position_locked_by_user", lambda: self.is_dragging)() or self._camera_active or self._browser_active:
            return False
        last_at = getattr(self, "_last_glitch_at", 0.0)
        if time.monotonic() - last_at < self.GLITCH_COOLDOWN_SECONDS:
            return False
        if random.random() >= self.GLITCH_CHANCE:
            return False
        self._last_glitch_at = time.monotonic()
        self.root.after(0, self._flash_screen_glitch)
        return True

    def maybe_trigger_blue_screen(self) -> bool:
        """Roll for an extremely rare fullscreen blue-screen flash."""
        if not getattr(self, "_screen_effects_enabled", True):
            return False
        if getattr(self, "_focus_mode", False):
            return False
        if getattr(self, "_is_game_active", lambda: False)():
            return False
        if self.paused or getattr(self, "_is_position_locked_by_user", lambda: self.is_dragging)() or self._camera_active or self._browser_active:
            return False
        if not os.path.isfile(crash_image_path):
            return False
        last_at = getattr(self, "_last_blue_screen_at", 0.0)
        if time.monotonic() - last_at < self.BLUE_SCREEN_COOLDOWN_SECONDS:
            return False
        if random.random() >= self.BLUE_SCREEN_CHANCE:
            return False
        self._last_blue_screen_at = time.monotonic()
        self.root.after(0, self._flash_blue_screen)
        return True

    def toggle_screen_effects(self):
        """Enable or disable rare screen glitch effects."""
        from content import dialogue as dlg

        self._screen_effects_enabled = not self._screen_effects_enabled
        if hasattr(self, "_persist_settings"):
            self._persist_settings()
        lines = (
            dlg.SCREEN_EFFECTS_ON_LINES
            if self._screen_effects_enabled
            else dlg.SCREEN_EFFECTS_OFF_LINES
        )
        self.speak(dlg.pick_line(lines), skip_ai=True)

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

    def _has_screen_effect_overlay(self) -> bool:
        """Return True while a glitch or blue-screen overlay is visible."""
        return self._has_glitch_overlay() or self._has_blue_screen_overlay()

    def _raise_screen_effect_overlays(self) -> None:
        """Keep glitch/BSOD above Kinito among topmost sibling windows."""
        # Blackout first, then BSOD, so the crash image stays on the primary monitor.
        for attr in ("_glitch_window", "_crash_blackout_window", "_crash_window"):
            window = getattr(self, attr, None)
            if window is None:
                continue
            try:
                if not window.winfo_exists():
                    continue
                window.wm_attributes("-topmost", True)
                window.lift()
                if hasattr(self, "_force_window_topmost"):
                    self._force_window_topmost(window)
            except tk.TclError:
                pass

    def _schedule_raise_screen_effect_overlays(self) -> None:
        """Debounce overlay re-raise onto the Tk thread (safe during surf)."""
        if not self._has_screen_effect_overlay():
            return
        if getattr(self, "_raise_overlay_pending", False):
            return
        self._raise_overlay_pending = True

        def _do_raise():
            self._raise_overlay_pending = False
            self._raise_screen_effect_overlays()

        try:
            self.root.after(0, _do_raise)
        except tk.TclError:
            self._raise_overlay_pending = False

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
        for attr in ("_crash_window", "_crash_blackout_window"):
            window = getattr(self, attr, None)
            if window is None:
                continue
            try:
                window.destroy()
            except tk.TclError:
                pass
            setattr(self, attr, None)
        self._crash_tk_image = None

    def _flash_screen_glitch(self):
        """Show a short-lived static overlay across the virtual screen."""
        if not self._running or not getattr(self, "_screen_effects_enabled", True):
            return
        if self._has_glitch_overlay():
            return

        x, y, width, height = self._overlay_virtual_screen_rect()
        if width < 1 or height < 1:
            return

        noise_w = max(width // self.GLITCH_NOISE_SCALE, 1)
        noise_h = max(height // self.GLITCH_NOISE_SCALE, 1)
        noise = Image.effect_noise((noise_w, noise_h), random.randint(40, 70)).convert("RGB")
        noise = noise.resize((width, height), Image.NEAREST)

        self._glitch_window = self._make_overlay_window(x=x, y=y, width=width, height=height)
        try:
            self._glitch_window.attributes("-alpha", 0.28)
        except tk.TclError:
            pass

        self._glitch_tk_image = ImageTk.PhotoImage(noise)
        label = tk.Label(
            self._glitch_window, image=self._glitch_tk_image, bd=0, highlightthickness=0
        )
        label.pack(fill="both", expand=True)

        self._raise_screen_effect_overlays()
        self._glitch_hide_timer = self.root.after(
            self.GLITCH_DURATION_MS,
            self.hide_screen_glitch,
        )

    def _flash_blue_screen(self):
        """Show the BSOD on the primary monitor; black out other screens briefly."""
        if not self._running or not getattr(self, "_screen_effects_enabled", True):
            return
        if self._has_blue_screen_overlay():
            return

        try:
            crash_img = Image.open(crash_image_path).convert("RGB")
        except OSError:
            return

        vx, vy, vw, vh = self._overlay_virtual_screen_rect()
        px, py, pw, ph = self._overlay_primary_screen_rect()
        if vw < 1 or vh < 1 or pw < 1 or ph < 1:
            return

        # Full virtual desktop goes black; BSOD sits on top of the primary only.
        self._crash_blackout_window = self._make_overlay_window(
            x=vx, y=vy, width=vw, height=vh
        )

        if crash_img.size != (pw, ph):
            crash_img = crash_img.resize((pw, ph), Image.Resampling.LANCZOS)

        self._crash_window = self._make_overlay_window(x=px, y=py, width=pw, height=ph)
        self._crash_tk_image = ImageTk.PhotoImage(crash_img)
        label = tk.Label(
            self._crash_window, image=self._crash_tk_image, bd=0, highlightthickness=0
        )
        label.pack(fill="both", expand=True)

        self._raise_screen_effect_overlays()
        self._crash_hide_timer = self.root.after(
            self.BLUE_SCREEN_DURATION_MS,
            self.hide_blue_screen,
        )
