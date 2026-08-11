"""Snake game window with Canvas and after()-driven game loop."""

from __future__ import annotations

import tkinter as tk
from tkinter import Button, Canvas, Frame, Label

from content import dialogue as dlg
from content import game_lines
from kinito.features.games.base import open_game_window
from kinito.features.games.snake import (
    DOWN,
    GRID_SIZE,
    LEFT,
    RIGHT,
    UP,
    new_game,
    queue_direction,
    step,
    tick_delay_ms,
)

CELL_PX = 22
PAD = 2
BG_COLOR = "#1a1a2e"
GRID_COLOR = "#16213e"
SNAKE_HEAD = "#4ade80"
SNAKE_BODY = "#22c55e"
FOOD_COLOR = "#f87171"
DEAD_COLOR = "#94a3b8"


class SnakeGame:
    """Classic snake: arrow keys / WASD, score, session highscore, New Game."""

    def __init__(self, app):
        self.app = app
        self.state = new_game()
        self.highscore = 0
        self.window = None
        self.canvas: Canvas | None = None
        self.status_label: Label | None = None
        self._running = False
        self._after_id = None
        self._announced_game_over = False

    def open(self):
        """Open the snake game window and start the loop."""
        canvas_size = GRID_SIZE * CELL_PX + PAD * 2
        self.window = open_game_window(
            self.app,
            "Snake with Kinito",
            canvas_size + 40,
            canvas_size + 120,
            min_width=canvas_size + 20,
            min_height=canvas_size + 100,
        )

        main = Frame(self.window)
        main.pack(fill=tk.BOTH, expand=True)

        self.status_label = Label(main, text=self._status_text())
        self.status_label.pack(side=tk.TOP, pady=8)

        self.canvas = Canvas(
            main,
            width=canvas_size,
            height=canvas_size,
            bg=BG_COLOR,
            highlightthickness=0,
        )
        self.canvas.pack(padx=10, pady=5)

        Button(main, text="New Game", command=self._reset).pack(side=tk.BOTTOM, pady=(0, 10))

        self.window.bind("<KeyPress>", self._on_key)
        self.canvas.bind("<KeyPress>", self._on_key)
        self.window.focus_force()
        self.canvas.focus_set()

        original_close = getattr(self.window, "_kinito_close", None)

        def on_close():
            self._stop_loop()
            if original_close:
                original_close()

        self.window.protocol("WM_DELETE_WINDOW", on_close)
        self.window._kinito_close = on_close

        self._draw()
        self._start_loop()

    def _status_text(self) -> str:
        if not self.state["alive"]:
            return (
                f"Game over! Score: {self.state['score']}. "
                f"Highscore: {self.highscore}. New Game to retry!"
            )
        return f"Score: {self.state['score']}  |  Highscore: {self.highscore}"

    def _on_key(self, event):
        key = event.keysym.lower()
        mapping = {
            "up": UP,
            "w": UP,
            "down": DOWN,
            "s": DOWN,
            "left": LEFT,
            "a": LEFT,
            "right": RIGHT,
            "d": RIGHT,
        }
        direction = mapping.get(key)
        if direction:
            queue_direction(self.state, *direction)

    def _start_loop(self):
        self._running = True
        self._schedule_tick()

    def _stop_loop(self):
        self._running = False
        if self._after_id is not None and self.window is not None:
            try:
                self.window.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None

    def _schedule_tick(self):
        if not self._running or self.window is None:
            return
        delay = tick_delay_ms(self.state["score"])
        self._after_id = self.window.after(delay, self._tick)

    def _tick(self):
        self._after_id = None
        if not self._running or self.window is None:
            return
        try:
            if not self.window.winfo_exists():
                self._running = False
                return
        except tk.TclError:
            self._running = False
            return

        if not self.state["alive"]:
            return

        result = step(self.state)
        self._draw()
        if self.status_label:
            self.status_label.config(text=self._status_text())

        if result == "dead":
            self._on_game_over()
            return

        self._schedule_tick()

    def _on_game_over(self):
        """Update highscore once and let Kinito comment."""
        if self._announced_game_over:
            return
        self._announced_game_over = True
        score = self.state["score"]
        is_new_high = score > self.highscore
        if is_new_high:
            self.highscore = score
        if self.status_label:
            self.status_label.config(text=self._status_text())

        if is_new_high and score > 0:
            line = dlg.pick_line(game_lines.SNAKE_NEW_HIGH_LINES).format(
                score=score,
                highscore=self.highscore,
            )
            outcome = "player_win"
        else:
            line = dlg.pick_line(game_lines.SNAKE_GAME_OVER_LINES).format(
                score=score,
                highscore=self.highscore,
            )
            outcome = "draw"
        if hasattr(self.app, "on_game_outcome"):
            self.app.on_game_outcome(outcome)
        self.app.speak_game_line(line)

    def _reset(self):
        """Start a fresh round; keep session highscore."""
        self._stop_loop()
        self.state = new_game()
        self._announced_game_over = False
        if self.status_label:
            self.status_label.config(text=self._status_text())
        self._draw()
        self._start_loop()
        if self.window is not None:
            self.window.focus_force()
            if self.canvas is not None:
                self.canvas.focus_set()

    def _cell_rect(self, x: int, y: int) -> tuple[int, int, int, int]:
        left = PAD + x * CELL_PX
        top = PAD + y * CELL_PX
        return left + 1, top + 1, left + CELL_PX - 1, top + CELL_PX - 1

    def _draw(self):
        if self.canvas is None:
            return
        self.canvas.delete("all")
        size = GRID_SIZE * CELL_PX + PAD * 2
        self.canvas.create_rectangle(0, 0, size, size, fill=BG_COLOR, outline=GRID_COLOR)

        food = self.state["food"]
        self.canvas.create_oval(
            *self._cell_rect(*food),
            fill=FOOD_COLOR,
            outline="",
        )

        body_color = SNAKE_BODY if self.state["alive"] else DEAD_COLOR
        head_color = SNAKE_HEAD if self.state["alive"] else DEAD_COLOR
        for index, (x, y) in enumerate(self.state["snake"]):
            color = head_color if index == 0 else body_color
            self.canvas.create_rectangle(
                *self._cell_rect(x, y),
                fill=color,
                outline="",
            )
