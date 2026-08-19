"""Color guessing game UI (What the Hex? style)."""

from __future__ import annotations

import tkinter as tk
from tkinter import Button, Frame, Label

from content import dialogue as dlg
from content import game_lines
from kinito.features.games.base import open_game_window
from kinito.features.games.color_guess import (
    DEFAULT_DIFFICULTY,
    DIFFICULTIES,
    apply_guess,
    new_round,
)

NEUTRAL_HEX_FG = "#555555"
GRID_GAP = 8
GRID_PADDING = 12
CIRCLE_DIAMETER = 72
DEFAULT_WINDOW_SIZE = (640, 480)


def _grid_rows(count: int, cols: int) -> int:
    return max(1, (count + cols - 1) // cols)


def _max_columns_for_width(canvas_width: int, count: int) -> int:
    """Return maximum circles per row for fixed diameter and gap."""
    available_width = max(canvas_width - 2 * GRID_PADDING, 1)
    fit = int((available_width + GRID_GAP) // (CIRCLE_DIAMETER + GRID_GAP))
    return max(1, min(count, fit))


class ColorGuessGame:
    """Hex-code color guessing mini-game."""

    def __init__(self, app) -> None:
        self.app = app
        self.difficulty = DEFAULT_DIFFICULTY
        self.state = new_round(self.difficulty)
        self.window: tk.Toplevel | None = None
        self.hex_label: Label | None = None
        self.status_label: Label | None = None
        self.prompt_label: Label | None = None
        self.new_game_button: Button | None = None
        self.canvas: tk.Canvas | None = None
        self.canvas_frame: Frame | None = None
        self.v_scroll: tk.Scrollbar | None = None
        self.difficulty_buttons: dict[int, Button] = {}
        self._circle_ids: dict[int, int] = {}
        self._ended = False

    def open(self) -> None:
        """Open the color guessing game window."""
        width, height = DEFAULT_WINDOW_SIZE
        self.window = open_game_window(
            self.app,
            "Color Guess with Kinito",
            width,
            height,
            min_width=520,
            min_height=420,
        )

        main = Frame(self.window)
        main.pack(fill=tk.BOTH, expand=True, padx=16, pady=10)

        footer = Frame(main)
        footer.pack(side=tk.BOTTOM, fill=tk.X, pady=(8, 0))
        Label(footer, text="DIFFICULTY:", font=("Arial", 9)).pack(side=tk.LEFT)
        for value in DIFFICULTIES:
            button = Button(
                footer,
                text=str(value),
                width=3,
                relief=tk.FLAT,
                font=("Arial", 9, "bold" if value == self.difficulty else "normal"),
                command=lambda n=value: self._set_difficulty(n),
            )
            button.pack(side=tk.LEFT, padx=1)
            self.difficulty_buttons[value] = button

        controls = Frame(main)
        controls.pack(side=tk.BOTTOM, fill=tk.X, pady=(4, 0))
        self.prompt_label = Label(
            controls,
            text="GUESS THE COLOR",
            font=("Arial", 10),
            fg=NEUTRAL_HEX_FG,
        )
        self.prompt_label.pack()
        self.status_label = Label(controls, text="", font=("Arial", 12, "bold"))
        self.status_label.pack()
        self.new_game_button = Button(
            controls,
            text="NEW GAME",
            command=self._reset,
        )
        self.new_game_button.pack(pady=(4, 0))
        self.new_game_button.pack_forget()

        self.hex_label = Label(
            main,
            text=self.state["target_hex"],
            font=("Arial", 32, "bold"),
            fg=NEUTRAL_HEX_FG,
        )
        self.hex_label.pack(side=tk.TOP, pady=(8, 12))

        self.canvas_frame = Frame(main)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        self.canvas = tk.Canvas(self.canvas_frame, highlightthickness=0, bg="white")
        self.v_scroll = tk.Scrollbar(
            self.canvas_frame,
            orient=tk.VERTICAL,
            command=self.canvas.yview,
        )
        self.canvas.configure(
            yscrollcommand=self.v_scroll.set,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scroll.grid(row=0, column=1, sticky="ns")
        self.canvas_frame.rowconfigure(0, weight=1)
        self.canvas_frame.columnconfigure(0, weight=1)
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)

        self.window.after_idle(self._draw_circles)

    def _on_canvas_resize(self, _event=None) -> None:
        self._draw_circles()

    def _on_mouse_wheel(self, event) -> None:
        if self.canvas is None:
            return
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _set_difficulty(self, count: int) -> None:
        if count == self.difficulty and self.state["status"] == "playing":
            return
        self.difficulty = count
        self._start_new_round()

    def _start_new_round(self, *, resize_window: bool = False) -> None:
        self.state = new_round(self.difficulty)
        self._ended = False
        if self.new_game_button is not None:
            self.new_game_button.pack_forget()
        if self.status_label is not None:
            self.status_label.config(text="")
        if self.prompt_label is not None:
            self.prompt_label.config(text="GUESS THE COLOR")
        if self.hex_label is not None:
            self.hex_label.config(text=self.state["target_hex"], fg=NEUTRAL_HEX_FG)
        for value, button in self.difficulty_buttons.items():
            button.config(font=("Arial", 9, "bold" if value == self.difficulty else "normal"))
        self._draw_circles()

    def _reset(self) -> None:
        self._start_new_round()

    def _layout(self) -> tuple[int, int, int, int]:
        """Return columns, rows, content width and content height."""
        count = self.state["count"]
        canvas_width = max(self.canvas.winfo_width(), 1) if self.canvas else 1
        canvas_height = max(self.canvas.winfo_height(), 1) if self.canvas else 1
        cols = _max_columns_for_width(canvas_width, count)
        rows = _grid_rows(count, cols)
        row_width = cols * CIRCLE_DIAMETER + (cols - 1) * GRID_GAP
        grid_height = rows * CIRCLE_DIAMETER + (rows - 1) * GRID_GAP
        content_width = max(canvas_width, row_width + 2 * GRID_PADDING)
        content_height = max(canvas_height, grid_height + 2 * GRID_PADDING)
        return cols, rows, content_width, content_height

    def _circle_bounds(self, index: int) -> tuple[int, int, int, int]:
        """Return oval bounds for *index* in wrapped, centered rows."""
        cols, rows, content_width, _content_height = self._layout()
        count = self.state["count"]
        row = index // cols
        col = index % cols
        items_last_row = count % cols
        items_in_row = cols
        if row == rows - 1 and items_last_row:
            items_in_row = items_last_row
        row_width = items_in_row * CIRCLE_DIAMETER + (items_in_row - 1) * GRID_GAP
        row_start_x = (content_width - row_width) // 2
        x0 = row_start_x + col * (CIRCLE_DIAMETER + GRID_GAP)
        y0 = GRID_PADDING + row * (CIRCLE_DIAMETER + GRID_GAP)
        return x0, y0, x0 + CIRCLE_DIAMETER, y0 + CIRCLE_DIAMETER

    def _draw_circles(self) -> None:
        if self.canvas is None:
            return
        self.canvas.delete("all")
        self._circle_ids.clear()
        _cols, _rows, content_width, content_height = self._layout()
        self.canvas.configure(scrollregion=(0, 0, content_width, content_height))

        visible_indices = self._visible_indices()
        if not visible_indices:
            return

        for index in visible_indices:
            x0, y0, x1, y1 = self._circle_bounds(index)
            color = self.state["colors"][index]
            circle_id = self.canvas.create_oval(
                x0,
                y0,
                x1,
                y1,
                fill=color,
                outline=color,
                tags=(f"circle_{index}", "clickable"),
            )
            self._circle_ids[index] = circle_id

        self.canvas.tag_bind("clickable", "<Button-1>", self._on_canvas_click)

    def _visible_indices(self) -> list[int]:
        if self.state["status"] == "won":
            return [self.state["target_index"]]
        return [
            index
            for index in range(len(self.state["colors"]))
            if index not in self.state["removed"]
        ]

    def _on_canvas_click(self, event) -> None:
        if self.canvas is None or self.state["status"] != "playing":
            return
        item = self.canvas.find_closest(event.x, event.y)
        if not item:
            return
        tags = self.canvas.gettags(item[0])
        index = None
        for tag in tags:
            if tag.startswith("circle_"):
                index = int(tag.split("_", 1)[1])
                break
        if index is None:
            return
        self._on_guess(index)

    def _on_guess(self, index: int) -> None:
        result = apply_guess(self.state, index)
        if result == "ignored":
            return
        if result == "wrong":
            self._draw_circles()
            return
        self._on_win()

    def _on_win(self) -> None:
        if self._ended:
            return
        self._ended = True
        target = self.state["target_hex"]
        if self.hex_label is not None:
            self.hex_label.config(fg=target)
        if self.prompt_label is not None:
            self.prompt_label.config(text="")
        if self.status_label is not None:
            self.status_label.config(text="CORRECT!")
        if self.new_game_button is not None:
            self.new_game_button.pack(pady=(4, 0))
        self._draw_circles()
        if hasattr(self.app, "on_game_outcome"):
            self.app.on_game_outcome("player_win")
        should_speak = True
        if hasattr(self.app, "is_color_guess_voice_enabled"):
            should_speak = bool(self.app.is_color_guess_voice_enabled())
        if should_speak:
            line = dlg.pick_line(game_lines.COLOR_GUESS_WIN_LINES).format(color=target)
            self.app.speak_game_line(line)
