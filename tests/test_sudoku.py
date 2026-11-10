"""Unit tests for sudoku logic."""

import random

from kinito.features.games import sudoku as su


def _valid_grid(grid):
    for index in range(su.CELL_COUNT):
        row, col = divmod(index, su.SIZE)
        assert {grid[row * su.SIZE + c] for c in range(9)} == set(range(1, 10))
        assert {grid[r * su.SIZE + col] for r in range(9)} == set(range(1, 10))
    for br in range(0, 9, 3):
        for bc in range(0, 9, 3):
            cells = {
                grid[(br + dr) * su.SIZE + bc + dc]
                for dr in range(3)
                for dc in range(3)
            }
            assert cells == set(range(1, 10))


def test_new_solution_is_valid():
    for seed in range(5):
        grid = su.new_solution(random.Random(seed))
        assert len(grid) == su.CELL_COUNT
        _valid_grid(grid)


def test_new_game_givens_match_grid():
    state = su.new_game("easy", random.Random(0))
    assert len(state["givens"]) >= su.DIFFICULTIES["easy"]
    for index in state["givens"]:
        assert state["grid"][index] == state["solution"][index]


def test_place_strict_check():
    state = su.new_game("medium", random.Random(1))
    empty = next(i for i in range(su.CELL_COUNT) if i not in state["givens"])
    correct = state["solution"][empty]
    wrong = correct % 9 + 1
    assert su.place(state, empty, wrong) == "invalid"
    assert empty not in state["entries"]
    assert su.place(state, empty, correct) in ("ok", "win")
    assert su.cell_value(state, empty) == correct


def test_place_counts_mistakes():
    state = su.new_game("medium", random.Random(1))
    assert state["mistakes"] == 0
    empty = next(i for i in range(su.CELL_COUNT) if i not in state["givens"])
    correct = state["solution"][empty]
    wrong = correct % 9 + 1
    assert su.place(state, empty, wrong) == "invalid"
    assert su.place(state, empty, wrong) == "invalid"
    assert state["mistakes"] == 2
    su.place(state, empty, correct)
    assert state["mistakes"] == 2


def test_place_rejects_given_cells():
    state = su.new_game("easy", random.Random(2))
    given = next(iter(state["givens"]))
    assert su.place(state, given, state["solution"][given]) == "given"


def test_erase_only_player_entries():
    state = su.new_game("easy", random.Random(3))
    given = next(iter(state["givens"]))
    assert su.erase(state, given) is False
    empty = next(i for i in range(su.CELL_COUNT) if i not in state["givens"])
    su.place(state, empty, state["solution"][empty])
    assert su.erase(state, empty) is True
    assert su.cell_value(state, empty) == 0


def test_completing_puzzle_wins():
    state = su.new_game("easy", random.Random(4))
    result = "ok"
    for index in range(su.CELL_COUNT):
        if index not in state["givens"]:
            result = su.place(state, index, state["solution"][index])
    assert result == "win"
    assert state["finished"] is True
    assert su.remaining_empty(state) == 0
    assert su.place(state, 0, 5) == "given"
