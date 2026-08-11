"""Minesweeper game window."""

from __future__ import annotations

import tkinter as tk
from tkinter import Button, Frame, Label

from content import dialogue as dlg
from content import game_lines
from kinito.features.games.base import create_uniform_grid, open_game_window
from kinito.features.games.minesweeper import (
    COLS,
    MINE_COUNT,
    ROWS,
    neighbor_count,
    new_game,
    remaining_mines,
    reveal_cell,
    toggle_flag,
)

FLAG = "F"
MINE = "*"
HIDDEN = ""

NUMBER_COLORS = {
    1: "#2563eb",
    2: "#16a34a",
    3: "#dc2626",
    4: "#7c3aed",
    5: "#b45309",
    6: "#0891b2",
    7: "#111827",
    8: "#6b7280",
}


class MinesweeperGame:
    """9x9 minesweeper: left-click reveal, right-click flag."""

    def __init__(self, app):
        self.app = app
        self.state = new_game()
        self.buttons: list[Button] = []
        self.status_label: Label | None = None
        self.window = None
        self._ended = False

    def open(self):
        """Open the minesweeper game window."""
        self.window = open_game_window(
            self.app,
            "Minesweeper with Kinito",
            420,
            520,
            min_width=360,
            min_height=460,
        )

        main = Frame(self.window)
        main.pack(fill=tk.BOTH, expand=True)

        self.status_label = Label(main, text=self._status_text())
        self.status_label.pack(side=tk.TOP, pady=8)

        grid = create_uniform_grid(main, ROWS, COLS, uniform="minesweeper")
        for index in range(ROWS * COLS):
            row, col = divmod(index, COLS)
            button = Button(
                grid,
                text=HIDDEN,
                width=3,
                height=1,
                command=lambda i=index: self._on_left_click(i),
            )
            button.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
            button.bind("<Button-3>", lambda event, i=index: self._on_right_click(i))
            button.bind("<Control-Button-1>", lambda event, i=index: self._on_right_click(i))
            self.buttons.append(button)

        Button(main, text="New Game", command=self._reset).pack(side=tk.BOTTOM, pady=(0, 10))

    def _status_text(self) -> str:
        if self.state["finished"]:
            if self.state["won"]:
                return "You cleared the board! New Game to play again."
            return "Boom! Mines revealed. New Game to try again."
        return (
            f"Mines left: {remaining_mines(self.state)}. "
            "Left-click open, right-click flag."
        )

    def _reset(self):
        """Start a fresh board."""
        self.state = new_game()
        self._ended = False
        for button in self.buttons:
            button.config(text=HIDDEN, fg="black", state="normal", relief=tk.RAISED)
        if self.status_label:
            self.status_label.config(text=self._status_text())

    def _refresh_cell(self, index: int):
        button = self.buttons[index]
        if index in self.state["flags"] and index not in self.state["revealed"]:
            button.config(text=FLAG, fg="#dc2626", disabledforeground="#dc2626", state="normal")
            return
        if index not in self.state["revealed"]:
            button.config(
                text=HIDDEN,
                fg="black",
                disabledforeground="gray50",
                state="normal",
                relief=tk.RAISED,
            )
            return
        if index in self.state["mines"]:
            button.config(
                text=MINE,
                fg="#111827",
                disabledforeground="#111827",
                state="disabled",
                relief=tk.SUNKEN,
            )
            return
        count = neighbor_count(self.state, index)
        if count == 0:
            button.config(
                text="",
                fg="black",
                disabledforeground="gray50",
                state="disabled",
                relief=tk.SUNKEN,
            )
        else:
            color = NUMBER_COLORS.get(count, "black")
            # Windows ignores fg on disabled buttons — set disabledforeground too.
            button.config(
                text=str(count),
                fg=color,
                disabledforeground=color,
                state="disabled",
                relief=tk.SUNKEN,
            )

    def _refresh_board(self):
        for index in range(ROWS * COLS):
            self._refresh_cell(index)
        if self.status_label:
            self.status_label.config(text=self._status_text())

    def _reveal_all_mines(self):
        for index in self.state["mines"]:
            self.state["revealed"].add(index)
            self.state["flags"].discard(index)

    def _lock_board(self):
        for button in self.buttons:
            button.config(state="disabled")

    def _end_game(self):
        if self._ended:
            return
        self._ended = True
        if not self.state["won"]:
            self._reveal_all_mines()
        self._refresh_board()
        self._lock_board()
        if self.state["won"]:
            line = dlg.pick_line(game_lines.MINESWEEPER_WIN_LINES).format(mines=MINE_COUNT)
            outcome = "player_win"
        else:
            line = dlg.pick_line(game_lines.MINESWEEPER_LOSE_LINES)
            outcome = "kinito_win"
        if hasattr(self.app, "on_game_outcome"):
            self.app.on_game_outcome(outcome)
        self.app.speak_game_line(line)

    def _on_left_click(self, index: int):
        if self.state["finished"]:
            return
        result = reveal_cell(self.state, index)
        if result == "ignored":
            return
        self._refresh_board()
        if result in ("win", "lose"):
            self._end_game()

    def _on_right_click(self, index: int):
        if self.state["finished"]:
            return
        if not toggle_flag(self.state, index):
            return
        self._refresh_cell(index)
        if self.status_label:
            self.status_label.config(text=self._status_text())
        return "break"
