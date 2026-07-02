"""Memory card-pair logic and UI."""

import tkinter as tk
from tkinter import Button, Frame, Label

from content import dialogue as dlg
from content import game_lines
from kinito.features.games.base import create_uniform_grid, game_emoji_font, open_game_window
from kinito.features.games.memory import DEFAULT_PAIRS, build_deck, is_match

GRID_SIZE = 4
PAIR_COUNT = len(DEFAULT_PAIRS)
FLIP_BACK_MS = 800
HIDDEN_TEXT = "?"
CARD_WIDTH = 3
CARD_HEIGHT = 2
POST_WIN_MIN_HEIGHT = 580


class MemoryGame:
    """4x4 memory game with emoji card pairs."""

    def __init__(self, app):
        self.app = app
        self.deck = build_deck()
        self.revealed = [False] * len(self.deck)
        self.matched = [False] * len(self.deck)
        self.buttons: list[Button] = []
        self.first_pick: int | None = None
        self.lock_input = False
        self.moves = 0
        self.pairs_found = 0
        self.status_label: Label | None = None
        self.window = None

    def open(self):
        """Open the memory game window."""
        self.window = open_game_window(
            self.app,
            "Memory with Kinito",
            420,
            560,
            min_width=340,
            min_height=480,
        )

        main = Frame(self.window)
        main.pack(fill=tk.BOTH, expand=True)

        Button(main, text="New Game", command=self._reset).pack(
            side=tk.BOTTOM,
            pady=(0, 10),
        )

        self.status_label = Label(main, text="Find all matching pairs!")
        self.status_label.pack(side=tk.TOP, pady=8)

        grid = create_uniform_grid(main, GRID_SIZE, GRID_SIZE, uniform="memory")
        card_font = game_emoji_font(22)

        for index in range(GRID_SIZE * GRID_SIZE):
            row, col = divmod(index, GRID_SIZE)
            button = Button(
                grid,
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

    def _reset(self):
        """Shuffle and restart."""
        self.deck = build_deck()
        self.revealed = [False] * len(self.deck)
        self.matched = [False] * len(self.deck)
        self.first_pick = None
        self.lock_input = False
        self.moves = 0
        self.pairs_found = 0
        for button in self.buttons:
            button.config(text=HIDDEN_TEXT, state="normal")
        if self.status_label:
            self.status_label.config(text="Find all matching pairs!")

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
            if self.pairs_found == PAIR_COUNT:
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
        elif self.pairs_found == PAIR_COUNT // 2:
            self.app.speak_game_line(dlg.pick_line(game_lines.MEMORY_HALF_LINES))

    def _on_win(self):
        """Announce victory."""
        if self.status_label:
            self.status_label.config(text=f"All pairs found in {self.moves} moves!")
        self._expand_window_for_summary()
        line = dlg.pick_line(game_lines.MEMORY_WIN_LINES).format(moves=self.moves)
        self.app.speak_game_line(line)
