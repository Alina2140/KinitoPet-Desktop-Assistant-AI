"""Hangman game logic and UI."""

from __future__ import annotations

import string
import tkinter as tk
from tkinter import Button, Frame, Label
from typing import Literal

from content import dialogue as dlg
from content import game_lines
from content.hangman_words import pick_word
from kinito.features.games.base import open_game_window

MAX_MISSES = 6
Status = Literal["playing", "won", "lost"]

HANGMAN_STAGES: tuple[str, ...] = (
    """
  +---+
  |   |
      |
      |
      |
      |
=======""",
    """
  +---+
  |   |
  O   |
      |
      |
      |
=======""",
    """
  +---+
  |   |
  O   |
  |   |
      |
      |
=======""",
    """
  +---+
  |   |
  O   |
 /|   |
      |
      |
=======""",
    """
  +---+
  |   |
  O   |
 /|\\  |
      |
      |
=======""",
    """
  +---+
  |   |
  O   |
 /|\\  |
 /    |
      |
=======""",
    """
  +---+
  |   |
  O   |
 /|\\  |
 / \\  |
      |
=======""",
)


def new_game(word: str) -> dict:
    """Create a hangman state for *word* (uppercase A–Z)."""
    normalized = word.strip().upper()
    return {
        "word": normalized,
        "revealed": [False] * len(normalized),
        "guessed": set(),
        "misses": 0,
        "status": "playing",
    }


def display_word(state: dict) -> str:
    """Return the masked word, e.g. 'C _ T'."""
    chars = []
    for letter, shown in zip(state["word"], state["revealed"], strict=True):
        chars.append(letter if shown else "_")
    return " ".join(chars)


def apply_guess(state: dict, letter: str) -> Literal["hit", "miss", "repeat", "ignored"]:
    """Apply one letter guess. Mutates *state*. Return the outcome label."""
    if state["status"] != "playing":
        return "ignored"
    ch = letter.strip().upper()
    if len(ch) != 1 or ch not in string.ascii_uppercase:
        return "ignored"
    if ch in state["guessed"]:
        return "repeat"

    state["guessed"].add(ch)
    if ch in state["word"]:
        for index, word_ch in enumerate(state["word"]):
            if word_ch == ch:
                state["revealed"][index] = True
        if all(state["revealed"]):
            state["status"] = "won"
        return "hit"

    state["misses"] += 1
    if state["misses"] >= MAX_MISSES:
        state["status"] = "lost"
        state["revealed"] = [True] * len(state["word"])
    return "miss"


class HangmanGame:
    """Hangman window: curated word, ASCII gallows, A–Z letter buttons."""

    def __init__(self, app):
        self.app = app
        self.used_words: set[str] = set()
        self.state = new_game(self._next_word())
        self.window = None
        self.gallows_label: Label | None = None
        self.word_label: Label | None = None
        self.status_label: Label | None = None
        self.letter_buttons: dict[str, Button] = {}
        self._ended = False

    def _next_word(self) -> str:
        word = pick_word(used=self.used_words)
        self.used_words.add(word)
        if len(self.used_words) >= len(pick_word.__globals__["WORDS"]):
            # Avoid importing WORDS at module top for a tiny helper — use pick_word pool reset.
            from content.hangman_words import WORDS

            if len(self.used_words) >= len(WORDS):
                self.used_words.clear()
                self.used_words.add(word)
        return word

    def open(self):
        """Open the hangman game window."""
        self.window = open_game_window(
            self.app,
            "Hangman with Kinito",
            360,
            400,
            min_width=360,
            min_height=400,
        )

        main = Frame(self.window)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.gallows_label = Label(
            main,
            text=HANGMAN_STAGES[0].strip("\n"),
            font=("Consolas", 12),
            justify="left",
            anchor="w",
        )
        self.gallows_label.pack(pady=(4, 2))

        self.word_label = Label(main, text=display_word(self.state), font=("Arial", 20, "bold"))
        self.word_label.pack(pady=6)

        self.status_label = Label(main, text=self._status_text())
        self.status_label.pack(pady=4)

        letters = Frame(main)
        letters.pack(pady=8)
        for index, ch in enumerate(string.ascii_uppercase):
            button = Button(
                letters,
                text=ch,
                width=3,
                command=lambda c=ch: self._on_letter(c),
            )
            button.grid(row=index // 9, column=index % 9, padx=2, pady=2)
            self.letter_buttons[ch] = button

        Button(main, text="New Game", command=self._reset).pack(pady=(4, 10))

    def _status_text(self) -> str:
        if self.state["status"] == "won":
            return f"You win! The word was {self.state['word']}."
        if self.state["status"] == "lost":
            return f"Game over! The word was {self.state['word']}."
        return f"Misses: {self.state['misses']}/{MAX_MISSES}. Pick a letter!"

    def _refresh(self):
        misses = min(self.state["misses"], MAX_MISSES)
        if self.gallows_label:
            self.gallows_label.config(text=HANGMAN_STAGES[misses].strip("\n"))
        if self.word_label:
            self.word_label.config(text=display_word(self.state))
        if self.status_label:
            self.status_label.config(text=self._status_text())

    def _lock_letters(self):
        for button in self.letter_buttons.values():
            button.config(state="disabled")

    def _on_letter(self, letter: str):
        if self.state["status"] != "playing":
            return
        result = apply_guess(self.state, letter)
        if result == "ignored":
            return
        button = self.letter_buttons.get(letter)
        if button is not None:
            button.config(state="disabled")
        self._refresh()
        if self.state["status"] in ("won", "lost"):
            self._end_game()

    def _end_game(self):
        if self._ended:
            return
        self._ended = True
        self._lock_letters()
        self._refresh()
        word = self.state["word"]
        if self.state["status"] == "won":
            line = dlg.pick_line(game_lines.HANGMAN_WIN_LINES).format(word=word)
            outcome = "player_win"
        else:
            line = dlg.pick_line(game_lines.HANGMAN_LOSE_LINES).format(word=word)
            outcome = "kinito_win"
        if hasattr(self.app, "on_game_outcome"):
            self.app.on_game_outcome(outcome)
        self.app.speak_game_line(line)

    def _reset(self):
        """Start a new round with a fresh word."""
        self.state = new_game(self._next_word())
        self._ended = False
        for _ch, button in self.letter_buttons.items():
            button.config(state="normal")
        self._refresh()
