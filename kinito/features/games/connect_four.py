"""Connect Four board logic, AI, and UI."""

from __future__ import annotations

import copy
import random
import tkinter as tk
from tkinter import Button, Frame, Label

from content import dialogue as dlg
from content import game_lines
from kinito.features.games.base import create_uniform_grid, open_game_window

ROWS = 6
COLS = 7
PLAYER = "L"
KINITO = "R"
EMPTY = " "

PLAYER_COLOR = "#7c3aed"
KINITO_COLOR = "#fa96ff"
PLAYER_BG = "#ddd6fe"
KINITO_BG = "#fbcfe8"
EMPTY_BG = "SystemButtonFace"
EMPTY_MARK = "○"
DISC_MARK = "●"

# Prefer center columns when no win/block is available.
COLUMN_PRIORITY = (3, 2, 4, 1, 5, 0, 6)


def new_board() -> list[list[str]]:
    """Create an empty 6x7 board (row 0 = top)."""
    return [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]


def valid_columns(board: list[list[str]]) -> list[int]:
    """Return columns that still have an empty top cell."""
    return [col for col in range(COLS) if board[0][col] == EMPTY]


def drop_disc(board: list[list[str]], col: int, player: str) -> tuple[int, int] | None:
    """Drop *player*'s disc into *col*. Return (row, col) or None if full/invalid."""
    if col < 0 or col >= COLS:
        return None
    for row in range(ROWS - 1, -1, -1):
        if board[row][col] == EMPTY:
            board[row][col] = player
            return row, col
    return None


def _four_in_a_row(board: list[list[str]], row: int, col: int, dr: int, dc: int) -> str | None:
    """If four equal discs start at (row, col) along (dr, dc), return that player."""
    piece = board[row][col]
    if piece == EMPTY:
        return None
    for step in range(1, 4):
        r, c = row + dr * step, col + dc * step
        if not (0 <= r < ROWS and 0 <= c < COLS) or board[r][c] != piece:
            return None
    return piece


def check_winner(board: list[list[str]]) -> str | None:
    """Return PLAYER, KINITO, 'draw', or None if the game continues."""
    directions = ((0, 1), (1, 0), (1, 1), (1, -1))
    for row in range(ROWS):
        for col in range(COLS):
            for dr, dc in directions:
                winner = _four_in_a_row(board, row, col, dr, dc)
                if winner:
                    return winner
    if all(board[0][col] != EMPTY for col in range(COLS)):
        return "draw"
    return None


def winning_column(board: list[list[str]], player: str) -> int | None:
    """Return a column where *player* would win immediately, if any."""
    for col in valid_columns(board):
        trial = copy.deepcopy(board)
        if drop_disc(trial, col, player) is None:
            continue
        if check_winner(trial) == player:
            return col
    return None


def choose_ai_column(board: list[list[str]], rng: random.Random | None = None) -> int:
    """Pick a column for Kinito: win, block, prefer center, else random."""
    source = rng or random
    win = winning_column(board, KINITO)
    if win is not None:
        return win
    block = winning_column(board, PLAYER)
    if block is not None:
        return block
    valid = set(valid_columns(board))
    for col in COLUMN_PRIORITY:
        if col in valid:
            return col
    return source.choice(list(valid))


class ConnectFourGame:
    """6x7 Connect Four: player is purple (L), Kinito is pink (R)."""

    def __init__(self, app):
        self.app = app
        self.board = new_board()
        self.buttons: list[list[Button]] = []
        self.status_label: Label | None = None
        self.finished = False
        self._busy = False
        self.window = None

    def open(self):
        """Open the Connect Four game window."""
        self.window = open_game_window(
            self.app,
            "Connect Four with Kinito",
            420,
            520,
            min_width=360,
            min_height=460,
        )

        main = Frame(self.window)
        main.pack(fill=tk.BOTH, expand=True)

        self.status_label = Label(
            main,
            text="You are purple. Click a column — your turn!",
        )
        self.status_label.pack(pady=8)

        grid = create_uniform_grid(main, ROWS, COLS, uniform="connect_four")
        mark_font = ("Segoe UI Symbol", 18, "bold")

        self.buttons = []
        for row in range(ROWS):
            row_buttons: list[Button] = []
            for col in range(COLS):
                button = Button(
                    grid,
                    text=EMPTY_MARK,
                    font=mark_font,
                    width=3,
                    height=1,
                    anchor="center",
                    justify="center",
                    command=lambda c=col: self._player_move(c),
                )
                button.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
                row_buttons.append(button)
            self.buttons.append(row_buttons)

        Button(main, text="New Game", command=self._reset).pack(pady=(0, 10))

    def _reset(self):
        """Start a fresh board."""
        self.board = new_board()
        self.finished = False
        self._busy = False
        for row in range(ROWS):
            for col in range(COLS):
                self.buttons[row][col].config(
                    text=EMPTY_MARK,
                    fg="black",
                    disabledforeground="gray50",
                    bg=EMPTY_BG,
                    state="normal",
                )
        if self.status_label:
            self.status_label.config(text="You are purple. Click a column — your turn!")

    def _refresh_cell(self, row: int, col: int):
        """Update one button to match the board cell."""
        piece = self.board[row][col]
        button = self.buttons[row][col]
        if piece == PLAYER:
            # disabledforeground is required on Windows — fg alone becomes gray.
            button.config(
                text=DISC_MARK,
                fg=PLAYER_COLOR,
                disabledforeground=PLAYER_COLOR,
                bg=PLAYER_BG,
                state="disabled",
            )
        elif piece == KINITO:
            button.config(
                text=DISC_MARK,
                fg=KINITO_COLOR,
                disabledforeground=KINITO_COLOR,
                bg=KINITO_BG,
                state="disabled",
            )
        else:
            button.config(
                text=EMPTY_MARK,
                fg="black",
                disabledforeground="gray50",
                bg=EMPTY_BG,
                state="normal",
            )

    def _lock_board(self):
        for row in self.buttons:
            for button in row:
                button.config(state="disabled")

    def _player_move(self, col: int):
        """Handle a click aiming at column *col*."""
        if self.finished or self._busy:
            return
        placed = drop_disc(self.board, col, PLAYER)
        if placed is None:
            return
        row, c = placed
        self._refresh_cell(row, c)

        result = check_winner(self.board)
        if result:
            self._end_game(result)
            return

        self._busy = True
        if self.status_label:
            self.status_label.config(text="Kinito's turn…")
        if self.window is not None:
            self.window.after(280, self._kinito_move)
        else:
            self._kinito_move()

    def _kinito_move(self):
        """Let Kinito play one disc after a short delay."""
        if self.finished:
            self._busy = False
            return
        col = choose_ai_column(self.board)
        placed = drop_disc(self.board, col, KINITO)
        self._busy = False
        if placed is None:
            if self.status_label:
                self.status_label.config(text="Your turn!")
            return
        row, c = placed
        self._refresh_cell(row, c)

        result = check_winner(self.board)
        if result:
            self._end_game(result)
        elif self.status_label:
            self.status_label.config(text="Your turn!")

    def _end_game(self, result: str):
        """Announce the outcome and lock the board."""
        self.finished = True
        self._busy = False
        self._lock_board()

        if result == PLAYER:
            line = dlg.pick_line(game_lines.CONNECT_FOUR_PLAYER_WIN_LINES)
            status = "You win! Four in a row."
        elif result == KINITO:
            line = dlg.pick_line(game_lines.CONNECT_FOUR_KINITO_WIN_LINES)
            status = "Kinito wins!"
        else:
            line = dlg.pick_line(game_lines.CONNECT_FOUR_DRAW_LINES)
            status = "Draw! Board is full."

        if self.status_label:
            self.status_label.config(text=status)
        self.app.speak_game_line(line)
