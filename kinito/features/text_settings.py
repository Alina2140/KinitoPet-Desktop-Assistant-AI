"""Text size settings: a Word-style dropdown for the speech-bubble text size."""

from __future__ import annotations

import tkinter as tk
from tkinter import Frame, Label, Toplevel, ttk

from kinito.window_icon import apply_window_icon

TEXT_SIZE_OPTIONS = (8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24)

UI_BG = "#e6ded5"


class TextSettingsMixin:
    """Open a small window with a font-size dropdown (persisted)."""

    TEXT_SETTINGS_WIDTH = 340
    TEXT_SETTINGS_HEIGHT = 260

    def open_text_size_settings(self) -> None:
        """Show a dropdown to pick the text size used by speech bubbles."""
        from content import dialogue as dlg

        if hasattr(self, "close_speech_bubble"):
            try:
                self.close_speech_bubble()
            except Exception:
                pass
        if hasattr(self, "speak"):
            try:
                self.speak(dlg.pick_line(dlg.TEXT_SIZE_OPEN_LINES), skip_ai=True)
            except Exception:
                pass

        existing = getattr(self, "_text_settings_window", None)
        if existing is not None:
            try:
                if existing.winfo_exists():
                    existing.lift()
                    existing.focus_force()
                    return
            except tk.TclError:
                pass

        width, height = self.TEXT_SETTINGS_WIDTH, self.TEXT_SETTINGS_HEIGHT
        window = Toplevel(self.root)
        self._text_settings_window = window
        window.title("Text size")
        apply_window_icon(window)
        window.wm_attributes("-topmost", True)
        window.configure(bg=UI_BG)
        window.resizable(True, True)
        window.minsize(280, 180)

        self.root.update_idletasks()
        center = getattr(self, "_centered_origin_on_primary", None)
        if callable(center):
            x, y = center(width, height)
        else:
            x = self.root.winfo_vrootx() + (self.root.winfo_vrootwidth() - width) // 2
            y = self.root.winfo_vrooty() + (self.root.winfo_vrootheight() - height) // 2
        window.geometry(f"{width}x{height}+{int(x)}+{int(y)}")

        def _on_close():
            self._text_settings_window = None
            try:
                window.destroy()
            except tk.TclError:
                pass

        footer = Frame(window, bg=UI_BG)
        footer.pack(fill="x", side="bottom", padx=12, pady=8)
        tk.Button(footer, text="Close", bg=UI_BG, command=_on_close).pack(side="right")

        Label(
            window,
            text="Pick a text size. Changes save automatically.",
            anchor="w",
            padx=12,
            pady=8,
            bg=UI_BG,
        ).pack(fill="x")

        row = Frame(window, bg=UI_BG)
        row.pack(fill="x", padx=12, pady=4)
        Label(row, text="Size:", bg=UI_BG).pack(side="left")

        current = self.text_size()
        selected = tk.StringVar(value=str(current))
        combo = ttk.Combobox(
            row,
            textvariable=selected,
            values=[str(size) for size in TEXT_SIZE_OPTIONS],
            state="readonly",
            width=6,
        )
        combo.pack(side="left", padx=8)

        preview = Label(
            window,
            text="The quick brown fox jumps over the lazy dog.",
            bg=UI_BG,
            justify="left",
            anchor="nw",
            padx=12,
            pady=8,
        )
        preview.pack(fill="both", expand=True)

        def refresh_preview() -> None:
            preview.config(
                font=self._bubble_font(),
                wraplength=max(100, window.winfo_width() - 40),
            )

        def on_size_selected(_event=None) -> None:
            try:
                size = int(selected.get())
            except (TypeError, ValueError):
                return
            self.set_text_size(size)
            refresh_preview()

        combo.bind("<<ComboboxSelected>>", on_size_selected)
        window.bind("<Configure>", lambda _event: refresh_preview())
        refresh_preview()

        window.protocol("WM_DELETE_WINDOW", _on_close)
