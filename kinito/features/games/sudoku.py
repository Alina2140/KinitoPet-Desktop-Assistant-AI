"""Sudoku game logic (9x9) — no UI."""

from __future__ import annotations

import random
from typing import Literal

SIZE = 9
CELL_COUNT = SIZE * SIZE

DIFFICULTIES = {
    "easy": 45,
    "medium": 35,
    "hard": 28,
}
DEFAULT_DIFFICULTY = "medium"

PlaceResult = Literal["ok", "given", "invalid", "win"]


def _peers(index: int) -> set[int]:
    """Return the indices that share a row, column or box with *index*."""
    row, col = divmod(index, SIZE)
    box_row, box_col = row // 3 * 3, col // 3 * 3
    peers = {row * SIZE + c for c in range(SIZE)}
    peers |= {r * SIZE + col for r in range(SIZE)}
    peers |= {
        (box_row + dr) * SIZE + box_col + dc for dr in range(3) for dc in range(3)
    }
    peers.discard(index)
    return peers


PEERS = [_peers(i) for i in range(CELL_COUNT)]


def _solve_random(grid: list[int], rng: random.Random) -> bool:
    """Fill *grid* with a random valid solution via backtracking."""
    try:
        index = grid.index(0)
    except ValueError:
        return True
    digits = list(range(1, SIZE + 1))
    rng.shuffle(digits)
    for digit in digits:
        if all(grid[p] != digit for p in PEERS[index]):
            grid[index] = digit
            if _solve_random(grid, rng):
                return True
            grid[index] = 0
    return False


def new_solution(rng: random.Random | None = None) -> list[int]:
    """Return a complete, valid Sudoku solution as a flat list of 81 ints."""
    source = rng or random
    grid = [0] * CELL_COUNT
    _solve_random(grid, source)
    return grid


def _count_solutions(grid: list[int], limit: int = 2) -> int:
    """Count solutions of *grid* up to *limit* (0 = empty cell)."""
    try:
        index = grid.index(0)
    except ValueError:
        return 1
    count = 0
    for digit in range(1, SIZE + 1):
        if all(grid[p] != digit for p in PEERS[index]):
            grid[index] = digit
            count += _count_solutions(grid, limit - count)
            grid[index] = 0
            if count >= limit:
                return count
    return count


def new_game(
    difficulty: str = DEFAULT_DIFFICULTY,
    rng: random.Random | None = None,
) -> dict:
    """Create a puzzle: *difficulty* controls how many givens remain."""
    source = rng or random
    target_givens = DIFFICULTIES.get(difficulty, DIFFICULTIES[DEFAULT_DIFFICULTY])
    solution = new_solution(source)

    puzzle = list(solution)
    indices = list(range(CELL_COUNT))
    source.shuffle(indices)
    givens_left = CELL_COUNT
    for index in indices:
        if givens_left <= target_givens:
            break
        saved = puzzle[index]
        puzzle[index] = 0
        if _count_solutions(list(puzzle)) != 1:
            puzzle[index] = saved
        else:
            givens_left -= 1

    givens = {i for i, v in enumerate(puzzle) if v}
    return {
        "solution": solution,
        "givens": givens,
        "grid": puzzle,
        "entries": {},
        "mistakes": 0,
        "finished": False,
        "difficulty": difficulty,
    }


def is_given(state: dict, index: int) -> bool:
    """Return True when *index* is a fixed clue cell."""
    return index in state["givens"]


def cell_value(state: dict, index: int) -> int:
    """Return the displayed value at *index* (0 when empty)."""
    if index in state["entries"]:
        return state["entries"][index]
    return state["grid"][index]


def remaining_empty(state: dict) -> int:
    """Return how many non-given cells are still empty."""
    return CELL_COUNT - len(state["givens"]) - len(state["entries"])


def place(state: dict, index: int, number: int) -> PlaceResult:
    """Place *number* at *index*, strictly checked against the solution."""
    if state["finished"]:
        return "given"
    if index < 0 or index >= CELL_COUNT or index in state["givens"]:
        return "given"
    if not 1 <= number <= SIZE:
        return "invalid"
    if state["solution"][index] != number:
        state["mistakes"] += 1
        return "invalid"
    state["entries"][index] = number
    if remaining_empty(state) == 0:
        state["finished"] = True
        return "win"
    return "ok"


def erase(state: dict, index: int) -> bool:
    """Remove a player entry at *index*. Return True when something changed."""
    if state["finished"] or index in state["givens"]:
        return False
    return state["entries"].pop(index, None) is not None
