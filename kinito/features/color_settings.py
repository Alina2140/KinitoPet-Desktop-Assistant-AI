"""Adjust colors window: the snake color and the chat name color are picked separately."""

from __future__ import annotations

import tkinter as tk
from tkinter import Canvas, Frame, Label, LabelFrame, Toplevel, colorchooser

from kinito.colors import (
    RAINBOW_COLOR,
    RAINBOW_COLORS,
    normalize_hex_color,
    rainbow_at,
)
from kinito.features.games.snake_ui import BG_COLOR as SNAKE_BG_COLOR
from kinito.features.games.snake_ui import snake_palette
from kinito.settings_store import DEFAULT_COLOR_SETTINGS
from kinito.window_icon import apply_window_icon

SNAKE_COLOR_PRESETS = (
    "#22c55e",
    "#14b8a6",
    "#3b82f6",
    "#a855f7",
    "#ec4899",
    "#ef4444",
    "#f97316",
    "#facc15",
)
CHAT_NAME_COLOR_PRESETS = (
    "#6a25eb",
    "#2563eb",
    "#0891b2",
    "#16a34a",
    "#d97706",
    "#dc2626",
    "#db2777",
    "#111827",
)
CONNECT_FOUR_COLOR_PRESETS = (
    "#7c3aed",
    "#2563eb",
    "#0891b2",
    "#16a34a",
    "#d97706",
    "#dc2626",
    "#db2777",
    "#111827",
)
TIC_TAC_TOE_COLOR_PRESETS = CONNECT_FOUR_COLOR_PRESETS

SNAKE_PREVIEW_SEGMENTS = 5
SNAKE_PREVIEW_CELL = 18
UI_BG = "#e6ded5"


def _rainbow_swatch_image(parent, width: int = 22, height: int = 22):
    """Return a small horizontal rainbow-gradient image for the Rainbow swatch."""
    try:
        from PIL import Image, ImageDraw, ImageTk

        from kinito.colors import hex_to_rgb

        stops = [hex_to_rgb(c) for c in RAINBOW_COLORS]
        img = Image.new("RGBA", (width, height))
        draw = ImageDraw.Draw(img)
        span = len(stops) - 1
        for x in range(width):
            pos = (x / max(1, width - 1)) * span
            low = min(int(pos), span - 1)
            frac = pos - low
            rgb = tuple(
                round(stops[low][ch] + (stops[low + 1][ch] - stops[low][ch]) * frac)
                for ch in range(3)
            )
            draw.line((x, 0, x, height - 1), fill=rgb)
        return ImageTk.PhotoImage(img, master=parent)
    except Exception:
        return None


class ColorSettingsMixin:
    """Let the user pick the snake color and their chat name color."""

    COLOR_SETTINGS_WIDTH = 420
    COLOR_SETTINGS_HEIGHT = 500

    def snake_color(self) -> str:
        """Return the chosen snake body color."""
        return normalize_hex_color(
            getattr(self, "_snake_color", None), DEFAULT_COLOR_SETTINGS["snake_color"]
        )

    def chat_name_color(self) -> str:
        """Return the chosen color for the user's name in the chat log."""
        return normalize_hex_color(
            getattr(self, "_chat_name_color", None), DEFAULT_COLOR_SETTINGS["chat_name_color"]
        )

    def set_snake_color(self, color: str) -> None:
        """Store a new snake color; open snake games pick it up on the next frame."""
        self._snake_color = normalize_hex_color(color, self.snake_color())
        if hasattr(self, "_persist_settings"):
            self._persist_settings()

    def set_chat_name_color(self, color: str) -> None:
        """Store a new chat name color and restyle an open chat log."""
        self._chat_name_color = normalize_hex_color(color, self.chat_name_color())
        apply = getattr(self, "apply_chat_name_color", None)
        if callable(apply):
            apply()
        if hasattr(self, "_persist_settings"):
            self._persist_settings()

    def connect_four_color(self) -> str:
        """Return the chosen color for the player's Connect Four discs."""
        return normalize_hex_color(
            getattr(self, "_connect_four_color", None),
            DEFAULT_COLOR_SETTINGS["connect_four_color"],
        )

    def set_connect_four_color(self, color: str) -> None:
        """Store a new Connect Four disc color and recolor an open game's discs."""
        self._connect_four_color = normalize_hex_color(color, self.connect_four_color())
        game = getattr(self, "_connect_four_game", None)
        refresh = getattr(game, "refresh_player_colors", None)
        if callable(refresh):
            try:
                refresh()
            except Exception:
                pass
        if hasattr(self, "_persist_settings"):
            self._persist_settings()

    def tic_tac_toe_color(self) -> str:
        """Return the chosen color for the player's Tic-Tac-Toe marks."""
        return normalize_hex_color(
            getattr(self, "_tic_tac_toe_color", None),
            DEFAULT_COLOR_SETTINGS["tic_tac_toe_color"],
        )

    def set_tic_tac_toe_color(self, color: str) -> None:
        """Store a new Tic-Tac-Toe mark color and recolor an open game's marks."""
        self._tic_tac_toe_color = normalize_hex_color(color, self.tic_tac_toe_color())
        game = getattr(self, "_tic_tac_toe_game", None)
        refresh = getattr(game, "refresh_player_marks", None)
        if callable(refresh):
            try:
                refresh()
            except Exception:
                pass
        if hasattr(self, "_persist_settings"):
            self._persist_settings()

    def open_color_settings(self) -> None:
        """Show the Adjust Colors window with separate Snake and Chat name sections."""
        from content import dialogue as dlg

        if hasattr(self, "speak"):
            try:
                self.speak(dlg.pick_line(dlg.COLOR_SETTINGS_OPEN_LINES), skip_ai=True)
            except Exception:
                pass

        existing = getattr(self, "_color_settings_window", None)
        if existing is not None:
            try:
                if existing.winfo_exists():
                    existing.lift()
                    existing.focus_force()
                    return
            except tk.TclError:
                pass

        width, height = self.COLOR_SETTINGS_WIDTH, self.COLOR_SETTINGS_HEIGHT
        window = Toplevel(self.root)
        self._color_settings_window = window
        window.title("Adjust Colors")
        apply_window_icon(window)
        window.wm_attributes("-topmost", True)
        window.configure(bg=UI_BG)

        self.root.update_idletasks()
        center = getattr(self, "_centered_origin_on_primary", None)
        if callable(center):
            x, y = center(width, height)
        else:
            x = self.root.winfo_vrootx() + (self.root.winfo_vrootwidth() - width) // 2
            y = self.root.winfo_vrooty() + (self.root.winfo_vrootheight() - height) // 2
        window.geometry(f"{width}x{height}+{int(x)}+{int(y)}")

        window.resizable(True, True)
        window.minsize(300, 240)

        # Scrollable container: the content can exceed the window when shrunk.
        scroller = Canvas(window, bg=UI_BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(window, orient="vertical", command=scroller.yview)
        scroller.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        scroller.pack(side="left", fill="both", expand=True)
        body = Frame(scroller, bg=UI_BG)
        body_window = scroller.create_window((0, 0), window=body, anchor="nw")

        def _sync_scroll_region(_event=None):
            scroller.configure(scrollregion=scroller.bbox("all"))
            scroller.itemconfigure(body_window, width=scroller.winfo_width())

        body.bind("<Configure>", _sync_scroll_region)
        scroller.bind("<Configure>", _sync_scroll_region)

        def _on_mousewheel(event):
            scroller.yview_scroll(int(-1 * (event.delta / 120)) or 1, "units")

        for widget in (window, scroller, body):
            widget.bind_all("<MouseWheel>", _on_mousewheel, add="+")

        Label(
            body,
            text="Pick your colors. Changes save automatically.",
            anchor="w",
            padx=12,
            pady=8,
            bg=UI_BG,
        ).pack(fill="x")

        self._build_color_section(
            body,
            "Snake",
            self._make_snake_preview,
            SNAKE_COLOR_PRESETS,
            self.snake_color,
            self.set_snake_color,
            DEFAULT_COLOR_SETTINGS["snake_color"],
        )
        self._build_color_section(
            body,
            "Chat name",
            self._make_chat_name_preview,
            CHAT_NAME_COLOR_PRESETS,
            self.chat_name_color,
            self.set_chat_name_color,
            DEFAULT_COLOR_SETTINGS["chat_name_color"],
        )
        self._build_color_section(
            body,
            "Connect 4 disc",
            self._make_connect_four_preview,
            CONNECT_FOUR_COLOR_PRESETS,
            self.connect_four_color,
            self.set_connect_four_color,
            DEFAULT_COLOR_SETTINGS["connect_four_color"],
        )
        self._build_color_section(
            body,
            "Tic-Tac-Toe mark",
            self._make_tic_tac_toe_preview,
            TIC_TAC_TOE_COLOR_PRESETS,
            self.tic_tac_toe_color,
            self.set_tic_tac_toe_color,
            DEFAULT_COLOR_SETTINGS["tic_tac_toe_color"],
        )

        def _on_close():
            self._color_settings_window = None
            try:
                window.unbind_all("<MouseWheel>")
                window.destroy()
            except tk.TclError:
                pass

        footer = Frame(body, bg=UI_BG)
        footer.pack(fill="x", side="bottom", padx=12, pady=8)
        tk.Button(footer, text="Close", bg=UI_BG, command=_on_close).pack(side="right")
        window.protocol("WM_DELETE_WINDOW", _on_close)

    def _make_snake_preview(self, parent):
        cell = SNAKE_PREVIEW_CELL
        canvas = Canvas(
            parent,
            width=cell * (SNAKE_PREVIEW_SEGMENTS + 2),
            height=cell * 2,
            bg=SNAKE_BG_COLOR,
            highlightthickness=0,
        )
        canvas.pack(anchor="w")

        def refresh():
            canvas.delete("all")
            selected = self.snake_color()
            head, body = ("", "") if selected == RAINBOW_COLOR else snake_palette(selected)
            top = cell // 2
            for index in range(SNAKE_PREVIEW_SEGMENTS):
                left = cell * (SNAKE_PREVIEW_SEGMENTS - index)
                if selected == RAINBOW_COLOR:
                    fill = rainbow_at(index)
                else:
                    fill = head if index == 0 else body
                canvas.create_rectangle(
                    left + 1,
                    top + 1,
                    left + cell - 1,
                    top + cell - 1,
                    fill=fill,
                    outline="",
                )

        return refresh

    def _make_chat_name_preview(self, parent):
        row = Frame(parent, bg=UI_BG)
        row.pack(anchor="w")
        resolve = getattr(self, "_resolve_chat_user_label", None)
        name = resolve() if callable(resolve) else "You"
        name_frame = Frame(row, bg=UI_BG)
        name_frame.pack(side="left")
        Label(row, text="Hi Kinito!", font=("Segoe UI", 11), bg=UI_BG).pack(side="left", padx=(4, 0))

        def refresh():
            for widget in name_frame.winfo_children():
                widget.destroy()
            selected = self.chat_name_color()
            for index, char in enumerate(f"{name}:"):
                fg = rainbow_at(index) if selected == RAINBOW_COLOR else selected
                Label(
                    name_frame,
                    text=char,
                    font=("Segoe UI", 11, "underline"),
                    bg=UI_BG,
                    fg=fg,
                ).pack(side="left")

        return refresh

    def _make_connect_four_preview(self, parent):
        cell = SNAKE_PREVIEW_CELL
        canvas = Canvas(
            parent,
            width=cell * 3,
            height=cell * 2,
            bg=UI_BG,
            highlightthickness=0,
        )
        canvas.pack(anchor="w")

        def refresh():
            from kinito.colors import lighten_hex

            canvas.delete("all")
            color = self.connect_four_color()
            if color == RAINBOW_COLOR:
                # Show the column gradient as a row of mini discs.
                mini = cell * 2 // 3
                for index in range(5):
                    offset = index * (mini + 1)
                    canvas.create_oval(
                        offset,
                        cell // 2,
                        offset + mini,
                        cell // 2 + mini,
                        fill=rainbow_at(4 - index),
                        outline="",
                    )
                return
            canvas.create_oval(
                2,
                2,
                cell * 2 - 2,
                cell * 2 - 2,
                fill=lighten_hex(color, 0.85),
                outline="",
            )
            canvas.create_oval(
                cell // 2,
                cell // 2,
                cell * 2 - cell // 2,
                cell * 2 - cell // 2,
                fill=color,
                outline="",
            )

        return refresh

    def _make_tic_tac_toe_preview(self, parent):
        row = Frame(parent, bg=UI_BG)
        row.pack(anchor="w")
        x_frame = Frame(row, bg=UI_BG)
        x_frame.pack(side="left")
        Label(
            row,
            text=" O",
            font=("Segoe UI", 14, "bold"),
            bg=UI_BG,
            fg="#fa96ff",
        ).pack(side="left", padx=(6, 0))

        def refresh():
            for widget in x_frame.winfo_children():
                widget.destroy()
            selected = self.tic_tac_toe_color()
            marks = (
                [rainbow_at(4 - i) for i in range(3)]
                if selected == RAINBOW_COLOR
                else [selected]
            )
            for mark_color in marks:
                Label(
                    x_frame,
                    text="X",
                    font=("Segoe UI", 14, "bold"),
                    bg=UI_BG,
                    fg=mark_color,
                ).pack(side="left")

        return refresh

    def _build_color_section(
        self, window, title, make_preview, presets, current, apply, default
    ) -> None:
        section = LabelFrame(window, text=title, padx=10, pady=8, bg=UI_BG)
        section.pack(fill="x", padx=12, pady=6)
        refresh_preview = make_preview(section)

        swatches = Frame(section, bg=UI_BG)
        swatches.pack(fill="x", pady=(8, 4))
        swatch_buttons: dict[str, tk.Button] = {}

        actions = Frame(section, bg=UI_BG)
        actions.pack(fill="x", pady=(4, 0))
        current_label = Label(actions, anchor="e", bg=UI_BG)

        def refresh():
            refresh_preview()
            selected = current()
            current_label.config(text=selected)
            for color, button in swatch_buttons.items():
                button.config(relief=tk.SUNKEN if color == selected else tk.RAISED)

        def choose(color: str):
            apply(color)
            refresh()

        for color in presets:
            button = tk.Button(
                swatches,
                bg=color,
                activebackground=color,
                width=2,
                bd=3,
                relief=tk.RAISED,
                command=lambda c=color: choose(c),
            )
            button.pack(side="left", padx=2)
            swatch_buttons[color] = button

        rainbow_image = _rainbow_swatch_image(swatches)
        rainbow_button = tk.Button(
            swatches,
            image=rainbow_image,
            text="R" if rainbow_image is None else "",
            fg="#a855f7",
            bd=3,
            relief=tk.RAISED,
            command=lambda: choose(RAINBOW_COLOR),
        )
        rainbow_button.image = rainbow_image
        rainbow_button.pack(side="left", padx=2)
        swatch_buttons[RAINBOW_COLOR] = rainbow_button

        def pick_custom():
            _rgb, hex_color = colorchooser.askcolor(
                color=current(), parent=window, title=f"{title} color"
            )
            if hex_color:
                choose(hex_color)

        tk.Button(actions, text="Custom...", bg=UI_BG, command=pick_custom).pack(side="left")
        tk.Button(actions, text="Reset", bg=UI_BG, command=lambda: choose(default)).pack(
            side="left", padx=6
        )
        current_label.pack(side="right")
        refresh()
