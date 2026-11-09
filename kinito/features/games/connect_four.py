"""Connect Four board logic, AI, and UI."""

from __future__ import annotations

import copy
import random
import tkinter as tk
from tkinter import Button, Frame, Label

from content import game_lines
from kinito.colors import RAINBOW_COLOR, rainbow_at
from kinito.features.games.base import create_uniform_grid, open_game_window

ROWS = 6
COLS = 7
PLAYER = "L"
KINITO = "R"
EMPTY = " "

PLAYER_COLOR = "#7c3aed"
KINITO_COLOR = "#fa96ff"
KINITO_BG = "#fbcfe8"
EMPTY_BG = "SystemButtonFace"
EMPTY_MARK = "○"
DISC_MARK = "●"

# Soft center bias for scoring (not a hard pick order).
def _center_weight(col: int, cols: int) -> int:
    """Symmetric center weight for a column of a *cols*-wide board."""
    return min(col + 1, cols - col)


# Selectable board sizes: (label, cols, rows). Classic is the original 7x6.
BOARD_SIZES = [
    ("Classic 7×6", 7, 6),
    ("Big 9×7", 9, 7),
    ("Huge 11×8", 11, 8),
]


def new_board(rows: int = ROWS, cols: int = COLS) -> list[list[str]]:
    """Create an empty board (row 0 = top)."""
    return [[EMPTY for _ in range(cols)] for _ in range(rows)]


def valid_columns(board: list[list[str]], cols: int = COLS) -> list[int]:
    """Return columns that still have an empty top cell."""
    return [col for col in range(cols) if board[0][col] == EMPTY]


def drop_disc(
    board: list[list[str]], col: int, player: str, rows: int = ROWS, cols: int = COLS
) -> tuple[int, int] | None:
    """Drop *player*'s disc into *col*. Return (row, col) or None if full/invalid."""
    if col < 0 or col >= cols:
        return None
    for row in range(rows - 1, -1, -1):
        if board[row][col] == EMPTY:
            board[row][col] = player
            return row, col
    return None


def _four_in_a_row(
    board: list[list[str]], row: int, col: int, dr: int, dc: int,
    rows: int = ROWS, cols: int = COLS,
) -> str | None:
    """If four equal discs start at (row, col) along (dr, dc), return that player."""
    piece = board[row][col]
    if piece == EMPTY:
        return None
    for step in range(1, 4):
        r, c = row + dr * step, col + dc * step
        if not (0 <= r < rows and 0 <= c < cols) or board[r][c] != piece:
            return None
    return piece


def check_winner(board: list[list[str]], rows: int = ROWS, cols: int = COLS) -> str | None:
    """Return PLAYER, KINITO, 'draw', or None if the game continues."""
    directions = ((0, 1), (1, 0), (1, 1), (1, -1))
    for row in range(rows):
        for col in range(cols):
            for dr, dc in directions:
                winner = _four_in_a_row(board, row, col, dr, dc, rows, cols)
                if winner:
                    return winner
    if all(board[0][col] != EMPTY for col in range(cols)):
        return "draw"
    return None


def winning_column(
    board: list[list[str]], player: str, rows: int = ROWS, cols: int = COLS
) -> int | None:
    """Return a column where *player* would win immediately, if any."""
    for col in valid_columns(board, cols):
        trial = copy.deepcopy(board)
        if drop_disc(trial, col, player, rows, cols) is None:
            continue
        if check_winner(trial, rows, cols) == player:
            return col
    return None


def _gives_opponent_immediate_win(
    board: list[list[str]], col: int, rows: int = ROWS, cols: int = COLS
) -> bool:
    """True if dropping in *col* lets the player win on the next move."""
    trial = copy.deepcopy(board)
    if drop_disc(trial, col, KINITO, rows, cols) is None:
        return True
    return winning_column(trial, PLAYER, rows, cols) is not None


def _adjacent_score(
    board: list[list[str]], row: int, col: int, player: str,
    rows: int = ROWS, cols: int = COLS,
) -> int:
    """Score nearby friendly discs; horizontal/diagonal outweigh pure vertical."""
    score = 0
    weights = (
        ((0, 1), 4),
        ((0, -1), 4),
        ((1, 1), 3),
        ((1, -1), 3),
        ((-1, 1), 3),
        ((-1, -1), 3),
        ((1, 0), 1),
        ((-1, 0), 1),
    )
    for (dr, dc), weight in weights:
        r, c = row + dr, col + dc
        if 0 <= r < rows and 0 <= c < cols and board[r][c] == player:
            score += weight
    return score


def _score_column(
    board: list[list[str]], col: int, rows: int = ROWS, cols: int = COLS
) -> int:
    """Heuristic value of dropping Kinito's disc in *col*."""
    trial = copy.deepcopy(board)
    placed = drop_disc(trial, col, KINITO, rows, cols)
    if placed is None:
        return -10_000
    row, c = placed
    score = _center_weight(c, cols) * 2
    score += _adjacent_score(trial, row, c, KINITO, rows, cols)
    # Prefer setting up an immediate threat the opponent must answer.
    if winning_column(trial, KINITO, rows, cols) is not None:
        score += 12
    # Discourage lonely vertical towers that gift diagonal setups.
    own_in_col = sum(1 for r in range(rows) if board[r][c] == KINITO)
    if own_in_col >= 1:
        score -= own_in_col * 2
    return score


def choose_ai_column(
    board: list[list[str]], rng: random.Random | None = None,
    rows: int = ROWS, cols: int = COLS,
) -> int:
    """Pick a column: win, block, then scored safe move with light randomness."""
    source = rng or random
    win = winning_column(board, KINITO, rows, cols)
    if win is not None:
        return win
    block = winning_column(board, PLAYER, rows, cols)
    if block is not None:
        return block

    valid = valid_columns(board, cols)
    if not valid:
        raise ValueError("no valid columns")

    safe = [
        col for col in valid
        if not _gives_opponent_immediate_win(board, col, rows, cols)
    ]
    pool = safe or valid
    scored = [(_score_column(board, col, rows, cols), col) for col in pool]
    best = max(score for score, _ in scored)
    # Near-best ties keep openings varied instead of always stacking center.
    top = [col for score, col in scored if score >= best - 2]
    return source.choice(top)


class ConnectFourGame:
    """6x7 Connect Four: player is purple (L), Kinito is pink (R)."""

    def __init__(self, app):
        self.app = app
        self.rows = ROWS
        self.cols = COLS
        self.board = new_board()
        self.buttons: list[list[Button]] = []
        self.status_label: Label | None = None
        self._board_frame = None
        self._size_var = None
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
            text="Click a column — your turn!",
        )
        self.status_label.pack(pady=8)

        # Board size picker: three options, rebuilds the grid on change.
        size_row = Frame(main)
        size_row.pack(pady=(0, 6))
        self._size_var = tk.StringVar(value=BOARD_SIZES[0][0])
        for label, cols, rows in BOARD_SIZES:
            tk.Radiobutton(
                size_row,
                text=label,
                value=label,
                variable=self._size_var,
                command=lambda c=cols, r=rows: self._set_size(c, r),
            ).pack(side=tk.LEFT, padx=6)

        self._board_frame = Frame(main)
        self._board_frame.pack(fill=tk.BOTH, expand=True)
        self._build_board()

        Button(main, text="New Game", command=self._reset).pack(pady=(0, 10))
        self.app._connect_four_game = self
        self.window.bind("<Destroy>", self._on_destroy)

    def _set_size(self, cols: int, rows: int):
        """Switch to a new board size and start a fresh board."""
        self.cols = cols
        self.rows = rows
        self._reset()

    def _build_board(self):
        """(Re)build the grid of cell buttons for the current size."""
        for child in self._board_frame.winfo_children():
            child.destroy()
        grid = create_uniform_grid(
            self._board_frame, self.rows, self.cols, uniform="connect_four"
        )
        mark_font = ("Segoe UI Symbol", 18, "bold")
        self.buttons = []
        for row in range(self.rows):
            row_buttons: list[Button] = []
            for col in range(self.cols):
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
        if self.window is not None:
            self.window.geometry(
                f"{self.cols * 56 + 40}x{self.rows * 56 + 160}"
            )

    def _on_destroy(self, event):
        if event.widget is self.window and getattr(
            self.app, "_connect_four_game", None
        ) is self:
            self.app._connect_four_game = None

    def refresh_player_colors(self) -> None:
        """Recolor every placed player disc (called when the color setting changes)."""
        for row in range(self.rows):
            for col in range(self.cols):
                if self.board[row][col] == PLAYER:
                    self._refresh_cell(row, col)

    def _reset(self):
        """Start a fresh board."""
        self.board = new_board(self.rows, self.cols)
        self.finished = False
        self._busy = False
        self._build_board()
        if self.status_label:
            self.status_label.config(text="Click a column — your turn!")

    def _player_color(self, col: int | None = None) -> str:
        # Live update path: the Adjust Colors window calls refresh_player_colors().
        getter = getattr(self.app, "connect_four_color", None)
        color = getter() if callable(getter) else PLAYER_COLOR
        if color == RAINBOW_COLOR:
            # Rainbow mode: the disc color is a gradient across the columns.
            return rainbow_at(self.cols - 1 - col if col is not None else 0)
        return color or PLAYER_COLOR

    def _player_bg(self, col: int | None = None) -> str:
        from kinito.colors import lighten_hex

        return lighten_hex(self._player_color(col), 0.85)

    def _refresh_cell(self, row: int, col: int):
        """Update one button to match the board cell."""
        piece = self.board[row][col]
        button = self.buttons[row][col]
        if piece == PLAYER:
            # disabledforeground is required on Windows — fg alone becomes gray.
            color = self._player_color(col)
            button.config(
                text=DISC_MARK,
                fg=color,
                disabledforeground=color,
                bg=self._player_bg(col),
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
        placed = drop_disc(self.board, col, PLAYER, self.rows, self.cols)
        if placed is None:
            return
        row, c = placed
        self._refresh_cell(row, c)

        result = check_winner(self.board, self.rows, self.cols)
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
        col = choose_ai_column(
            self.board, rows=self.rows, cols=self.cols
        )
        placed = drop_disc(self.board, col, KINITO, self.rows, self.cols)
        self._busy = False
        if placed is None:
            if self.status_label:
                self.status_label.config(text="Your turn!")
            return
        row, c = placed
        self._refresh_cell(row, c)

        result = check_winner(self.board, self.rows, self.cols)
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
            line = game_lines.pick_game_line(self.app, game_lines.CONNECT_FOUR_PLAYER_WIN_LINES, "win")
            status = "You win! Four in a row."
            outcome = "player_win"
        elif result == KINITO:
            line = game_lines.pick_game_line(self.app, game_lines.CONNECT_FOUR_KINITO_WIN_LINES, "lose")
            status = "Kinito wins!"
            outcome = "kinito_win"
        else:
            line = game_lines.pick_game_line(self.app, game_lines.CONNECT_FOUR_DRAW_LINES, "draw")
            status = "Draw! Board is full."
            outcome = "draw"

        if self.status_label:
            self.status_label.config(text=status)
        if hasattr(self.app, "on_game_outcome"):
            self.app.on_game_outcome(outcome)
        self.app.speak_game_line(line)
