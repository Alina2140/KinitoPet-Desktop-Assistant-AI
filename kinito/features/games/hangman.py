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

_LETTER_BTN_BG = "#ececec"
_LETTER_BTN_FG = "#111111"
_LETTER_BTN_ACTIVE_BG = "#d4d4d4"
_LETTER_BTN_DISABLED_BG = "#a8a8a8"
_LETTER_BTN_DISABLED_FG = "#5a5a5a"

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


def _resolve_guess_letter(letter: str) -> str | None:
    ch = letter.strip().upper()
    if len(ch) != 1 or ch not in string.ascii_uppercase:
        return None
    return ch


def _score_guess(state: dict, ch: str) -> Literal["hit", "miss"]:
    """Score *ch* after it was reserved in ``guessed``."""
    if ch in state["word"]:
        for index, word_ch in enumerate(state["word"]):
            if word_ch == ch:
                state["revealed"][index] = True
        if all(state["revealed"]):
            state["status"] = "won"
        return "hit"

    if state["misses"] >= MAX_MISSES:
        state["status"] = "lost"
        state["revealed"] = [True] * len(state["word"])
        return "miss"

    state["misses"] += 1
    if state["misses"] >= MAX_MISSES:
        state["misses"] = MAX_MISSES
        state["status"] = "lost"
        state["revealed"] = [True] * len(state["word"])
    return "miss"


def apply_guess(state: dict, letter: str) -> Literal["hit", "miss", "repeat", "ignored"]:
    """Apply one letter guess. Mutates *state*. Return the outcome label."""
    if state["status"] != "playing":
        return "ignored"
    ch = _resolve_guess_letter(letter)
    if ch is None:
        return "ignored"
    if ch in state["guessed"]:
        return "repeat"

    state["guessed"].add(ch)
    return _score_guess(state, ch)


def _style_letter_button(
    button: Button,
    *,
    enabled: bool,
    command=None,
) -> None:
    """Dim used letters via background color (works on Tk builds without disabledbackground)."""
    if enabled:
        options = {
            "state": tk.NORMAL,
            "bg": _LETTER_BTN_BG,
            "fg": _LETTER_BTN_FG,
            "activebackground": _LETTER_BTN_ACTIVE_BG,
            "relief": tk.RIDGE,
            "cursor": "hand2",
        }
        if command is not None:
            options["command"] = command
        button.config(**options)
        return
    button.config(
        state=tk.DISABLED,
        bg=_LETTER_BTN_DISABLED_BG,
        fg=_LETTER_BTN_DISABLED_FG,
        activebackground=_LETTER_BTN_DISABLED_BG,
        relief=tk.SUNKEN,
        cursor="arrow",
    )


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
        self._guess_in_progress = False

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
                relief=tk.RIDGE,
                bd=2,
            )
            _style_letter_button(button, enabled=True)
            button.grid(row=index // 9, column=index % 9, padx=2, pady=2)
            self.letter_buttons[ch] = button

        Button(main, text="New Game", command=self._reset).pack(pady=(4, 10))

    def _status_text(self) -> str:
        if self.state["status"] == "won":
            return f"You win! The word was {self.state['word']}."
        if self.state["status"] == "lost":
            return f"Game over! The word was {self.state['word']}."
        misses = min(int(self.state["misses"]), MAX_MISSES)
        return f"Misses: {misses}/{MAX_MISSES}. Pick a letter!"

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
            _style_letter_button(button, enabled=False)

    def _freeze_active_letters(self) -> None:
        """Disable every unused letter so queued clicks cannot fire mid-guess."""
        for ch, button in self.letter_buttons.items():
            if ch not in self.state["guessed"]:
                button.config(state=tk.DISABLED)

    def _sync_letter_buttons(self) -> None:
        """Refresh letter buttons from game state."""
        for ch, button in self.letter_buttons.items():
            if ch in self.state["guessed"]:
                _style_letter_button(button, enabled=False)
            elif self.state["status"] == "playing":
                _style_letter_button(
                    button,
                    enabled=True,
                    command=lambda c=ch: self._on_letter(c),
                )
            else:
                _style_letter_button(button, enabled=False)

    def _on_letter(self, letter: str):
        if self._guess_in_progress or self.state["status"] != "playing":
            return
        if int(self.state["misses"]) >= MAX_MISSES:
            self.state["status"] = "lost"
            self.state["revealed"] = [True] * len(self.state["word"])
            self._lock_letters()
            self._refresh()
            self._end_game()
            return
        ch = _resolve_guess_letter(letter)
        if ch is None or ch in self.state["guessed"]:
            return

        self._guess_in_progress = True
        self._freeze_active_letters()
        try:
            self.state["guessed"].add(ch)
            _score_guess(self.state, ch)
            self._refresh()
            self._sync_letter_buttons()
            if self.state["status"] in ("won", "lost"):
                self._end_game()
        finally:
            self._guess_in_progress = False

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
        self._guess_in_progress = False
        for ch, button in self.letter_buttons.items():
            _style_letter_button(
                button,
                enabled=True,
                command=lambda c=ch: self._on_letter(c),
            )
        self._refresh()
