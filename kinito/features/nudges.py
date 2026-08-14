"""Spontaneous ambient wellness/creepy reminder nudges."""

from __future__ import annotations

import random
import sys
import time
import tkinter as tk
from tkinter import Canvas, Frame, Label, Toplevel

from PIL import Image, ImageDraw, ImageTk

from content.app_lines import maybe_pick_app_aware_nudge_line
from content.nudge_lines import pick_nudge_line
from kinito.window_icon import apply_window_icon
from kinito.window_targets import list_monitor_rects, random_fully_visible_origin


class NudgesMixin:
    """Occasionally remind the user via a Windows-style text popup."""

    NUDGE_CHANCE = 1 / 270
    NUDGE_COOLDOWN_SECONDS = 300
    NUDGE_POPUP_MAX_WRAP = 340
    NUDGE_POPUP_MIN_WRAP = 180
    NUDGE_POPUP_AUTO_CLOSE_MS = 6000
    APP_AWARE_NUDGE_CHANCE = 0.35
    BORED_PLAY_INVITE_CHANCE = 0.4
    BORED_PLAY_INVITE_INTENSITY = 0.3

    _NUDGE_BG = "#ffffff"
    _NUDGE_FOOTER_BG = "#f3f3f3"
    _NUDGE_BORDER = "#e5e5e5"
    _NUDGE_TEXT = "#1b1b1b"
    _NUDGE_BTN_BORDER = "#8a8a8a"
    _NUDGE_MSG_FONT_CANDIDATES = (
        ("Segoe UI Variable Text", 9),
        ("Segoe UI Variable", 9),
        ("Segoe UI", 9),
    )
    _NUDGE_BTN_FONT_CANDIDATES = (
        ("Segoe UI Variable Text", 9),
        ("Segoe UI Variable", 9),
        ("Segoe UI", 9),
    )

    def maybe_trigger_ambient_reminder(self) -> bool:
        """Roll for an ambient nudge; schedule on the Tk main thread if it hits."""
        if not getattr(self, "_ambient_reminders_enabled", True):
            return False
        if getattr(self, "_focus_mode", False):
            return False
        if getattr(self, "_is_game_active", lambda: False)():
            return False
        if self.paused or getattr(self, "_is_position_locked_by_user", lambda: self.is_dragging)() or self._camera_active or self._browser_active:
            return False
        if getattr(self, "_is_busy_with_speech", lambda: False)():
            return False
        if self._nudge_popup_is_open():
            return False
        last_at = getattr(self, "_last_nudge_at", 0.0)
        if time.monotonic() - last_at < self.NUDGE_COOLDOWN_SECONDS:
            return False
        chance = self.NUDGE_CHANCE
        if hasattr(self, "mood_nudge_mult"):
            chance *= max(0.05, float(self.mood_nudge_mult()))
        if random.random() >= chance:
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
        if hasattr(self, "_persist_settings"):
            self._persist_settings()
        lines = (
            dlg.REMINDERS_ON_LINES
            if self._ambient_reminders_enabled
            else dlg.REMINDERS_OFF_LINES
        )
        self.speak(dlg.pick_line(lines), skip_ai=True)

    def _pick_ambient_nudge_text(self) -> str:
        """Pick a wellness/creepy nudge, sometimes referencing open apps."""
        from content.nudge_lines import pick_play_invite_nudge_line
        from kinito.features.mood import MOOD_BORED

        if (
            hasattr(self, "get_mood")
            and hasattr(self, "get_mood_intensity")
            and getattr(self, "is_mood_system_enabled", lambda: True)()
            and self.get_mood() == MOOD_BORED
            and self.get_mood_intensity() >= self.BORED_PLAY_INVITE_INTENSITY
            and random.random() < self.BORED_PLAY_INVITE_CHANCE
        ):
            return pick_play_invite_nudge_line()

        snapshot = None
        get_snapshot = getattr(self, "get_app_snapshot", None)
        if callable(get_snapshot):
            snapshot = get_snapshot()
        app_line = maybe_pick_app_aware_nudge_line(
            snapshot, chance=self.APP_AWARE_NUDGE_CHANCE
        )
        if app_line:
            return app_line
        return pick_nudge_line()

    def _present_ambient_nudge(self):
        """Show one nudge line as a Windows-style system dialog."""
        if not self._running:
            return
        if not getattr(self, "_ambient_reminders_enabled", True):
            return
        existing = getattr(self, "_nudge_popup", None)
        if existing is not None:
            try:
                if existing.winfo_exists():
                    return
            except tk.TclError:
                self._nudge_popup = None
        text = self._pick_ambient_nudge_text()
        self.show_popup_text(text, title="KinitoPET")

    def _nudge_popup_is_open(self) -> bool:
        """Return True while a nudge dialog is still on screen."""
        existing = getattr(self, "_nudge_popup", None)
        if existing is None:
            return False
        try:
            return bool(existing.winfo_exists())
        except tk.TclError:
            self._nudge_popup = None
            return False

    def _pin_assistant_screen_position(self) -> tuple[int, int]:
        """Remember Kinito's logical position so Toplevel creation cannot teleport him."""
        try:
            pinned_x = int(getattr(self, "x", self.root.winfo_x()))
            pinned_y = int(getattr(self, "y", self.root.winfo_y()))
        except (tk.TclError, TypeError, ValueError):
            pinned_x, pinned_y = 0, 0
        self.x = pinned_x
        self.y = pinned_y
        return pinned_x, pinned_y

    def _restore_assistant_screen_position(self, pinned_x: int, pinned_y: int) -> None:
        """Re-apply *pinned_x*/*pinned_y* to the overrideredirect root window."""
        self.x = int(pinned_x)
        self.y = int(pinned_y)
        try:
            if not self.root.winfo_exists():
                return
            self.root.geometry(f"+{self.x}+{self.y}")
        except tk.TclError:
            pass

    @staticmethod
    def _deiconify_nudge_popup_noactivate(popup: tk.Toplevel) -> None:
        """Show *popup* without stealing focus from Kinito's root window."""
        try:
            popup.wm_attributes("-topmost", True)
            popup.deiconify()
        except tk.TclError:
            return
        if sys.platform != "win32":
            return
        try:
            import ctypes

            hwnd = int(popup.winfo_id())
            parent = ctypes.windll.user32.GetParent(hwnd)
            if parent:
                hwnd = parent
            # HWND_TOPMOST + NOMOVE/NOSIZE/NOACTIVATE
            ctypes.windll.user32.SetWindowPos(
                hwnd,
                -1,
                0,
                0,
                0,
                0,
                0x0002 | 0x0001 | 0x0010,
            )
        except (OSError, AttributeError, ValueError, TypeError, tk.TclError):
            pass

    @staticmethod
    def _pick_nudge_font(root: tk.Misc, candidates: tuple[tuple[str, int], ...]) -> tuple:
        """Return the first installed font from *candidates*, else Tk default."""
        try:
            available = {name.casefold() for name in root.tk.call("font", "families")}
        except tk.TclError:
            available = set()
        for family, size in candidates:
            if family.casefold() in available:
                return (family, size)
        return candidates[-1]

    @classmethod
    def _nudge_wraplength_for(cls, text: str, *, font: tuple) -> int:
        """Choose a wrap width so short messages stay compact."""
        # Rough average glyph width for Segoe UI ~0.5em at this size.
        size = int(font[1]) if len(font) > 1 else 12
        approx_char_px = max(6, int(size * 0.55))
        natural = max(len(line) for line in (text.splitlines() or [text])) * approx_char_px
        return max(cls.NUDGE_POPUP_MIN_WRAP, min(cls.NUDGE_POPUP_MAX_WRAP, natural + 8))

    @staticmethod
    def _make_nudge_info_icon(size: int = 32, *, master: tk.Misc | None = None) -> ImageTk.PhotoImage:
        """Return a blue circular question-mark icon (Windows-like)."""
        from PIL import ImageFont

        scale = 4
        canvas_size = size * scale
        image = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse((0, 0, canvas_size - 1, canvas_size - 1), fill=(0, 120, 212, 255))
        try:
            font = ImageFont.truetype("segoeui.ttf", int(canvas_size * 0.62))
        except OSError:
            font = ImageFont.load_default()
        mark = "?"
        bbox = draw.textbbox((0, 0), mark, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(
            (
                (canvas_size - tw) / 2 - bbox[0],
                (canvas_size - th) / 2 - bbox[1] - canvas_size * 0.02,
            ),
            mark,
            font=font,
            fill=(255, 255, 255, 255),
        )
        image = image.resize((size, size), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(image, master=master)

    @classmethod
    def _attach_rounded_ok_button(
        cls,
        parent: tk.Misc,
        command,
        *,
        font: tuple,
        text: str = "OK",
    ) -> Label:
        """Create a Windows-like rounded OK button on *parent*."""
        from PIL import ImageFont

        pad_x, pad_y, radius = 20, 5, 6
        scale = 3
        try:
            family, size = font[0], int(font[1])
        except (IndexError, TypeError, ValueError):
            family, size = "Segoe UI", 8
        try:
            pil_font = ImageFont.truetype("segoeui.ttf", size * scale)
        except OSError:
            try:
                pil_font = ImageFont.truetype(f"{family}.ttf", size * scale)
            except OSError:
                pil_font = ImageFont.load_default()

        probe = Image.new("RGBA", (1, 1))
        probe_draw = ImageDraw.Draw(probe)
        bbox = probe_draw.textbbox((0, 0), text, font=pil_font)
        text_w = max(bbox[2] - bbox[0], 12 * scale)
        text_h = max(bbox[3] - bbox[1], 10 * scale)
        width = text_w + pad_x * 2 * scale
        height = text_h + pad_y * 2 * scale

        def _render(*, fill: tuple[int, int, int], border: tuple[int, int, int]) -> ImageTk.PhotoImage:
            image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            draw.rounded_rectangle(
                (0, 0, width - 1, height - 1),
                radius=radius * scale,
                fill=fill + (255,),
                outline=border + (255,),
                width=scale,
            )
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            draw.text(
                ((width - tw) / 2 - bbox[0], (height - th) / 2 - bbox[1]),
                text,
                font=pil_font,
                fill=(27, 27, 27, 255),
            )
            out = image.resize(
                (max(1, width // scale), max(1, height // scale)),
                Image.Resampling.LANCZOS,
            )
            return ImageTk.PhotoImage(out, master=parent)

        normal = _render(fill=(255, 255, 255), border=(138, 138, 138))
        pressed = _render(fill=(229, 229, 229), border=(138, 138, 138))
        label = Label(
            parent,
            image=normal,
            bg=cls._NUDGE_FOOTER_BG,
            bd=0,
            cursor="hand2",
        )
        label._nudge_btn_images = (normal, pressed)  # keep refs
        label._nudge_ok_text = text

        def _press(_event=None):
            label.configure(image=pressed)

        def _release(_event=None):
            label.configure(image=normal)
            if callable(command):
                command()

        label.bind("<ButtonPress-1>", _press)
        label.bind("<ButtonRelease-1>", _release)
        return label

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
        """Show *text* in a compact Windows-style topmost dialog popup."""
        auto_close_ms = (
            self.NUDGE_POPUP_AUTO_CLOSE_MS if auto_close_ms is None else auto_close_ms
        )
        if self._nudge_popup_is_open():
            return

        # Creating a Toplevel under an overrideredirect root can teleport Kinito
        # on Windows; pin and restore his logical screen position around setup.
        pinned_x, pinned_y = self._pin_assistant_screen_position()

        popup = Toplevel(self.root)
        self._nudge_popup = popup
        try:
            popup.withdraw()
        except tk.TclError:
            pass
        try:
            popup.attributes("-alpha", 0.0)
        except tk.TclError:
            pass
        # Park off-screen until sized, so Windows never flashes a default frame.
        popup.geometry("-10000-10000")
        popup.title(title)
        apply_window_icon(popup)
        popup.configure(bg=self._NUDGE_BG)
        popup.resizable(False, False)
        try:
            # Slimmer caption; avoid transient() — it relocates overrideredirect parents.
            popup.wm_attributes("-toolwindow", True)
        except tk.TclError:
            pass

        msg_font = self._pick_nudge_font(popup, self._NUDGE_MSG_FONT_CANDIDATES)
        btn_font = self._pick_nudge_font(popup, self._NUDGE_BTN_FONT_CANDIDATES)
        wrap = (
            max(self.NUDGE_POPUP_MIN_WRAP, int(width) - 96)
            if width is not None
            else self._nudge_wraplength_for(str(text), font=msg_font)
        )

        body = Frame(popup, bg=self._NUDGE_BG)
        body.pack(fill="x", padx=18, pady=(16, 10))

        icon_photo = self._make_nudge_info_icon(32, master=popup)
        popup._nudge_icon_photo = icon_photo  # keep reference
        Label(body, image=icon_photo, bg=self._NUDGE_BG, bd=0).pack(
            side="left", anchor="n", padx=(0, 12), pady=(1, 0)
        )

        Label(
            body,
            text=text,
            wraplength=wrap,
            justify="left",
            anchor="nw",
            bg=self._NUDGE_BG,
            fg=self._NUDGE_TEXT,
            font=msg_font,
        ).pack(side="left", anchor="nw")

        footer = Frame(popup, bg=self._NUDGE_FOOTER_BG)
        footer.pack(fill="x", side="bottom")

        Canvas(
            footer,
            height=1,
            bg=self._NUDGE_BORDER,
            highlightthickness=0,
            bd=0,
        ).pack(fill="x", side="top")

        def _handle_close():
            if getattr(self, "_nudge_popup", None) is popup:
                self._nudge_popup = None
            try:
                popup.destroy()
            except tk.TclError:
                pass
            self._restore_assistant_screen_position(pinned_x, pinned_y)

        button_row = Frame(footer, bg=self._NUDGE_FOOTER_BG)
        button_row.pack(fill="x", padx=12, pady=10)
        ok_btn = self._attach_rounded_ok_button(
            button_row,
            _handle_close,
            font=btn_font,
            text="OK",
        )
        ok_btn.pack(side="right")

        popup.update_idletasks()
        needed_w = popup.winfo_reqwidth()
        needed_h = popup.winfo_reqheight()
        if width is not None:
            needed_w = int(width)
        if height is not None:
            needed_h = int(height)

        if x is None or y is None:
            fallback = None
            query = getattr(self, "_query_virtual_screen_rect", None)
            if callable(query):
                try:
                    fallback = query()
                except Exception:
                    fallback = None
            if fallback is None:
                try:
                    fallback = (
                        int(self.root.winfo_vrootx()),
                        int(self.root.winfo_vrooty()),
                        int(self.root.winfo_vrootwidth()),
                        int(self.root.winfo_vrootheight()),
                    )
                except tk.TclError:
                    fallback = None
            monitors = list_monitor_rects(fallback=fallback)
            x, y = random_fully_visible_origin(
                needed_w,
                needed_h,
                monitors=monitors,
                margin=16,
            )
        popup.geometry(f"{int(needed_w)}x{int(needed_h)}+{int(x)}+{int(y)}")

        popup.protocol("WM_DELETE_WINDOW", _handle_close)
        self._deiconify_nudge_popup_noactivate(popup)
        try:
            popup.attributes("-alpha", 1.0)
        except tk.TclError:
            pass
        self._restore_assistant_screen_position(pinned_x, pinned_y)
        # Windows may move the borderless root asynchronously after the popup maps.
        try:
            self.root.after(1, lambda: self._restore_assistant_screen_position(pinned_x, pinned_y))
            self.root.after(50, lambda: self._restore_assistant_screen_position(pinned_x, pinned_y))
        except tk.TclError:
            pass

        if auto_close_ms > 0:
            popup.after(auto_close_ms, _handle_close)
