"""Mini battleships game logic."""

from __future__ import annotations

import random
from typing import Literal

GRID_SIZE = 5
SHIP_COUNT = 3
MAX_SHOTS = 18
CELL_COUNT = GRID_SIZE * GRID_SIZE

ShootResult = Literal["miss", "hit", "already", "win", "lose"]


def place_ships_random(rng: random.Random | None = None) -> set[int]:
    """Place *SHIP_COUNT* single-cell ships on random indices."""
    source = rng or random
    return set(source.sample(range(CELL_COUNT), SHIP_COUNT))


def new_game(rng: random.Random | None = None) -> dict:
    """Create a new battleships game state."""
    ships = place_ships_random(rng)
    return {
        "ships": ships,
        "shots": set(),
        "hits": set(),
        "finished": False,
    }


def ships_remaining(state: dict) -> int:
    """Return how many ship cells have not been hit yet."""
    return len(state["ships"] - state["hits"])


def shots_remaining(state: dict) -> int:
    """Return how many shots the player has left."""
    return MAX_SHOTS - len(state["shots"])


def all_sunk(state: dict) -> bool:
    """Return True when every ship cell has been hit."""
    return state["ships"].issubset(state["hits"])


def shoot(state: dict, index: int) -> ShootResult:
    """Fire at *index* and return the outcome."""
    if state["finished"]:
        return "already"
    if index in state["shots"]:
        return "already"
    state["shots"].add(index)
    if index in state["ships"]:
        state["hits"].add(index)
        if all_sunk(state):
            state["finished"] = True
            return "win"
        outcome: ShootResult = "hit"
    else:
        outcome = "miss"

    if len(state["shots"]) >= MAX_SHOTS:
        state["finished"] = True
        return "lose"
    return outcome
