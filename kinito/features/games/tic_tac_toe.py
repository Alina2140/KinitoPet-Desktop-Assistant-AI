"""Tic-tac-toe board logic, AI, and UI."""

import random
import tkinter as tk
from tkinter import Button, Frame, Label

from content import dialogue as dlg
from content import game_lines
from kinito.features.games.base import create_uniform_grid, open_game_window

WIN_LINES = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
)

PLAYER = "X"
KINITO = "O"
EMPTY = " "


def check_winner(board: list[str]) -> str | None:
    """Return PLAYER, KINITO, 'draw', or None if the game continues."""
    for a, b, c in WIN_LINES:
        if board[a] != EMPTY and board[a] == board[b] == board[c]:
            return board[a]
    if all(cell != EMPTY for cell in board):
        return "draw"
    return None


def available_moves(board: list[str]) -> list[int]:
    """Return indices of empty cells."""
    return [i for i, cell in enumerate(board) if cell == EMPTY]


def winning_move(board: list[str], player: str) -> int | None:
    """Return an index where *player* can win on the next move, if any."""
    for index in available_moves(board):
        trial = board[:]
        trial[index] = player
        if check_winner(trial) == player:
            return index
    return None


def choose_ai_move(board: list[str]) -> int:
    """Pick a move for Kinito using simple heuristics."""
    win = winning_move(board, KINITO)
    if win is not None:
        return win
    block = winning_move(board, PLAYER)
    if block is not None:
        return block
    if board[4] == EMPTY:
        return 4
    corners = [i for i in (0, 2, 6, 8) if board[i] == EMPTY]
    if corners:
        return random.choice(corners)
    return random.choice(available_moves(board))


class TicTacToeGame:
    """3x3 tic-tac-toe window: player is X, Kinito is O."""

    def __init__(self, app):
        self.app = app
        self.board = [EMPTY] * 9
        self.buttons: list[Button] = []
        self.status_label: Label | None = None
        self.finished = False
        self.window = None

    def open(self):
        """Open the game window."""
        self.window = open_game_window(
            self.app,
            "Tic-Tac-Toe with Kinito",
            360,
            540,
            min_width=300,
            min_height=460,
        )

        main = Frame(self.window)
        main.pack(fill=tk.BOTH, expand=True)

        self.status_label = Label(main, text="You are X. Your turn!")
        self.status_label.pack(pady=8)

        grid = create_uniform_grid(main, 3, 3, uniform="ttt")
        mark_font = ("Arial", 24, "bold")

        for row in range(3):
            for col in range(3):
                index = row * 3 + col
                button = Button(
                    grid,
                    text="",
                    font=mark_font,
                    width=3,
                    height=2,
                    anchor="center",
                    justify="center",
                    command=lambda i=index: self._player_move(i),
                )
                button.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
                self.buttons.append(button)

        Button(main, text="New Game", command=self._reset).pack(pady=(0, 10))

    def _reset(self):
        """Start a fresh board."""
        self.board = [EMPTY] * 9
        self.finished = False
        for button in self.buttons:
            button.config(text="", state="normal")
        if self.status_label:
            self.status_label.config(text="You are X. Your turn!")

    def _player_move(self, index: int):
        """Handle a click on cell *index*."""
        if self.finished or self.board[index] != EMPTY:
            return

        self.board[index] = PLAYER
        self.buttons[index].config(text=PLAYER, state="disabled")
        result = check_winner(self.board)
        if result:
            self._end_game(result)
            return

        ai_index = choose_ai_move(self.board)
        self.board[ai_index] = KINITO
        self.buttons[ai_index].config(text=KINITO, state="disabled")
        result = check_winner(self.board)
        if result:
            self._end_game(result)
        elif self.status_label:
            self.status_label.config(text="Your turn!")

    def _end_game(self, result: str):
        """Announce the outcome and lock the board."""
        self.finished = True
        for button in self.buttons:
            button.config(state="disabled")

        if result == PLAYER:
            line = dlg.pick_line(game_lines.TTT_PLAYER_WIN_LINES)
            status = "You win!"
        elif result == KINITO:
            line = dlg.pick_line(game_lines.TTT_KINITO_WIN_LINES)
            status = "Kinito wins!"
        else:
            line = dlg.pick_line(game_lines.TTT_DRAW_LINES)
            status = "Draw!"

        if self.status_label:
            self.status_label.config(text=status)
        self.app.speak_game_line(line)
