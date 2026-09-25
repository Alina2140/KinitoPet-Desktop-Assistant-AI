"""Memory card-pair logic and UI."""

import tkinter as tk
from tkinter import Button, Frame, Label

from content import dialogue as dlg
from content import game_lines
from kinito.features.games.base import create_uniform_grid, game_emoji_font, open_game_window
from kinito.features.games.memory import (
    PAIR_OPTIONS,
    build_deck,
    grid_shape,
    is_match,
    normalize_pair_count,
    select_pairs,
)

FLIP_BACK_MS = 800
HIDDEN_TEXT = "?"
CARD_WIDTH = 3
CARD_HEIGHT = 2
POST_WIN_MIN_HEIGHT = 580


class MemoryGame:
    """Memory game with a configurable number of emoji card pairs."""

    def __init__(self, app, pair_count: int | None = None):
        self.app = app
        self.pair_count = normalize_pair_count(pair_count)
        self.deck = build_deck(select_pairs(self.pair_count))
        self.revealed = [False] * len(self.deck)
        self.matched = [False] * len(self.deck)
        self.buttons: list[Button] = []
        self.first_pick: int | None = None
        self.lock_input = False
        self.moves = 0
        self.pairs_found = 0
        self.status_label: Label | None = None
        self.grid_frame: Frame | None = None
        self.main_frame: Frame | None = None
        self.pair_buttons: dict[int, Button] = {}
        self.window = None
        self.best_moves: int | None = None
        self._refresh_best_moves()

    def _refresh_best_moves(self) -> None:
        """Load the persistent best for the current pair-count category."""
        scores = self.app.game_scores() if hasattr(self.app, "game_scores") else None
        self.best_moves = (
            scores.memory_best_moves(self.pair_count) if scores is not None else None
        )

    def open(self):
        """Open the memory game window."""
        rows, cols = grid_shape(self.pair_count)
        width = max(360, 90 * cols + 80)
        height = max(420, 90 * rows + 160)
        self.window = open_game_window(
            self.app,
            "Memory with Kinito",
            width,
            height,
            min_width=max(300, width - 80),
            min_height=max(360, height - 80),
        )

        self.main_frame = Frame(self.window)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        footer = Frame(self.main_frame)
        footer.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 10), padx=10)
        Label(footer, text="PAIRS:", font=("Arial", 9)).pack(side=tk.LEFT)
        for value in PAIR_OPTIONS:
            button = Button(
                footer,
                text=str(value),
                width=3,
                relief=tk.FLAT,
                font=("Arial", 9, "bold" if value == self.pair_count else "normal"),
                command=lambda n=value: self._set_pair_count(n),
            )
            button.pack(side=tk.LEFT, padx=1)
            self.pair_buttons[value] = button
        Button(footer, text="New Game", command=self._reset).pack(side=tk.RIGHT)

        self.status_label = Label(self.main_frame, text=self._status_idle_text())
        self.status_label.pack(side=tk.TOP, pady=8)

        self._build_grid()

    def _build_grid(self):
        """Create or recreate the card button grid for the current pair count."""
        if self.grid_frame is not None:
            self.grid_frame.destroy()
            self.grid_frame = None
        self.buttons.clear()

        rows, cols = grid_shape(self.pair_count)
        self.grid_frame = create_uniform_grid(
            self.main_frame,
            rows,
            cols,
            uniform="memory",
        )
        card_font = game_emoji_font(22)

        for index in range(rows * cols):
            row, col = divmod(index, cols)
            button = Button(
                self.grid_frame,
                text=HIDDEN_TEXT,
                font=card_font,
                width=CARD_WIDTH,
                height=CARD_HEIGHT,
                anchor="center",
                justify="center",
                command=lambda i=index: self._flip_card(i),
            )
            button.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
            self.buttons.append(button)

    def _status_idle_text(self) -> str:
        if self.best_moves is None:
            return f"Find all {self.pair_count} matching pairs!"
        return f"Find all {self.pair_count} pairs!  Best: {self.best_moves} moves"

    def _expand_window_for_summary(self):
        """Grow the window after a win so status text and controls stay visible."""
        if not self.window or not self.window.winfo_exists():
            return
        try:
            self.window.update_idletasks()
            width = max(self.window.winfo_width(), 420)
            height = max(self.window.winfo_height(), POST_WIN_MIN_HEIGHT)
            x = self.window.winfo_x()
            y = self.window.winfo_y()
            self.window.geometry(f"{width}x{height}+{x}+{y}")
        except tk.TclError:
            pass

    def _set_pair_count(self, pair_count: int) -> None:
        """Switch board size and start a fresh game."""
        count = normalize_pair_count(pair_count)
        if count == self.pair_count and self.pairs_found == 0 and self.moves == 0:
            return
        self.pair_count = count
        for value, button in self.pair_buttons.items():
            button.config(font=("Arial", 9, "bold" if value == self.pair_count else "normal"))
        self._refresh_best_moves()
        self._reset(rebuild_grid=True)

    def _reset(self, *, rebuild_grid: bool = False):
        """Shuffle and restart."""
        self.deck = build_deck(select_pairs(self.pair_count))
        self.revealed = [False] * len(self.deck)
        self.matched = [False] * len(self.deck)
        self.first_pick = None
        self.lock_input = False
        self.moves = 0
        self.pairs_found = 0
        if rebuild_grid or len(self.buttons) != len(self.deck):
            self._build_grid()
        else:
            for button in self.buttons:
                button.config(text=HIDDEN_TEXT, state="normal")
        if self.status_label:
            self.status_label.config(text=self._status_idle_text())

    def _flip_card(self, index: int):
        """Reveal a card at *index*."""
        if self.lock_input or self.matched[index] or self.revealed[index]:
            return

        self.revealed[index] = True
        self.buttons[index].config(text=self.deck[index])

        if self.first_pick is None:
            self.first_pick = index
            return

        self.moves += 1
        first = self.first_pick
        second = index
        self.first_pick = None

        if is_match(self.deck[first], self.deck[second]):
            self.matched[first] = True
            self.matched[second] = True
            self.buttons[first].config(state="disabled")
            self.buttons[second].config(state="disabled")
            self.pairs_found += 1
            self._on_pair_found()
            if self.pairs_found == self.pair_count:
                self._on_win()
            return

        self.lock_input = True
        self.window.after(
            FLIP_BACK_MS,
            lambda: self._hide_pair(first, second),
        )

    def _hide_pair(self, first: int, second: int):
        """Hide two non-matching cards."""
        if not self.window or not self.window.winfo_exists():
            return
        self.revealed[first] = False
        self.revealed[second] = False
        self.buttons[first].config(text=HIDDEN_TEXT)
        self.buttons[second].config(text=HIDDEN_TEXT)
        self.lock_input = False

    def _on_pair_found(self):
        """Comment on pair milestones."""
        if self.pairs_found == 1:
            self.app.speak_game_line(dlg.pick_line(game_lines.MEMORY_FIRST_PAIR_LINES))
        elif self.pairs_found == self.pair_count // 2:
            self.app.speak_game_line(dlg.pick_line(game_lines.MEMORY_HALF_LINES))

    def _on_win(self):
        """Announce victory and update the persistent best-move record."""
        is_new_best = False
        if hasattr(self.app, "game_scores"):
            is_new_best = self.app.game_scores().record_memory_moves(
                self.moves, self.pair_count
            )
            self.best_moves = self.app.game_scores().memory_best_moves(self.pair_count)
        elif self.best_moves is None or self.moves < self.best_moves:
            self.best_moves = self.moves
            is_new_best = True

        best = self.best_moves if self.best_moves is not None else self.moves
        if self.status_label:
            if is_new_best:
                self.status_label.config(
                    text=f"New best! {self.moves} moves (previous best beaten)"
                )
            else:
                self.status_label.config(
                    text=f"All pairs found in {self.moves} moves! Best: {best}"
                )
        self._expand_window_for_summary()
        if is_new_best:
            line = dlg.pick_line(game_lines.MEMORY_NEW_BEST_LINES).format(
                moves=self.moves,
                best=best,
            )
        else:
            line = dlg.pick_line(game_lines.MEMORY_WIN_LINES).format(
                moves=self.moves,
                best=best,
            )
        if hasattr(self.app, "on_game_outcome"):
            self.app.on_game_outcome("player_win")
        self.app.speak_game_line(line)
