"""Adjust colors window: the snake color and the chat name color are picked separately."""

from __future__ import annotations

import tkinter as tk
from tkinter import Canvas, Frame, Label, LabelFrame, Toplevel, colorchooser

from kinito.colors import normalize_hex_color
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

SNAKE_PREVIEW_SEGMENTS = 5
SNAKE_PREVIEW_CELL = 18
UI_BG = "#e6ded5"


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
            head, body = snake_palette(self.snake_color())
            top = cell // 2
            for index in range(SNAKE_PREVIEW_SEGMENTS):
                left = cell * (SNAKE_PREVIEW_SEGMENTS - index)
                canvas.create_rectangle(
                    left + 1,
                    top + 1,
                    left + cell - 1,
                    top + cell - 1,
                    fill=head if index == 0 else body,
                    outline="",
                )

        return refresh

    def _make_chat_name_preview(self, parent):
        row = Frame(parent, bg=UI_BG)
        row.pack(anchor="w")
        resolve = getattr(self, "_resolve_chat_user_label", None)
        name = resolve() if callable(resolve) else "You"
        name_label = Label(
            row, text=f"{name}:", font=("Segoe UI", 11, "underline"), bg=UI_BG
        )
        name_label.pack(side="left")
        Label(row, text="Hi Kinito!", font=("Segoe UI", 11), bg=UI_BG).pack(side="left", padx=(4, 0))

        def refresh():
            name_label.config(fg=self.chat_name_color())

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
