"""Sudoku game window: 9x9 board on top, number pad below."""

from __future__ import annotations

import tkinter as tk
from tkinter import Button, Frame, Label

from content import game_lines
from kinito.features.games.base import open_game_window
from kinito.features.games.sudoku import (
    DEFAULT_DIFFICULTY,
    DIFFICULTIES,
    SIZE,
    cell_value,
    erase,
    is_given,
    new_game,
    place,
    remaining_empty,
)

BG = "#f5f5f0"
GIVEN_BG = "#e4e4e4"
ENTRY_BG = "#ffffff"
HIGHLIGHT_BG = "#ffd966"
PAD_ACTIVE_BG = "#ffd966"
ERROR_BG = "#ff6b6b"
BOX_BG = "#c8c8c8"

CELL_FONT = ("Segoe UI", 16)
GIVEN_FONT = ("Segoe UI", 16, "bold")
PAD_FONT = ("Segoe UI", 14, "bold")
HEADER_FONT = ("Segoe UI", 10)
STATUS_FONT = ("Segoe UI", 9)

FLASH_MS = 350


class SudokuGame:
    """9x9 sudoku: pick a number below, then click cells to place it."""

    def __init__(self, app):
        self.app = app
        self.difficulty = DEFAULT_DIFFICULTY
        self.state = new_game(self.difficulty)
        self.selected: int | None = None
        self.erase_mode = False
        self.buttons: list[Button] = []
        self.pad_buttons: dict[int, Button] = {}
        self.erase_button: Button | None = None
        self.status_label: Label | None = None
        self.window = None
        self._ended = False

    def open(self):
        """Open the sudoku game window."""
        self.window = open_game_window(
            self.app,
            "Sudoku with Kinito",
            560,
            640,
            min_width=480,
            min_height=560,
        )
        self.window.configure(bg=BG)

        # Header: difficulty picker.
        header = Frame(self.window, bg=BG)
        header.pack(pady=(10, 4))
        Label(header, text="New game:", bg=BG, font=HEADER_FONT).pack(side=tk.LEFT)
        for name in DIFFICULTIES:
            Button(
                header,
                text=name.capitalize(),
                font=HEADER_FONT,
                command=lambda d=name: self._reset(d),
            ).pack(side=tk.LEFT, padx=4)

        # Board: 3x3 grid of block frames, each holding a 3x3 button grid.
        board = Frame(self.window, bg=BG)
        board.pack(padx=10, pady=6)
        blocks: dict[tuple[int, int], Frame] = {}
        for index in range(SIZE * SIZE):
            row, col = divmod(index, SIZE)
            block_key = (row // 3, col // 3)
            inner_row, inner_col = row % 3, col % 3
            if block_key not in blocks:
                block = Frame(board, bg=BOX_BG, bd=2, relief=tk.SOLID)
                block.grid(row=block_key[0], column=block_key[1], padx=1, pady=1)
                blocks[block_key] = block
            button = Button(
                blocks[block_key],
                text="",
                width=2,
                font=CELL_FONT,
                bd=1,
                relief=tk.SOLID,
                command=lambda i=index: self._on_cell_click(i),
            )
            button.grid(row=inner_row, column=inner_col)
            self.buttons.append(button)

        # Number pad: 1-9 plus an erase toggle.
        pad = Frame(self.window, bg=BG)
        pad.pack(pady=(6, 2))
        for number in range(1, SIZE + 1):
            button = Button(
                pad,
                text=str(number),
                width=3,
                font=PAD_FONT,
                bd=2,
                relief=tk.RAISED,
                command=lambda n=number: self._select_number(n),
            )
            button.pack(side=tk.LEFT, padx=2)
            self.pad_buttons[number] = button
        self.erase_button = Button(
            pad,
            text="Erase",
            font=PAD_FONT,
            bd=2,
            relief=tk.RAISED,
            command=self._toggle_erase,
        )
        self.erase_button.pack(side=tk.LEFT, padx=(10, 2))

        self.status_label = Label(self.window, text="", bg=BG, font=STATUS_FONT)
        self.status_label.pack(side=tk.BOTTOM, pady=(2, 8))
        self._update_status()
        self._refresh()

    def _select_number(self, number: int):
        self.selected = None if self.selected == number else number
        self.erase_mode = False
        self._refresh()

    def _toggle_erase(self):
        self.erase_mode = not self.erase_mode
        self._refresh()

    def _update_status(self, extra: str = ""):
        parts = [
            f"{self.difficulty.capitalize()} · {remaining_empty(self.state)} cells left"
            f" · mistakes {self.state['mistakes']}",
        ]
        scores = self.app.game_scores() if hasattr(self.app, "game_scores") else None
        if scores is not None:
            best = scores.sudoku_best_mistakes(self.difficulty)
            if best is not None:
                parts.append(f"best {best} mistakes")
        parts.append("Pick a number, then click a cell.")
        if extra:
            parts.append(extra)
        if self.status_label is not None:
            self.status_label.config(text="  ·  ".join(parts))

    def _refresh(self):
        selected = self.selected
        for index, button in enumerate(self.buttons):
            value = cell_value(self.state, index)
            given = is_given(self.state, index)
            highlight = selected is not None and value == selected
            button.config(
                text=str(value) if value else "",
                font=GIVEN_FONT if given else CELL_FONT,
                fg="#000000" if given else "#1a4fa0",
                bg=HIGHLIGHT_BG if highlight else (GIVEN_BG if given else ENTRY_BG),
                activebackground=HIGHLIGHT_BG if highlight else ENTRY_BG,
                state="disabled" if self._ended else "normal",
                disabledforeground="#000000" if given else "#1a4fa0",
            )
        for number, button in self.pad_buttons.items():
            active = self.selected == number
            button.config(
                bg=PAD_ACTIVE_BG if active else "SystemButtonFace",
                relief=tk.SUNKEN if active else tk.RAISED,
            )
        if self.erase_button is not None:
            self.erase_button.config(
                bg=PAD_ACTIVE_BG if self.erase_mode else "SystemButtonFace",
                relief=tk.SUNKEN if self.erase_mode else tk.RAISED,
            )

    def _flash_error(self, index: int):
        button = self.buttons[index]
        button.config(bg=ERROR_BG)
        if self.window is not None:
            self.window.after(FLASH_MS, self._refresh)

    def _on_cell_click(self, index: int):
        if self._ended:
            return
        if self.erase_mode:
            if erase(self.state, index):
                self._update_status()
                self._refresh()
            return
        if self.selected is None or is_given(self.state, index):
            return
        result = place(self.state, index, self.selected)
        if result == "invalid":
            self._update_status()
            self._flash_error(index)
            return
        if result in ("ok", "win"):
            self._update_status()
            self._refresh()
        if result == "win":
            self._end_game()

    def _end_game(self):
        if self._ended:
            return
        self._ended = True
        self._refresh()
        extra = "Solved!"
        if hasattr(self.app, "game_scores"):
            new_best = self.app.game_scores().record_sudoku_mistakes(
                self.difficulty, self.state["mistakes"]
            )
            if new_best:
                extra = "Solved! NEW BEST!"
        self._update_status(extra)
        line = game_lines.pick_game_line(
            self.app, game_lines.SUDOKU_WIN_LINES, "win"
        )
        if hasattr(self.app, "on_game_outcome"):
            self.app.on_game_outcome("player_win")
        self.app.speak_game_line(line)

    def _reset(self, difficulty: str):
        """Start a fresh puzzle at *difficulty*."""
        self.difficulty = difficulty
        self.state = new_game(difficulty)
        self.selected = None
        self.erase_mode = False
        self._ended = False
        self._update_status()
        self._refresh()
