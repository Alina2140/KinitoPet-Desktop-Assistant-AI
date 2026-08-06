"""Minesweeper game logic (9x9, 10 mines) — no UI."""

from __future__ import annotations

import random
from collections import deque
from typing import Literal

ROWS = 9
COLS = 9
MINE_COUNT = 10
CELL_COUNT = ROWS * COLS

RevealResult = Literal["ok", "ignored", "lose", "win"]


def _neighbors(index: int) -> list[int]:
    """Return neighboring cell indices for *index*."""
    row, col = divmod(index, COLS)
    result: list[int] = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            r, c = row + dr, col + dc
            if 0 <= r < ROWS and 0 <= c < COLS:
                result.append(r * COLS + c)
    return result


def new_game() -> dict:
    """Create an empty board; mines are placed on the first reveal."""
    return {
        "mines": set(),
        "revealed": set(),
        "flags": set(),
        "started": False,
        "finished": False,
        "won": False,
    }


def ensure_mines(
    state: dict,
    safe_index: int,
    rng: random.Random | None = None,
) -> None:
    """Place mines after the first click, avoiding *safe_index* and its neighbors."""
    if state["started"]:
        return
    source = rng or random
    forbidden = {safe_index, *_neighbors(safe_index)}
    candidates = [i for i in range(CELL_COUNT) if i not in forbidden]
    # If the safe zone is huge, fall back to excluding only the click cell.
    if len(candidates) < MINE_COUNT:
        candidates = [i for i in range(CELL_COUNT) if i != safe_index]
    state["mines"] = set(source.sample(candidates, MINE_COUNT))
    state["started"] = True


def neighbor_count(state: dict, index: int) -> int:
    """Return how many mines surround *index*."""
    return sum(1 for n in _neighbors(index) if n in state["mines"])


def remaining_mines(state: dict) -> int:
    """Return mine count minus current flags (for the status display)."""
    return MINE_COUNT - len(state["flags"])


def toggle_flag(state: dict, index: int) -> bool:
    """Toggle a flag on *index*. Return True if the flags set changed."""
    if state["finished"] or index in state["revealed"]:
        return False
    if index in state["flags"]:
        state["flags"].remove(index)
    else:
        state["flags"].add(index)
    return True


def _check_win(state: dict) -> bool:
    """Return True when every non-mine cell is revealed."""
    return len(state["revealed"]) == CELL_COUNT - len(state["mines"])


def reveal_cell(
    state: dict,
    index: int,
    rng: random.Random | None = None,
) -> RevealResult:
    """Reveal *index* (and flood-fill zeros). Return outcome."""
    if state["finished"]:
        return "ignored"
    if index < 0 or index >= CELL_COUNT:
        return "ignored"
    if index in state["revealed"] or index in state["flags"]:
        return "ignored"

    ensure_mines(state, index, rng)

    if index in state["mines"]:
        state["revealed"].add(index)
        state["finished"] = True
        state["won"] = False
        return "lose"

    queue: deque[int] = deque([index])
    while queue:
        current = queue.popleft()
        if current in state["revealed"] or current in state["mines"]:
            continue
        if current in state["flags"]:
            continue
        state["revealed"].add(current)
        if neighbor_count(state, current) == 0:
            for neighbor in _neighbors(current):
                if neighbor not in state["revealed"] and neighbor not in state["mines"]:
                    queue.append(neighbor)

    if _check_win(state):
        state["finished"] = True
        state["won"] = True
        return "win"
    return "ok"
