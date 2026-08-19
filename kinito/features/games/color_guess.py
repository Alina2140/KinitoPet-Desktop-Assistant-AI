"""Color guessing game logic (What the Hex? style)."""

from __future__ import annotations

import random
from typing import Literal

DIFFICULTIES = (2, 3, 4, 5, 6, 7, 8, 9, 10, 24, 48)
DEFAULT_DIFFICULTY = 9

Status = Literal["playing", "won"]
GuessResult = Literal["wrong", "correct", "ignored"]


def random_hex(rng: random.Random | None = None) -> str:
    """Return a random six-digit hex color string (e.g. ``#A1B2C3``)."""
    source = rng or random.Random()
    value = source.randint(0, 0xFFFFFF)
    return f"#{value:06X}"


def new_round(count: int, rng: random.Random | None = None) -> dict:
    """Create a new round with *count* unique color options."""
    source = rng or random.Random()
    if count not in DIFFICULTIES:
        count = DEFAULT_DIFFICULTY

    colors: list[str] = []
    seen: set[str] = set()
    while len(colors) < count:
        hex_color = random_hex(source)
        if hex_color not in seen:
            seen.add(hex_color)
            colors.append(hex_color)

    target_index = source.randrange(count)
    return {
        "colors": colors,
        "target_index": target_index,
        "target_hex": colors[target_index],
        "status": "playing",
        "removed": set(),
        "count": count,
    }


def apply_guess(state: dict, index: int) -> GuessResult:
    """Apply a guess at *index* and return the outcome."""
    if state["status"] == "won":
        return "ignored"
    if index < 0 or index >= len(state["colors"]):
        return "ignored"
    if index in state["removed"]:
        return "ignored"

    if index == state["target_index"]:
        state["status"] = "won"
        return "correct"

    state["removed"].add(index)
    return "wrong"
