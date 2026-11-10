"""Rare fake-terminal easter egg: a pretend console typing creepy commands.

Everything shown is static text from content/terminal_scripts.py — nothing is
ever executed, read, or written by this feature.
"""

from __future__ import annotations

import getpass
import random
import sys
import time
import tkinter as tk

from content.terminal_scripts import FAKE_TERMINAL_SCRIPTS, PROMPT
from kinito.tk_toplevels import (
    _toplevel_hwnd,
    create_staged_toplevel,
    pin_assistant_screen_position,
    reveal_staged_toplevel,
    schedule_assistant_position_restore,
)
from kinito.window_targets import list_monitor_rects, random_fully_visible_origin


def _apply_system_titlebar_theme(window) -> None:
    """Match the window's title bar to the Windows app theme (like real cmd)."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        import winreg

        dark = True
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            )
            light, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            dark = not light
            winreg.CloseKey(key)
        except OSError:
            pass
        hwnd = _toplevel_hwnd(window)
        if not hwnd:
            return
        value = ctypes.c_int(1 if dark else 0)
        dwmapi = ctypes.windll.dwmapi
        for attr in (20, 19):  # DWMWA_USE_IMMERSIVE_DARK_MODE (20 on Win11, 19 on older)
            if dwmapi.DwmSetWindowAttribute(
                int(hwnd), attr, ctypes.byref(value), ctypes.sizeof(value)
            ) == 0:
                break
    except (OSError, AttributeError, ValueError, TypeError):
        pass


class FakeTerminalMixin:
    """Occasionally open a fake console window typing spooky commands."""

    TERMINAL_CHANCE = 1 / 800
    TERMINAL_COOLDOWN_SECONDS = 600
    TERMINAL_WIDTH = 620
    TERMINAL_HEIGHT = 360
    TERMINAL_TYPE_MS = 28
    TERMINAL_LINE_PAUSE_MS = 260
    TERMINAL_CMD_PAUSE_MS = 450
    TERMINAL_CLOSE_DELAY_MS = 2600
    TERMINAL_FONT = ("Consolas", 10)
    TERMINAL_BG = "#0c0c0c"
    TERMINAL_FG = "#cccccc"

    def maybe_trigger_terminal(self) -> bool:
        """Roll for a rare fake-terminal popup; schedule on the Tk main thread."""
        if not getattr(self, "_terminal_enabled", True):
            return False
        if getattr(self, "_focus_mode", False):
            return False
        if getattr(self, "_is_game_active", lambda: False)():
            return False
        if (
            self.paused
            or getattr(
                self, "_is_position_locked_by_user", lambda: self.is_dragging
            )()
            or self._camera_active
            or self._browser_active
        ):
            return False
        last_at = getattr(self, "_last_terminal_at", 0.0)
        if last_at > 0 and time.monotonic() - last_at < self.TERMINAL_COOLDOWN_SECONDS:
            return False
        chance = self.TERMINAL_CHANCE
        if getattr(self, "_special_days_enabled", True):
            from content.special_days import seasonal_multiplier

            chance *= seasonal_multiplier("terminal_mult")
        if random.random() >= chance:
            return False
        self._last_terminal_at = time.monotonic()
        self.root.after(0, self._open_fake_terminal)
        return True

    def toggle_terminal(self):
        """Enable or disable the fake-terminal easter egg."""
        from content import dialogue as dlg

        self._terminal_enabled = not getattr(self, "_terminal_enabled", True)
        if not self._terminal_enabled:
            self.hide_fake_terminal()
        if hasattr(self, "_persist_settings"):
            self._persist_settings()
        lines = (
            dlg.TERMINAL_ON_LINES
            if self._terminal_enabled
            else dlg.TERMINAL_OFF_LINES
        )
        self.speak(dlg.pick_line(lines), skip_ai=True)

    def _has_fake_terminal(self) -> bool:
        window = getattr(self, "_terminal_window", None)
        try:
            return window is not None and window.winfo_exists()
        except tk.TclError:
            return False

    def _cancel_terminal_timer(self):
        for timer in getattr(self, "_terminal_timers", ()):
            try:
                self.root.after_cancel(timer)
            except (tk.TclError, ValueError):
                pass
        self._terminal_timers = []

    def _terminal_after(self, delay_ms, callback):
        timer = self.root.after(delay_ms, callback)
        self._terminal_timers.append(timer)
        return timer

    def hide_fake_terminal(self):
        """Close the fake terminal immediately and cancel pending typing."""
        self._cancel_terminal_timer()
        window = getattr(self, "_terminal_window", None)
        if window is not None:
            try:
                window.destroy()
            except tk.TclError:
                pass
        self._terminal_window = None
        self._terminal_text = None

    def _terminal_script_lines(self):
        """Pick a script and personalize placeholders (e.g. {user})."""
        script = random.choice(FAKE_TERMINAL_SCRIPTS)
        try:
            user = getpass.getuser() or "player"
        except Exception:  # noqa: BLE001
            user = "player"
        return [
            (kind, text.replace("{user}", user)) for kind, text in script
        ]

    def _open_fake_terminal(self):
        """Open a console-looking window and start typing a random script."""
        if not self._running or not getattr(self, "_terminal_enabled", True):
            return
        if self._has_fake_terminal():
            return

        pinned = pin_assistant_screen_position(self)
        window = create_staged_toplevel(self.root)
        self._terminal_window = window
        window.title(r"C:\Windows\system32\cmd.exe")
        window.configure(bg=self.TERMINAL_BG)

        text = tk.Text(
            window,
            bg=self.TERMINAL_BG,
            fg=self.TERMINAL_FG,
            font=self.TERMINAL_FONT,
            bd=0,
            highlightthickness=0,
            insertbackground=self.TERMINAL_FG,
            wrap="none",
        )
        text.insert("end", "Microsoft Windows [Version 10.0.19045.3656]\n")
        text.insert("end", "(c) Kinito Corporation. All rights reserved.\n\n")
        text.configure(state="disabled")
        text.pack(fill="both", expand=True)
        self._terminal_text = text

        try:
            fallback = self._query_virtual_screen_rect()
        except Exception:  # noqa: BLE001
            self.root.update_idletasks()
            fallback = (
                int(self.root.winfo_vrootx()),
                int(self.root.winfo_vrooty()),
                int(self.root.winfo_vrootwidth()),
                int(self.root.winfo_vrootheight()),
            )
        monitors = list_monitor_rects(fallback=fallback)
        x, y = random_fully_visible_origin(
            self.TERMINAL_WIDTH,
            self.TERMINAL_HEIGHT,
            monitors=monitors,
            margin=24,
        )
        reveal_staged_toplevel(
            window,
            geometry=f"{self.TERMINAL_WIDTH}x{self.TERMINAL_HEIGHT}+{x}+{y}",
        )
        schedule_assistant_position_restore(self, *pinned)
        _apply_system_titlebar_theme(window)

        window.protocol("WM_DELETE_WINDOW", self.hide_fake_terminal)
        self._terminal_lines = self._terminal_script_lines()
        self._terminal_line_index = 0
        self._terminal_char_index = 0
        self._terminal_after(600, self._terminal_type_next)

    def _terminal_append(self, chunk: str) -> bool:
        """Append *chunk* to the console text; return False if the window died."""
        text = getattr(self, "_terminal_text", None)
        if text is None or not self._has_fake_terminal():
            return False
        try:
            text.configure(state="normal")
            text.insert("end", chunk)
            text.see("end")
            text.configure(state="disabled")
        except tk.TclError:
            return False
        return True

    def _terminal_type_next(self):
        """Type the next character/line of the current script step."""
        if not self._has_fake_terminal():
            return
        lines = getattr(self, "_terminal_lines", [])
        index = getattr(self, "_terminal_line_index", 0)
        if index >= len(lines):
            self._terminal_after(self.TERMINAL_CLOSE_DELAY_MS, self.hide_fake_terminal)
            return

        kind, text = lines[index]
        if kind == "out":
            if not self._terminal_append(text + "\n"):
                return
            self._terminal_line_index = index + 1
            self._terminal_char_index = 0
            self._terminal_after(self.TERMINAL_LINE_PAUSE_MS, self._terminal_type_next)
            return

        # "cmd": type character by character, prefixed by the prompt.
        char_index = getattr(self, "_terminal_char_index", 0)
        full = PROMPT + text
        if char_index >= len(full):
            if not self._terminal_append("\n"):
                return
            self._terminal_line_index = index + 1
            self._terminal_char_index = 0
            self._terminal_after(self.TERMINAL_CMD_PAUSE_MS, self._terminal_type_next)
            return
        if not self._terminal_append(full[char_index]):
            return
        self._terminal_char_index = char_index + 1
        self._terminal_after(self.TERMINAL_TYPE_MS, self._terminal_type_next)
