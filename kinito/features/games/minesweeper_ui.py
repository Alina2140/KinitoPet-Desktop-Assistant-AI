"""Minesweeper game window styled after the classic Windows game."""

from __future__ import annotations

import tkinter as tk
from tkinter import Button, Frame, Label

from content import game_lines
from kinito.features.games.base import open_game_window
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

BG = "#c0c0c0"
PANEL_BG = "#bdbdbd"
FLAG = "F"
FLAG_COLOR = "#ff0000"
MINE = "*"
HIDDEN = ""

# Classic Minesweeper digit colors.
NUMBER_COLORS = {
    1: "#0000ff",
    2: "#008000",
    3: "#ff0000",
    4: "#000080",
    5: "#800000",
    6: "#008080",
    7: "#000000",
    8: "#808080",
}

CELL_FONT = ("Courier New", 13, "bold")
LED_FONT = ("Courier", 16, "bold")
SMILEY_FONT = ("Segoe UI Emoji", 12)
SMILEY_PLAYING = "🙂"
SMILEY_WIN = "😎"
SMILEY_LOSE = "😵"


def _led(parent, width: int = 3) -> Label:
    """Return a red-on-black seven-segment-style counter label."""
    led = Label(
        parent,
        text="0" * width,
        font=LED_FONT,
        fg="#ff0000",
        bg="#000000",
        padx=4,
        pady=0,
    )
    return led


CELL_PX = 26  # fixed pixel size of one board cell's inner tile


def _tile_image(master, size: int, with_flag: bool) -> tk.PhotoImage | None:
    """Return a *size* px grey tile; with_flag draws the classic red flag."""
    try:
        from PIL import Image, ImageDraw, ImageTk

        tile = Image.new("RGBA", (size, size), BG)
        if with_flag:
            draw = ImageDraw.Draw(tile)
            c = size // 2
            pole_w = max(2, int(size * 0.07))
            top = int(size * 0.10)
            bottom = int(size * 0.82)
            # Pole.
            draw.line((c, top, c, bottom), fill="#000000", width=pole_w)
            # Red triangular flag pointing right from the top of the pole.
            flag_w = int(size * 0.42)
            flag_h = int(size * 0.30)
            draw.polygon(
                [(c, top), (c + flag_w, top + flag_h // 2), (c, top + flag_h)],
                fill="#ff0000",
            )
            # Base.
            base_w = int(size * 0.42)
            draw.rectangle(
                (c - base_w // 2, bottom, c + base_w // 2, bottom + pole_w),
                fill="#000000",
            )
        return ImageTk.PhotoImage(tile, master=master)
    except Exception:
        return None


def _mine_tile_image(master, size: int) -> tk.PhotoImage | None:
    """Return a *size* px tile with a drawn classic mine (ball + spikes)."""
    try:
        from PIL import Image, ImageDraw, ImageTk

        tile = Image.new("RGBA", (size, size), BG)
        draw = ImageDraw.Draw(tile)
        c = size // 2
        r = int(size * 0.30)
        spike = int(size * 0.16)
        w = max(2, int(size * 0.06))
        black = "#000000"
        # Spikes: vertical, horizontal, both diagonals.
        draw.line((c, c - r - spike, c, c + r + spike), fill=black, width=w)
        draw.line((c - r - spike, c, c + r + spike, c), fill=black, width=w)
        draw.line(
            (c - r - spike + 2, c - r - spike + 2, c + r + spike - 2, c + r + spike - 2),
            fill=black,
            width=w,
        )
        draw.line(
            (c - r - spike + 2, c + r + spike - 2, c + r + spike - 2, c - r - spike + 2),
            fill=black,
            width=w,
        )
        draw.ellipse((c - r, c - r, c + r, c + r), fill=black)
        hl = max(2, int(size * 0.10))
        draw.ellipse(
            (c - r + hl // 2, c - r + hl // 2, c - r + hl, c - r + hl), fill="#ffffff"
        )
        return ImageTk.PhotoImage(tile, master=master)
    except Exception:
        return None


class MinesweeperGame:
    """16x16 minesweeper: left-click reveal, right-click flag, smiley to reset."""

    def __init__(self, app):
        self.app = app
        self.state = new_game()
        self.buttons: list[Button] = []
        self.mine_led: Label | None = None
        self.timer_led: Label | None = None
        self.smiley: Button | None = None
        self.status_label: Label | None = None
        self.window = None
        self._flag_image: tk.PhotoImage | None = None
        self._mine_image: tk.PhotoImage | None = None
        self._blank_image: tk.PhotoImage | None = None
        self._ended = False
        self._seconds = 0
        self._timer_job = None

    def open(self):
        """Open the minesweeper game window."""
        self.window = open_game_window(
            self.app,
            "Minesweeper with Kinito",
            560,
            640,
            min_width=480,
            min_height=560,
        )
        self.window.configure(bg=BG)
        self._blank_image = _tile_image(self.window, CELL_PX, with_flag=False)
        self._flag_image = _tile_image(self.window, CELL_PX, with_flag=True)
        self._mine_image = _mine_tile_image(self.window, CELL_PX)

        # Scrollable container: the board can exceed the window when shrunk.
        scroller = tk.Canvas(self.window, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.window, orient="vertical", command=scroller.yview)
        scroller.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        scroller.pack(side="left", fill="both", expand=True)
        outer = Frame(scroller, bg=BG, bd=6, relief=tk.RAISED)
        outer_window = scroller.create_window((0, 0), window=outer, anchor="nw")

        def _sync_scroll_region(_event=None):
            scroller.configure(scrollregion=scroller.bbox("all"))
            scroller.itemconfigure(outer_window, width=scroller.winfo_width())

        outer.bind("<Configure>", _sync_scroll_region)
        scroller.bind("<Configure>", _sync_scroll_region)

        def _on_mousewheel(event):
            scroller.yview_scroll(int(-1 * (event.delta / 120)) or 1, "units")

        self.window.bind_all("<MouseWheel>", _on_mousewheel, add="+")

        def _on_destroy(event):
            if event.widget is self.window:
                try:
                    self.window.unbind_all("<MouseWheel>")
                except tk.TclError:
                    pass

        self.window.bind("<Destroy>", _on_destroy)

        # Header: sunken panel with mine counter, smiley, timer — like the original.
        header = Frame(outer, bg=BG, bd=3, relief=tk.SUNKEN)
        header.pack(fill=tk.X, padx=4, pady=(4, 6))

        header.columnconfigure(1, weight=1)
        self.mine_led = _led(header)
        self.mine_led.grid(row=0, column=0, padx=6, pady=3, sticky="w")

        self.smiley = Button(
            header,
            text=SMILEY_PLAYING,
            font=SMILEY_FONT,
            width=2,
            bd=3,
            relief=tk.RAISED,
            bg=BG,
            activebackground=BG,
            command=self._reset,
        )
        self.smiley.grid(row=0, column=1, pady=1)

        self.timer_led = _led(header)
        self.timer_led.grid(row=0, column=2, padx=6, pady=3, sticky="e")

        # Board: sunken frame of beveled cells.
        board = Frame(outer, bg=BG, bd=3, relief=tk.SUNKEN)
        board.pack(pady=(0, 4))
        for index in range(ROWS * COLS):
            row, col = divmod(index, COLS)
            button = Button(
                board,
                text=HIDDEN,
                font=CELL_FONT,
                image=self._blank_image,
                compound="center",
                bd=3,
                relief=tk.RAISED,
                bg=BG,
                activebackground=BG,
                disabledforeground="black",
                command=lambda i=index: self._on_left_click(i),
            )
            button.grid(row=row, column=col)
            button.bind("<Button-3>", lambda event, i=index: self._on_right_click(i))
            button.bind("<Control-Button-1>", lambda event, i=index: self._on_right_click(i))
            self.buttons.append(button)

        self.status_label = Label(
            outer,
            text="Left-click open, right-click flag — click the face to restart.",
            bg=BG,
            fg="#404040",
            font=("Segoe UI", 8),
        )
        self.status_label.pack(side=tk.BOTTOM, pady=(0, 2))

        self._refresh_counters()
        self._tick_timer()

    def _tick_timer(self):
        if self.window is None:
            return
        try:
            if not self.window.winfo_exists():
                return
        except tk.TclError:
            return
        if not self.state["finished"]:
            self._seconds = min(999, self._seconds + 1)
            self._set_led(self.timer_led, self._seconds)
        self._timer_job = self.window.after(1000, self._tick_timer)

    @staticmethod
    def _set_led(led: Label | None, value: int):
        if led is not None:
            led.config(text=f"{max(0, value):03d}")

    def _refresh_counters(self):
        self._set_led(self.mine_led, remaining_mines(self.state))
        self._set_led(self.timer_led, self._seconds)

    def _set_smiley(self, face: str):
        if self.smiley is not None:
            self.smiley.config(text=face)

    def _reset(self):
        """Start a fresh board."""
        self.state = new_game()
        self._ended = False
        self._seconds = 0
        for button in self.buttons:
            button.config(
                text=HIDDEN,
                image=self._blank_image,
                compound="center",
                font=CELL_FONT,
                fg="black",
                disabledforeground="black",
                bg=BG,
                state="normal",
                relief=tk.RAISED,
                bd=3,
            )
        self._set_smiley(SMILEY_PLAYING)
        self._refresh_counters()

    def _refresh_cell(self, index: int):
        button = self.buttons[index]
        if index in self.state["flags"] and index not in self.state["revealed"]:
            if self._flag_image is not None:
                button.config(
                    text="", image=self._flag_image, compound="center", state="normal"
                )
            else:
                button.config(
                    text=FLAG,
                    image=self._blank_image,
                    compound="center",
                    fg=FLAG_COLOR,
                    disabledforeground=FLAG_COLOR,
                    state="normal",
                )
            return
        button.config(image=self._blank_image, compound="center")
        if index not in self.state["revealed"]:
            button.config(
                text=HIDDEN,
                fg="black",
                disabledforeground="black",
                state="normal",
                relief=tk.RAISED,
            )
            return
        # Revealed cells stay enabled so Windows renders their true fg color
        # (disabled buttons draw paler). Clicks on them are ignored anyway.
        if index in self.state["mines"]:
            if self._mine_image is not None:
                button.config(
                    text="",
                    image=self._mine_image,
                    compound="center",
                    state="normal",
                    relief=tk.SOLID,
                    bd=1,
                )
            else:
                button.config(
                    text=MINE,
                    fg="black",
                    state="normal",
                    relief=tk.SOLID,
                    bd=1,
                )
            return
        count = neighbor_count(self.state, index)
        if count == 0:
            button.config(
                text="",
                state="normal",
                relief=tk.SOLID,
                bd=1,
            )
        else:
            color = NUMBER_COLORS.get(count, "black")
            button.config(
                text=str(count),
                fg=color,
                state="normal",
                relief=tk.SOLID,
                bd=1,
            )

    def _refresh_board(self):
        for index in range(ROWS * COLS):
            self._refresh_cell(index)
        self._refresh_counters()

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
            self._set_smiley(SMILEY_WIN)
            line = game_lines.pick_game_line(
                self.app, game_lines.MINESWEEPER_WIN_LINES, "win"
            ).format(mines=MINE_COUNT)
            outcome = "player_win"
        else:
            self._set_smiley(SMILEY_LOSE)
            line = game_lines.pick_game_line(
                self.app, game_lines.MINESWEEPER_LOSE_LINES, "lose"
            )
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
        self._refresh_counters()
        return "break"
