"""Unit tests for mini-game logic."""

import random

import pytest

from content import dialogue as dlg
from content.magic_8_ball import MAGIC_8_BALL_ANSWERS
from content.trivia_questions import (
    ROUND_SIZE,
    TRIVIA_QUESTIONS,
    TriviaQuestion,
    check_answer,
    pick_random_question,
)
from kinito.features.games.battleships import (
    GRID_SIZE,
    MAX_SHOTS,
    SHIP_COUNT,
    all_sunk,
    new_game,
    place_ships_random,
    ships_remaining,
    shoot,
    shots_remaining,
)
from kinito.features.games.coin_dice import (
    HEADS,
    TAILS,
    coin_outcome,
    dice_outcome,
    flip_coin,
    roll_dice,
)
from kinito.features.games.magic_8_ball import pick_answer
from kinito.features.games.memory import DEFAULT_PAIRS, build_deck, is_match
from kinito.features.games.number_guess import (
    compare_guess,
    is_valid_guess,
    parse_guess,
)
from kinito.features.games.rock_paper_scissors import MOVES, rps_winner
from kinito.features.games.tic_tac_toe import (
    EMPTY,
    KINITO,
    PLAYER,
    check_winner,
    choose_ai_move,
    winning_move,
)


def test_rps_rock_beats_scissors():
    assert rps_winner(dlg.BUTTON_ROCK, dlg.BUTTON_SCISSORS) == "player"


def test_rps_scissors_beats_paper():
    assert rps_winner(dlg.BUTTON_SCISSORS, dlg.BUTTON_PAPER) == "player"


def test_rps_paper_beats_rock():
    assert rps_winner(dlg.BUTTON_PAPER, dlg.BUTTON_ROCK) == "player"


def test_rps_draw():
    for move in MOVES:
        assert rps_winner(move, move) is None


def test_rps_kinito_wins():
    assert rps_winner(dlg.BUTTON_ROCK, dlg.BUTTON_PAPER) == "kinito"


def test_parse_guess_valid():
    assert parse_guess(" 42 ") == 42


def test_parse_guess_invalid():
    assert parse_guess("abc") is None


@pytest.mark.parametrize("value", [0, 101, -5])
def test_is_valid_guess_out_of_range(value):
    assert is_valid_guess(value) is False


def test_compare_guess():
    assert compare_guess(50, 50) == "correct"
    assert compare_guess(10, 50) == "higher"
    assert compare_guess(90, 50) == "lower"


def test_ttt_player_row_win():
    board = [PLAYER, PLAYER, PLAYER] + [EMPTY] * 6
    assert check_winner(board) == PLAYER


def test_ttt_draw():
    board = [
        PLAYER,
        KINITO,
        PLAYER,
        KINITO,
        PLAYER,
        KINITO,
        KINITO,
        PLAYER,
        KINITO,
    ]
    assert check_winner(board) == "draw"


def test_ttt_winning_move_finds_block():
    board = [PLAYER, PLAYER, EMPTY] + [EMPTY] * 6
    assert winning_move(board, PLAYER) == 2


def test_ttt_ai_blocks_player_win():
    board = [PLAYER, PLAYER, EMPTY, EMPTY, KINITO, EMPTY, EMPTY, EMPTY, EMPTY]
    assert choose_ai_move(board) == 2


def test_memory_deck_has_pairs():
    random.seed(0)
    deck = build_deck()
    assert len(deck) == 16
    for symbol in DEFAULT_PAIRS:
        assert deck.count(symbol) == 2


def test_memory_is_match():
    assert is_match("🦊", "🦊") is True
    assert is_match("🦊", "🐸") is False


def test_flip_coin_returns_valid_side():
    random.seed(0)
    assert flip_coin() in (HEADS, TAILS)


def test_roll_dice_in_range():
    random.seed(0)
    for _ in range(20):
        assert 1 <= roll_dice() <= 6


def test_coin_outcome():
    assert coin_outcome(HEADS, HEADS) == "win"
    assert coin_outcome(HEADS, TAILS) == "lose"


def test_dice_outcome():
    assert dice_outcome(3, 3) == "win"
    assert dice_outcome(2, 5) == "lose"


def test_magic_8_ball_pick_answer():
    random.seed(0)
    answer = pick_answer()
    assert answer in MAGIC_8_BALL_ANSWERS


def test_trivia_check_answer():
    question = TriviaQuestion("Cats are reptiles.", False)
    assert check_answer(question, False) is True
    assert check_answer(question, True) is False


def test_trivia_pick_random_question_excludes_used():
    random.seed(0)
    first = pick_random_question()
    second = pick_random_question({first})
    assert second != first


def test_trivia_round_size_is_five():
    assert ROUND_SIZE == 5
    assert len(TRIVIA_QUESTIONS) >= ROUND_SIZE


def test_battleships_place_ships_no_duplicates():
    rng = random.Random(0)
    ships = place_ships_random(rng)
    assert len(ships) == SHIP_COUNT
    assert all(0 <= index < GRID_SIZE * GRID_SIZE for index in ships)


def test_battleships_shoot_miss_then_hit():
    state = new_game(rng=random.Random(0))
    ship_index = next(iter(state["ships"]))
    miss_index = next(i for i in range(GRID_SIZE * GRID_SIZE) if i not in state["ships"])
    assert shoot(state, miss_index) == "miss"
    assert shoot(state, miss_index) == "already"
    assert shoot(state, ship_index) == "hit"
    assert ships_remaining(state) == SHIP_COUNT - 1


def test_battleships_win_when_all_ships_hit():
    state = new_game(rng=random.Random(1))
    results = []
    for index in sorted(state["ships"]):
        results.append(shoot(state, index))
    assert results[-1] == "win"
    assert all_sunk(state)
    assert state["finished"] is True


def test_battleships_shots_remaining():
    state = new_game(rng=random.Random(0))
    assert shots_remaining(state) == MAX_SHOTS
    miss_index = next(i for i in range(GRID_SIZE * GRID_SIZE) if i not in state["ships"])
    shoot(state, miss_index)
    assert shots_remaining(state) == MAX_SHOTS - 1


def test_battleships_lose_when_out_of_shots():
    state = new_game(rng=random.Random(0))
    miss_indices = [i for i in range(GRID_SIZE * GRID_SIZE) if i not in state["ships"]]
    results = []
    for index in miss_indices[:MAX_SHOTS]:
        results.append(shoot(state, index))
    assert results[-1] == "lose"
    assert state["finished"] is True
    assert not all_sunk(state)


def test_game_window_close_shows_speech_bubble():
    from unittest.mock import MagicMock, patch

    from kinito.features.games.base import open_game_window

    app = MagicMock()
    app._game_window = None
    app._ensure_single_game_window = MagicMock()
    app.speak_game_line = MagicMock()
    app.root = MagicMock()
    app.root.update_idletasks = MagicMock()
    app.root.winfo_vrootx.return_value = 0
    app.root.winfo_vrooty.return_value = 0
    app.root.winfo_vrootwidth.return_value = 1920
    app.root.winfo_vrootheight.return_value = 1080

    window = MagicMock()
    with (
        patch("kinito.features.games.base.Toplevel", return_value=window),
        patch("kinito.features.games.base.apply_window_icon"),
    ):
        open_game_window(app, "Test Game", 400, 500)

    close_handler = window.protocol.call_args.args[1]
    close_handler()
    app.root.after.assert_called_once()
    after_callback = app.root.after.call_args.args[1]
    after_callback()
    app.speak_game_line.assert_called_once()
