"""Tetris game logic (no UI)."""

from __future__ import annotations

import random
from typing import Literal

COLS = 10
ROWS = 20
BASE_DELAY_MS = 500
MIN_DELAY_MS = 80
DELAY_STEP_MS = 40

# Line-clear points (before × level): single, double, triple, tetris.
LINE_SCORES = (0, 100, 300, 500, 800)

Point = tuple[int, int]  # (x, y) with y increasing downward
PieceType = Literal["I", "O", "T", "S", "Z", "J", "L"]

PIECE_TYPES: tuple[PieceType, ...] = ("I", "O", "T", "S", "Z", "J", "L")

# Four clockwise rotations per piece (local offsets).
SHAPES: dict[PieceType, tuple[tuple[Point, ...], ...]] = {
    "I": (
        ((0, 1), (1, 1), (2, 1), (3, 1)),
        ((2, 0), (2, 1), (2, 2), (2, 3)),
        ((0, 2), (1, 2), (2, 2), (3, 2)),
        ((1, 0), (1, 1), (1, 2), (1, 3)),
    ),
    "O": (
        ((1, 0), (2, 0), (1, 1), (2, 1)),
        ((1, 0), (2, 0), (1, 1), (2, 1)),
        ((1, 0), (2, 0), (1, 1), (2, 1)),
        ((1, 0), (2, 0), (1, 1), (2, 1)),
    ),
    "T": (
        ((0, 1), (1, 1), (2, 1), (1, 0)),
        ((1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 1), (1, 1), (2, 1), (1, 2)),
        ((1, 0), (1, 1), (1, 2), (0, 1)),
    ),
    "S": (
        ((1, 0), (2, 0), (0, 1), (1, 1)),
        ((1, 0), (1, 1), (2, 1), (2, 2)),
        ((1, 1), (2, 1), (0, 2), (1, 2)),
        ((0, 0), (0, 1), (1, 1), (1, 2)),
    ),
    "Z": (
        ((0, 0), (1, 0), (1, 1), (2, 1)),
        ((2, 0), (1, 1), (2, 1), (1, 2)),
        ((0, 1), (1, 1), (1, 2), (2, 2)),
        ((1, 0), (0, 1), (1, 1), (0, 2)),
    ),
    "J": (
        ((0, 0), (0, 1), (1, 1), (2, 1)),
        ((1, 0), (2, 0), (1, 1), (1, 2)),
        ((0, 1), (1, 1), (2, 1), (2, 2)),
        ((1, 0), (1, 1), (0, 2), (1, 2)),
    ),
    "L": (
        ((2, 0), (0, 1), (1, 1), (2, 1)),
        ((1, 0), (1, 1), (1, 2), (2, 2)),
        ((0, 1), (1, 1), (2, 1), (0, 2)),
        ((0, 0), (1, 0), (1, 1), (1, 2)),
    ),
}

# Guideline-ish neon colors for UI (stored on locked cells).
PIECE_COLORS: dict[PieceType, str] = {
    "I": "#22d3ee",
    "O": "#facc15",
    "T": "#c084fc",
    "S": "#4ade80",
    "Z": "#f87171",
    "J": "#60a5fa",
    "L": "#fb923c",
}

Outcome = Literal["ok", "locked", "dead", "noop"]


def cells_for(piece_type: PieceType, rotation: int, ox: int, oy: int) -> list[Point]:
    """Return absolute board cells for a piece pose."""
    shape = SHAPES[piece_type][rotation % 4]
    return [(ox + x, oy + y) for x, y in shape]


def _refill_bag(state: dict) -> None:
    bag = list(PIECE_TYPES)
    state["rng"].shuffle(bag)
    state["bag"] = bag


def _next_from_bag(state: dict) -> PieceType:
    if not state["bag"]:
        _refill_bag(state)
    return state["bag"].pop()


def _empty_board() -> list[list[str | None]]:
    return [[None for _ in range(COLS)] for _ in range(ROWS)]


def _spawn_x(_piece_type: PieceType) -> int:
    """Horizontal spawn origin so pieces appear roughly centered."""
    return 3


def _collides(state: dict, piece_type: PieceType, rotation: int, ox: int, oy: int) -> bool:
    board: list[list[str | None]] = state["board"]
    for x, y in cells_for(piece_type, rotation, ox, oy):
        if x < 0 or x >= COLS or y >= ROWS:
            return True
        if y < 0:
            continue
        if board[y][x] is not None:
            return True
    return False


def _lock_piece(state: dict) -> None:
    active = state["active"]
    if active is None:
        return
    color = PIECE_COLORS[active["type"]]
    board: list[list[str | None]] = state["board"]
    for x, y in cells_for(active["type"], active["rotation"], active["x"], active["y"]):
        if 0 <= y < ROWS and 0 <= x < COLS:
            board[y][x] = color
    state["active"] = None


def _clear_lines(state: dict) -> int:
    board: list[list[str | None]] = state["board"]
    kept = [row for row in board if any(cell is None for cell in row)]
    cleared = ROWS - len(kept)
    if cleared == 0:
        return 0
    new_rows = [[None for _ in range(COLS)] for _ in range(cleared)]
    state["board"] = new_rows + kept
    return cleared


def _apply_line_score(state: dict, cleared: int) -> None:
    if cleared <= 0:
        return
    points = LINE_SCORES[min(cleared, 4)] * state["level"]
    state["score"] += points
    state["lines"] += cleared
    state["level"] = 1 + state["lines"] // 10


def _spawn(state: dict) -> bool:
    """Spawn next piece as active; pull a new next. Return False if blocked."""
    piece_type: PieceType = state["next_type"]
    state["next_type"] = _next_from_bag(state)
    ox = _spawn_x(piece_type)
    oy = 0
    state["active"] = {
        "type": piece_type,
        "rotation": 0,
        "x": ox,
        "y": oy,
    }
    if _collides(state, piece_type, 0, ox, oy):
        state["alive"] = False
        return False
    return True


def new_game(rng: random.Random | None = None) -> dict:
    """Create a fresh Tetris game with an active piece and next preview."""
    source = rng or random.Random()
    state: dict = {
        "board": _empty_board(),
        "active": None,
        "next_type": "I",
        "bag": [],
        "score": 0,
        "lines": 0,
        "level": 1,
        "alive": True,
        "rng": source,
    }
    _refill_bag(state)
    state["next_type"] = _next_from_bag(state)
    _spawn(state)
    return state


def move(state: dict, dx: int) -> Outcome:
    """Shift the active piece horizontally by *dx*. Return outcome."""
    if not state["alive"] or state["active"] is None:
        return "noop"
    active = state["active"]
    nx = active["x"] + dx
    if _collides(state, active["type"], active["rotation"], nx, active["y"]):
        return "noop"
    active["x"] = nx
    return "ok"


def rotate(state: dict) -> Outcome:
    """Rotate active piece clockwise with simple wall kicks."""
    if not state["alive"] or state["active"] is None:
        return "noop"
    active = state["active"]
    if active["type"] == "O":
        return "noop"
    new_rot = (active["rotation"] + 1) % 4
    ox, oy = active["x"], active["y"]
    kicks = ((0, 0), (-1, 0), (1, 0), (0, -1), (-2, 0), (2, 0), (0, 1))
    for kx, ky in kicks:
        if not _collides(state, active["type"], new_rot, ox + kx, oy + ky):
            active["rotation"] = new_rot
            active["x"] = ox + kx
            active["y"] = oy + ky
            return "ok"
    return "noop"


def soft_drop(state: dict) -> Outcome:
    """Move one cell down; if blocked, lock. Soft-drop awards +1 per cell."""
    if not state["alive"] or state["active"] is None:
        return "noop"
    active = state["active"]
    if not _collides(state, active["type"], active["rotation"], active["x"], active["y"] + 1):
        active["y"] += 1
        state["score"] += 1
        return "ok"
    return _lock_and_continue(state)


def hard_drop(state: dict) -> Outcome:
    """Drop to the bottom instantly; +2 score per cell fallen."""
    if not state["alive"] or state["active"] is None:
        return "noop"
    active = state["active"]
    fallen = 0
    while not _collides(
        state, active["type"], active["rotation"], active["x"], active["y"] + 1
    ):
        active["y"] += 1
        fallen += 1
    state["score"] += fallen * 2
    return _lock_and_continue(state)


def _lock_and_continue(state: dict) -> Outcome:
    _lock_piece(state)
    cleared = _clear_lines(state)
    _apply_line_score(state, cleared)
    if not _spawn(state):
        return "dead"
    return "locked"


def step(state: dict) -> Outcome:
    """Gravity tick: move down one cell, or lock if blocked."""
    if not state["alive"]:
        return "dead"
    if state["active"] is None:
        return "dead"
    active = state["active"]
    if not _collides(state, active["type"], active["rotation"], active["x"], active["y"] + 1):
        active["y"] += 1
        return "ok"
    return _lock_and_continue(state)


def tick_delay_ms(level: int) -> int:
    """Return gravity delay in ms; faster as level rises, floored at minimum."""
    level = max(1, int(level))
    delay = BASE_DELAY_MS - (level - 1) * DELAY_STEP_MS
    return max(MIN_DELAY_MS, delay)


def active_cells(state: dict) -> list[Point]:
    """Return absolute cells of the active piece, or empty if none."""
    active = state.get("active")
    if not active:
        return []
    return cells_for(active["type"], active["rotation"], active["x"], active["y"])
