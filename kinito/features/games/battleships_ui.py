"""Mini battleships game window."""

import tkinter as tk
from tkinter import Button, Frame, Label

from content import dialogue as dlg
from content import game_lines
from kinito.features.games.base import create_uniform_grid, open_game_window
from kinito.features.games.battleships import (
    GRID_SIZE,
    SHIP_COUNT,
    new_game,
    ships_remaining,
    shoot,
    shots_remaining,
)

WATER = "~"
MISS = "X"
HIT = "H"
SHIP = "S"


class BattleshipsGame:
    """5x5 battleships window: player shoots at Kinito's hidden ships."""

    def __init__(self, app):
        self.app = app
        self.state = new_game()
        self.buttons: list[Button] = []
        self.status_label: Label | None = None
        self.window = None
        self.commented_first_hit = False

    def open(self):
        """Open the battleships game window."""
        self.window = open_game_window(
            self.app,
            "Battleships with Kinito",
            340,
            480,
            min_width=300,
            min_height=420,
        )

        main = Frame(self.window)
        main.pack(fill=tk.BOTH, expand=True)

        self.status_label = Label(main, text=self._status_text())
        self.status_label.pack(side=tk.TOP, pady=8)

        grid = create_uniform_grid(main, GRID_SIZE, GRID_SIZE, uniform="battleships")
        for index in range(GRID_SIZE * GRID_SIZE):
            row, col = divmod(index, GRID_SIZE)
            button = Button(
                grid,
                text=WATER,
                width=3,
                height=1,
                command=lambda i=index: self._fire(i),
            )
            button.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
            self.buttons.append(button)

        Button(main, text="New Game", command=self._reset).pack(side=tk.BOTTOM, pady=(0, 10))

    def _status_text(self) -> str:
        if self.state["finished"]:
            return "Game over. S = ship. New Game to play again!"
        shots_left = shots_remaining(self.state)
        ships_left = ships_remaining(self.state)
        return f"Shots left: {shots_left}. Ships left: {ships_left}. Click a cell to fire!"

    def _reset(self):
        """Start a fresh game board."""
        self.state = new_game()
        self.commented_first_hit = False
        for button in self.buttons:
            button.config(text=WATER, state="normal")
        if self.status_label:
            self.status_label.config(text=self._status_text())

    def _reveal_ships(self):
        """Show unrevealed ship cells after the game ends."""
        for index in self.state["ships"]:
            button = self.buttons[index]
            if button.cget("text") == WATER:
                button.config(text=SHIP)
            button.config(state="disabled")

    def _end_game(self, result: str):
        """Lock the board, reveal ships, and announce the outcome."""
        self._reveal_ships()
        if self.status_label:
            self.status_label.config(text=self._status_text())

        if result == "win":
            line = dlg.pick_line(game_lines.BATTLESHIPS_WIN_LINES).format(
                shots=len(self.state["shots"]),
            )
        else:
            hits = len(self.state["hits"])
            line = dlg.pick_line(game_lines.BATTLESHIPS_LOSE_LINES).format(
                hits=hits,
                total=SHIP_COUNT,
            )
        self.app.speak_game_line(line)

    def _fire(self, index: int):
        """Handle a shot at cell *index*."""
        if self.state["finished"]:
            return

        result = shoot(self.state, index)
        if result == "already":
            return

        button = self.buttons[index]
        if result in ("hit", "win"):
            button.config(text=HIT, state="disabled")
            if not self.commented_first_hit:
                self.commented_first_hit = True
                self.app.speak_game_line(dlg.pick_line(game_lines.BATTLESHIPS_FIRST_HIT_LINES))
            elif result == "hit":
                self.app.speak_game_line(dlg.pick_line(game_lines.BATTLESHIPS_HIT_LINES))
        else:
            button.config(text=MISS, state="disabled")

        if self.status_label:
            self.status_label.config(text=self._status_text())

        if result in ("win", "lose"):
            self._end_game(result)
