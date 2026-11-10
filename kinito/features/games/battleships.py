"""Battleships fleet placement, duel rules and shot selection."""

from __future__ import annotations

import random

GRID_SIZE = 10
SHIP_LENGTHS = (5, 4, 3, 3, 2)
CELL_COUNT = GRID_SIZE * GRID_SIZE


def ship_cells(ship: int, index: int, vertical: bool) -> set[int]:
    if not 0 <= ship < len(SHIP_LENGTHS) or not 0 <= index < CELL_COUNT:
        return set()
    row, col = divmod(index, GRID_SIZE)
    length = SHIP_LENGTHS[ship]
    if (row if vertical else col) + length > GRID_SIZE:
        return set()
    return {index + step * (GRID_SIZE if vertical else 1) for step in range(length)}


def can_place(fleet: dict, ship: int, cells: set[int]) -> bool:
    return bool(cells) and not any(cells & other for key, other in fleet.items() if key != ship)


def place_ships_random(rng: random.Random | None = None) -> dict[int, set[int]]:
    source = rng or random
    fleet: dict[int, set[int]] = {}
    for ship in range(len(SHIP_LENGTHS)):
        options = [cells for index in range(CELL_COUNT) for vertical in (False, True)
                   if can_place(fleet, ship, cells := ship_cells(ship, index, vertical))]
        if not options:
            return place_ships_random(rng)
        fleet[ship] = source.choice(options)
    return fleet


def new_game(rng: random.Random | None = None) -> dict:
    return {
        "player": {"fleet": {}, "shots": set(), "hits": set(), "sunk": set()},
        "kinito": {"fleet": place_ships_random(rng), "shots": set(), "hits": set(), "sunk": set()},
        "phase": "placement", "turn": "player", "winner": None,
    }


def place_ship(state: dict, ship: int, index: int, vertical: bool) -> bool:
    cells = ship_cells(ship, index, vertical)
    fleet = state["player"]["fleet"]
    if state["phase"] != "placement" or not can_place(fleet, ship, cells):
        return False
    fleet[ship] = cells
    return True


def start_game(state: dict) -> bool:
    if state["phase"] != "placement" or len(state["player"]["fleet"]) != len(SHIP_LENGTHS):
        return False
    state["phase"] = "playing"
    return True


def ships_remaining(board: dict) -> int:
    return sum(not cells <= board["hits"] for cells in board["fleet"].values())


def shoot(state: dict, attacker: str, index: int) -> str:
    if (state["phase"] != "playing" or attacker != state["turn"]
            or not 0 <= index < CELL_COUNT):
        return "already"
    board = state["kinito" if attacker == "player" else "player"]
    if index in board["shots"]:
        return "already"
    board["shots"].add(index)
    ship = next((cells for cells in board["fleet"].values() if index in cells), None)
    if ship is None:
        state["turn"] = "kinito" if attacker == "player" else "player"
        return "miss"
    board["hits"].add(index)
    sunk = ship <= board["hits"]
    if sunk:
        board["sunk"].update(ship)
    if ships_remaining(board) == 0:
        state["phase"] = "finished"
        state["winner"] = attacker
        return "win"
    return "sunk" if sunk else "hit"


def neighbors(index: int) -> set[int]:
    row, col = divmod(index, GRID_SIZE)
    return {r * GRID_SIZE + c for r, c in
            ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))
            if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE}


def choose_ai_shot(knowledge: dict, rng: random.Random | None = None) -> int:
    source = rng or random
    available = set(range(CELL_COUNT)) - knowledge["shots"]
    hits = knowledge["hits"] - knowledge["sunk"]
    adjacent = set().union(*(neighbors(hit) for hit in hits)) & available
    aligned = set()
    for hit in hits:
        for step in (1, GRID_SIZE):
            other = hit + step
            if other in hits and other in neighbors(hit):
                for candidate in (hit - step, other + step):
                    if candidate in available and (candidate in neighbors(hit) or candidate in neighbors(other)):
                        aligned.add(candidate)
    return source.choice(sorted(aligned or adjacent or available))
