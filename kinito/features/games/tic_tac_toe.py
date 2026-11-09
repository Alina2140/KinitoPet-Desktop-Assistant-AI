"""Tic-tac-toe board logic, AI, and UI."""

import random
import tkinter as tk
from tkinter import Button, Frame, Label

from content import game_lines
from kinito.colors import RAINBOW_COLOR, rainbow_at
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
PLAYER_COLOR = "#7c3aed"
KINITO_COLOR = "#fa96ff"


def check_winner(board: list[str]) -> str | None:
    """Return PLAYER, KINITO, 'draw', or None if the game continues."""
    for a, b, c in WIN_LINES:
        if board[a] != EMPTY and board[a] == board[b] == board[c]:
            return board[a]
    if all(cell != EMPTY for cell in board):
        return "draw"
    return None


def winning_line(board: list[str]) -> tuple[int, int, int] | None:
    """Return the three cell indices of the winning line, if any."""
    for line in WIN_LINES:
        a, b, c = line
        if board[a] != EMPTY and board[a] == board[b] == board[c]:
            return line
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


def _fork_move(board: list[str], player: str) -> int | None:
    """Return a move that creates two winning threats at once, if any."""
    for index in available_moves(board):
        trial = board[:]
        trial[index] = player
        threats = 0
        for follow in available_moves(trial):
            probe = trial[:]
            probe[follow] = player
            if check_winner(probe) == player:
                threats += 1
                if threats >= 2:
                    return index
    return None


def _apply(board: list[str], index: int, player: str) -> list[str]:
    trial = board[:]
    trial[index] = player
    return trial


def choose_ai_move(board: list[str], rng: random.Random | None = None) -> int:
    """Pick a move for Kinito: win, block, fork, then varied heuristics."""
    source = rng or random
    win = winning_move(board, KINITO)
    if win is not None:
        return win
    block = winning_move(board, PLAYER)
    if block is not None:
        return block
    fork = _fork_move(board, KINITO)
    if fork is not None:
        return fork
    if _fork_move(board, PLAYER) is not None:
        killers = [
            move
            for move in available_moves(board)
            if _fork_move(_apply(board, move, KINITO), PLAYER) is None
        ]
        if killers:
            return source.choice(killers)

    empties = available_moves(board)
    if board[4] == EMPTY:
        # Usually take center; sometimes leave it for a less robotic opener.
        if len(empties) == 9 or (len(empties) == 8 and source.random() < 0.75):
            return 4
        if len(empties) < 8:
            return 4

    corners = [i for i in (0, 2, 6, 8) if board[i] == EMPTY]
    sides = [i for i in (1, 3, 5, 7) if board[i] == EMPTY]

    def without_gifting_fork(moves: list[int]) -> list[int]:
        return [
            move
            for move in moves
            if _fork_move(_apply(board, move, KINITO), PLAYER) is None
        ]

    for group in (corners, sides, empties):
        safe = without_gifting_fork(group)
        if safe:
            return source.choice(safe)
    return source.choice(empties)


class TicTacToeGame:
    """3x3 tic-tac-toe window: player is X, Kinito is O."""

    def __init__(self, app):
        self.app = app
        self.board = [EMPTY] * 9
        self.buttons: list[Button] = []
        self.status_label: Label | None = None
        self.finished = False
        self.window = None
        self._strike_overlay = None
        self._strike_cells: tuple[int, int, int] | None = None
        self.app._tic_tac_toe_game = self

    def open(self):
        """Open the game window."""
        self.window = open_game_window(
            self.app,
            "Tic-Tac-Toe with Kinito",
            340,
            420,
            min_width=300,
            min_height=380,
        )

        main = Frame(self.window)
        main.pack(fill=tk.BOTH, expand=True)

        self.status_label = Label(main, text="You are X. Your turn!")
        self.status_label.pack(pady=8)

        grid = create_uniform_grid(main, 3, 3, uniform="ttt")
        mark_font = ("Arial", 34, "bold")

        for row in range(3):
            for col in range(3):
                index = row * 3 + col
                button = Button(
                    grid,
                    text="",
                    font=mark_font,
                    width=2,
                    height=1,
                    anchor="center",
                    justify="center",
                    command=lambda i=index: self._player_move(i),
                )
                button.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
                self.buttons.append(button)

        Button(main, text="New Game", command=self._reset).pack(pady=(0, 10))
        self.window.bind("<Destroy>", self._on_destroy)
        self.window.bind("<Configure>", self._reposition_strike)

    def _reset(self):
        """Start a fresh board."""
        self._hide_strike()
        self.board = [EMPTY] * 9
        self.finished = False
        for button in self.buttons:
            button.config(text="", state="normal")
        if self.status_label:
            self.status_label.config(text="You are X. Your turn!")

    def _on_destroy(self, event):
        if event.widget is self.window:
            self._hide_strike()
        if event.widget is self.window and getattr(
            self.app, "_tic_tac_toe_game", None
        ) is self:
            self.app._tic_tac_toe_game = None

    def _player_color(self, index: int | None = None) -> str:
        # Live update path: the Adjust Colors window calls refresh_player_marks().
        getter = getattr(self.app, "tic_tac_toe_color", None)
        color = getter() if callable(getter) else PLAYER_COLOR
        if color == RAINBOW_COLOR:
            # Rainbow mode: mark colors are a gradient across the board cells.
            return rainbow_at(8 - index if index is not None else 8)
        return color or PLAYER_COLOR

    def refresh_player_marks(self) -> None:
        """Recolor every placed player mark (called when the color setting changes)."""
        for index, cell in enumerate(self.board):
            if cell == PLAYER:
                color = self._player_color(index)
                self.buttons[index].config(fg=color, disabledforeground=color)

    def _player_move(self, index: int):
        """Handle a click on cell *index*."""
        if self.finished or self.board[index] != EMPTY:
            return

        self.board[index] = PLAYER
        color = self._player_color(index)
        self.buttons[index].config(
            text=PLAYER,
            fg=color,
            disabledforeground=color,
            state="disabled",
        )
        result = check_winner(self.board)
        if result:
            self._end_game(result)
            return

        ai_index = choose_ai_move(self.board)
        self.board[ai_index] = KINITO
        self.buttons[ai_index].config(
            text=KINITO,
            fg=KINITO_COLOR,
            disabledforeground=KINITO_COLOR,
            state="disabled",
        )
        result = check_winner(self.board)
        if result:
            self._end_game(result)
        elif self.status_label:
            self.status_label.config(text="Your turn!")

    def _hide_strike(self) -> None:
        """Remove the winning-line overlay if present."""
        self._strike_cells = None
        overlay = self._strike_overlay
        self._strike_overlay = None
        if overlay is not None:
            try:
                overlay.destroy()
            except tk.TclError:
                pass

    def _cell_center(self, index: int, origin_x: int, origin_y: int) -> tuple[int, int]:
        """Return the screen center of cell *index* relative to the grid origin."""
        button = self.buttons[index]
        return (
            button.winfo_rootx() - origin_x + button.winfo_width() // 2,
            button.winfo_rooty() - origin_y + button.winfo_height() // 2,
        )

    def _show_strike(self, cells: tuple[int, int, int]) -> None:
        """Draw a strike line through the winning *cells* via a transparent overlay."""
        self._hide_strike()
        grid = self.buttons[cells[0]].master
        grid.update_idletasks()
        overlay_bg = "#ff00ff"
        try:
            top = tk.Toplevel(self.window)
            top.overrideredirect(True)
            top.wm_attributes("-topmost", True)
            top.wm_attributes("-transparentcolor", overlay_bg)
            canvas = tk.Canvas(top, bg=overlay_bg, highlightthickness=0)
            canvas.pack(fill="both", expand=True)
            self._strike_overlay = top
            self._strike_cells = cells
            self._strike_canvas = canvas
            self._reposition_strike()
        except tk.TclError:
            self._strike_overlay = None
            self._strike_cells = None
            # Fallback without transparency: highlight the winning cells.
            for index in cells:
                self.buttons[index].config(bg="#fde68a")

    def _reposition_strike(self, _event=None) -> None:
        """Keep the strike overlay aligned with the grid when the window moves."""
        overlay = self._strike_overlay
        cells = self._strike_cells
        if overlay is None or cells is None:
            return
        try:
            grid = self.buttons[cells[0]].master
            x0, y0 = grid.winfo_rootx(), grid.winfo_rooty()
            w, h = grid.winfo_width(), grid.winfo_height()
            overlay.geometry(f"{w}x{h}+{x0}+{y0}")
            canvas = getattr(self, "_strike_canvas", None)
            if canvas is not None:
                canvas.delete("all")
                start = self._cell_center(cells[0], x0, y0)
                end = self._cell_center(cells[-1], x0, y0)
                canvas.create_line(
                    *start,
                    *end,
                    fill="#111111",
                    width=7,
                    capstyle=tk.ROUND,
                )
        except tk.TclError:
            self._strike_overlay = None
            self._strike_cells = None

    def _end_game(self, result: str):
        """Announce the outcome and lock the board."""
        self.finished = True
        for button in self.buttons:
            button.config(state="disabled")

        if result == PLAYER:
            line = game_lines.pick_game_line(self.app, game_lines.TTT_PLAYER_WIN_LINES, "win")
            status = "You win!"
            outcome = "player_win"
        elif result == KINITO:
            line = game_lines.pick_game_line(self.app, game_lines.TTT_KINITO_WIN_LINES, "lose")
            status = "Kinito wins!"
            outcome = "kinito_win"
        else:
            line = game_lines.pick_game_line(self.app, game_lines.TTT_DRAW_LINES, "draw")
            status = "Draw!"
            outcome = "draw"

        if result in (PLAYER, KINITO):
            win_cells = winning_line(self.board)
            if win_cells:
                self._show_strike(win_cells)
        if self.status_label:
            self.status_label.config(text=status)
        if hasattr(self.app, "on_game_outcome"):
            self.app.on_game_outcome(outcome)
        self.app.speak_game_line(line)
