"""Snake game logic (no UI)."""

from __future__ import annotations

import random
from typing import Literal

GRID_SIZE = 16
START_LENGTH = 3
BASE_DELAY_MS = 160
MIN_DELAY_MS = 95
DELAY_STEP_MS = 8

Direction = tuple[int, int]
Point = tuple[int, int]

UP: Direction = (0, -1)
DOWN: Direction = (0, 1)
LEFT: Direction = (-1, 0)
RIGHT: Direction = (1, 0)


def _spawn_food(snake: list[Point], rng: random.Random) -> Point:
    """Pick a random empty cell for food."""
    occupied = set(snake)
    free = [
        (x, y)
        for x in range(GRID_SIZE)
        for y in range(GRID_SIZE)
        if (x, y) not in occupied
    ]
    if not free:
        return snake[0]
    return rng.choice(free)


def new_game(rng: random.Random | None = None) -> dict:
    """Create a new snake game state with a short snake in the center."""
    source = rng or random
    mid = GRID_SIZE // 2
    snake: list[Point] = [(mid - i, mid) for i in range(START_LENGTH)]
    return {
        "snake": snake,
        "direction": RIGHT,
        "pending_direction": RIGHT,
        "food": _spawn_food(snake, source),
        "score": 0,
        "alive": True,
        "grew": False,
        "rng": source,
    }


def queue_direction(state: dict, dx: int, dy: int) -> bool:
    """Queue a new direction if it is not a 180-degree turn. Return True if queued."""
    if not state["alive"]:
        return False
    if (dx, dy) not in (UP, DOWN, LEFT, RIGHT):
        return False
    current = state["direction"]
    if (dx, dy) == (-current[0], -current[1]):
        return False
    state["pending_direction"] = (dx, dy)
    return True


def step(state: dict) -> Literal["ok", "ate", "dead"]:
    """Advance one tick. Mutates *state* and returns the outcome."""
    if not state["alive"]:
        return "dead"

    state["direction"] = state["pending_direction"]
    dx, dy = state["direction"]
    head_x, head_y = state["snake"][0]
    new_head = (head_x + dx, head_y + dy)

    if not (0 <= new_head[0] < GRID_SIZE and 0 <= new_head[1] < GRID_SIZE):
        state["alive"] = False
        state["grew"] = False
        return "dead"

    body = state["snake"]
    will_eat = new_head == state["food"]
    # Tail vacates unless we grow — allow moving into the current tail cell.
    collision_body = body if will_eat else body[:-1]
    if new_head in collision_body:
        state["alive"] = False
        state["grew"] = False
        return "dead"

    body.insert(0, new_head)
    if will_eat:
        state["score"] += 1
        state["grew"] = True
        state["food"] = _spawn_food(body, state["rng"])
        return "ate"

    body.pop()
    state["grew"] = False
    return "ok"


def tick_delay_ms(score: int) -> int:
    """Return the game-loop delay in ms; faster as score rises, floored at minimum."""
    delay = BASE_DELAY_MS - score * DELAY_STEP_MS
    return max(MIN_DELAY_MS, delay)
