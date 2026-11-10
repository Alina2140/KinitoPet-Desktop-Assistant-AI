"""Unit tests for mini-game logic."""

import random

import pytest

from content import dialogue as dlg
from content.hangman_words import WORDS, pick_word
from content.magic_8_ball import MAGIC_8_BALL_ANSWERS
from content.trivia_questions import (
    ROUND_SIZE,
    TRIVIA_QUESTIONS,
    TriviaQuestion,
    check_answer,
    pick_random_question,
)
from kinito.features.games import battleships as bs
from kinito.features.games import color_guess as cg
from kinito.features.games import connect_four as c4
from kinito.features.games import hangman as hangman_game
from kinito.features.games import minesweeper as ms
from kinito.features.games import snake as snake_game
from kinito.features.games import tetris as tetris_game
from kinito.features.games.coin_dice import (
    HEADS,
    TAILS,
    coin_outcome,
    dice_outcome,
    flip_coin,
    roll_dice,
)
from kinito.features.games.hangman import MAX_MISSES, apply_guess, display_word
from kinito.features.games.magic_8_ball import pick_answer
from kinito.features.games.memory import (
    DEFAULT_PAIRS,
    PAIR_OPTIONS,
    build_deck,
    grid_shape,
    is_match,
    normalize_pair_count,
    select_pairs,
)
from kinito.features.games.number_guess import (
    compare_guess,
    is_valid_guess,
    parse_guess,
)
from kinito.features.games.rock_paper_scissors import MOVES, rps_winner
from kinito.features.games.snake import (
    BASE_DELAY_MS,
    LEFT,
    MIN_DELAY_MS,
    RIGHT,
    UP,
    queue_direction,
    step,
    tick_delay_ms,
)
from kinito.features.games.tetris import (
    BASE_DELAY_MS as TETRIS_BASE_DELAY_MS,
)
from kinito.features.games.tetris import (
    COLS,
    LINE_SCORES,
    PIECE_TYPES,
    ROWS,
    hard_drop,
    move,
    rotate,
    soft_drop,
)
from kinito.features.games.tetris import (
    MIN_DELAY_MS as TETRIS_MIN_DELAY_MS,
)
from kinito.features.games.tetris import (
    step as tetris_step,
)
from kinito.features.games.tetris import (
    tick_delay_ms as tetris_tick_delay_ms,
)
from kinito.features.games.tic_tac_toe import (
    EMPTY,
    KINITO,
    PLAYER,
    check_winner,
    choose_ai_move,
    winning_line,
    winning_move,
)


def test_rps_rock_beats_scissors():
    assert rps_winner(dlg.BUTTON_ROCK, dlg.BUTTON_SCISSORS) == "player"


def test_rps_scissors_beats_paper():
    assert rps_winner(dlg.BUTTON_SCISSORS, dlg.BUTTON_PAPER) == "player"


def test_rps_paper_beats_rock():
    assert rps_winner(dlg.BUTTON_PAPER, dlg.BUTTON_ROCK) == "player"


def test_rps_draw():
    for rps_move in MOVES:
        assert rps_winner(rps_move, rps_move) is None


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


def test_ttt_winning_line_indices():
    board = [EMPTY] * 3 + [KINITO] * 3 + [EMPTY] * 3
    assert winning_line(board) == (3, 4, 5)
    board = list(board)
    board[4] = PLAYER
    assert winning_line(board) is None
    board = [PLAYER, EMPTY, EMPTY, EMPTY, PLAYER, EMPTY, EMPTY, EMPTY, PLAYER]
    assert winning_line(board) == (0, 4, 8)


def test_memory_deck_has_pairs():
    random.seed(0)
    deck = build_deck()
    assert len(deck) == len(DEFAULT_PAIRS) * 2
    for symbol in DEFAULT_PAIRS:
        assert deck.count(symbol) == 2


def test_memory_deck_for_pair_options():
    for count in PAIR_OPTIONS:
        pairs = select_pairs(count)
        assert len(pairs) == count
        deck = build_deck(pairs)
        assert len(deck) == count * 2
        rows, cols = grid_shape(count)
        assert rows * cols == count * 2
        for symbol in pairs:
            assert deck.count(symbol) == 2


def test_memory_normalize_pair_count():
    assert normalize_pair_count(12) == 12
    assert normalize_pair_count(99) == 16
    assert normalize_pair_count(None) == 16


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


def test_trivia_pick_random_question_respects_pack():
    from content.trivia_questions import PACK_ANIMALS, questions_for_pack

    random.seed(0)
    for _ in range(20):
        question = pick_random_question(pack=PACK_ANIMALS)
        assert question.pack == PACK_ANIMALS
        assert question in questions_for_pack(PACK_ANIMALS)


def test_trivia_mixed_uses_all_packs():
    from content.trivia_questions import ALL_PACK_IDS, PACK_MIXED, TRIVIA_PACKS

    assert len(TRIVIA_QUESTIONS) == sum(len(q) for q in TRIVIA_PACKS.values())
    for pack_id in ALL_PACK_IDS:
        if pack_id == PACK_MIXED:
            continue
        assert len(TRIVIA_PACKS[pack_id]) >= ROUND_SIZE


def test_trivia_round_size_is_five():
    assert ROUND_SIZE == 5
    assert len(TRIVIA_QUESTIONS) >= ROUND_SIZE


def test_battleships_random_fleet():
    for seed in range(30):
        fleet = bs.place_ships_random(random.Random(seed))
        assert [len(ship) for ship in fleet.values()] == list(bs.SHIP_LENGTHS)
        cells = set().union(*fleet.values())
        assert len(cells) == 17
        assert all(0 <= cell < 100 for cell in cells)


def test_battleships_placement():
    state = bs.new_game(random.Random(0))
    assert not bs.start_game(state)
    assert bs.place_ship(state, 0, 0, False)
    assert not bs.place_ship(state, 1, 3, False)
    assert not bs.place_ship(state, 1, 98, True)
    assert not bs.place_ship(state, 1, 9, False)
    assert state["player"]["fleet"][0] == set(range(5))
    assert bs.place_ship(state, 1, 10, False)
    assert bs.place_ship(state, 0, 5, True)
    assert state["player"]["fleet"][0] == {5, 15, 25, 35, 45}
    assert not bs.place_ship(state, 0, -1, False)


def _battleships_duel():
    state = bs.new_game(random.Random(0))
    for ship in range(5):
        assert bs.place_ship(state, ship, ship * 10, False)
    assert bs.start_game(state)
    return state


def test_battleships_turns():
    state = _battleships_duel()
    fleet = state["kinito"]["fleet"]
    hit = next(iter(fleet[0]))
    assert bs.shoot(state, "player", hit) == "hit"
    assert state["turn"] == "player"
    assert bs.shoot(state, "player", hit) == "already"
    miss = next(i for i in range(100) if not any(i in s for s in fleet.values()))
    assert bs.shoot(state, "player", miss) == "miss"
    assert state["turn"] == "kinito"
    assert bs.shoot(state, "player", hit) == "already"
    assert not bs.place_ship(state, 0, 60, False)


@pytest.mark.parametrize("attacker", ["player", "kinito"])
def test_battleships_victory(attacker):
    state = _battleships_duel()
    state["turn"] = attacker
    defender = "kinito" if attacker == "player" else "player"
    results = [bs.shoot(state, attacker, i)
               for ship in state[defender]["fleet"].values() for i in sorted(ship)]
    assert results.count("sunk") == 4
    assert results[-1] == "win"
    assert state["winner"] == attacker
    assert state["phase"] == "finished"
    assert bs.ships_remaining(state[defender]) == 0
    assert bs.shoot(state, attacker, 99) == "already"


def test_battleships_ai_targets_and_edges():
    knowledge = {"shots": {0}, "hits": {0}, "sunk": set()}
    assert bs.choose_ai_shot(knowledge, random.Random(1)) in {1, 10}
    knowledge = {"shots": {44, 45}, "hits": {44, 45}, "sunk": set()}
    assert bs.choose_ai_shot(knowledge, random.Random(1)) in {43, 46}
    knowledge = {"shots": {0, 1}, "hits": {0, 1}, "sunk": {0}}
    assert bs.choose_ai_shot(knowledge, random.Random(1)) in {2, 11}
    knowledge = {"shots": set(range(99)), "hits": set(), "sunk": set()}
    assert bs.choose_ai_shot(knowledge) == 99


def test_battleships_ui_timer_and_reset():
    from unittest.mock import Mock

    from kinito.features.games.battleships_ui import BattleshipsGame

    app = Mock(spec=["speak_game_line", "on_game_outcome"])
    game = BattleshipsGame(app)
    game.window = Mock()
    game._refresh = Mock()
    game._start()
    assert game.state["phase"] == "placement"
    game.state = _battleships_duel()
    board = game.state["kinito"]
    miss = next(i for i in range(100) if not any(i in s for s in board["fleet"].values()))
    game._fire("player", miss)
    game.window.after.assert_called_once()
    scheduled = game._after_id
    game._fire("player", miss + 1)
    assert game.window.after.call_count == 1
    game.dragging = True
    game.preview = (10, 10)
    game._reset()
    game.window.after_cancel.assert_called_once_with(scheduled)
    assert game.state["phase"] == "placement"
    assert not game.dragging
    assert game.preview is None


def test_battleships_kinito_sinking_line():
    from unittest.mock import Mock

    from content import game_lines
    from kinito.features.games.battleships_ui import BattleshipsGame

    app = Mock(spec=["speak_game_line", "on_game_outcome"])
    game = BattleshipsGame(app)
    game.window = Mock()
    game._refresh = Mock()
    game.state = _battleships_duel()
    game.state["turn"] = "kinito"
    cells = sorted(game.state["player"]["fleet"][4])
    game._fire("kinito", cells[0])
    app.speak_game_line.assert_not_called()
    game._fire("kinito", cells[1])
    assert app.speak_game_line.call_args.args[0] in game_lines.BATTLESHIPS_KINITO_SUNK_LINES
    app.on_game_outcome.assert_not_called()


def test_battleships_player_color_and_rainbow():
    from unittest.mock import Mock

    from kinito.colors import rainbow_at
    from kinito.features.games.battleships_ui import BattleshipsGame

    app = Mock(spec=["battleships_color"])
    app.battleships_color.return_value = "#16a34a"
    game = BattleshipsGame(app)
    assert game._player_color(0) == "#16a34a"
    app.battleships_color.return_value = "rainbow"
    assert game._player_color(2) == rainbow_at(2)


def test_battleships_ui_rotation_and_invalid_drop():
    from types import SimpleNamespace
    from unittest.mock import Mock

    from kinito.features.games.battleships_ui import BattleshipsGame

    game = BattleshipsGame(Mock(spec=[]))
    game._draw = Mock()
    game._refresh = Mock()
    game.origins = {"player": (0, 0)}
    game.cell = 20
    bs.place_ship(game.state, 0, 0, False)
    game._rotate()
    assert game.state["player"]["fleet"][0] == {0, 10, 20, 30, 40}
    game.dragging = True
    game._release(SimpleNamespace(x=-10, y=-10))
    assert game.state["player"]["fleet"][0] == {0, 10, 20, 30, 40}


def test_snake_starts_at_left_edge_heading_right():
    state = snake_game.new_game(rng=random.Random(0))
    row = snake_game.GRID_SIZE // 2
    assert state["snake"] == [
        (snake_game.START_LENGTH - 1 - i, row) for i in range(snake_game.START_LENGTH)
    ]
    assert state["snake"][-1] == (0, row)
    assert state["direction"] == RIGHT


def test_snake_rejects_180_turn():
    state = snake_game.new_game(rng=random.Random(0))
    assert state["direction"] == RIGHT
    assert queue_direction(state, *LEFT) is False
    assert state["pending_direction"] == RIGHT
    assert queue_direction(state, *UP) is True
    assert state["pending_direction"] == UP


def test_snake_step_without_food_keeps_length():
    state = snake_game.new_game(rng=random.Random(0))
    state["food"] = (0, 0)
    length_before = len(state["snake"])
    head_before = state["snake"][0]
    assert step(state) == "ok"
    assert len(state["snake"]) == length_before
    assert state["snake"][0] == (head_before[0] + 1, head_before[1])
    assert state["alive"] is True


def test_tetris_next_preview_centers_every_piece():
    from unittest.mock import MagicMock

    from kinito.features.games.tetris import SHAPES
    from kinito.features.games.tetris_ui import NEXT_CELL, PAD, TetrisGame

    size = 4 * NEXT_CELL + PAD * 2
    for piece_type in SHAPES:
        game = TetrisGame.__new__(TetrisGame)
        game.state = {"next_type": piece_type}
        game.next_canvas = MagicMock()
        game._draw_next()

        rects = [
            call.args
            for call in game.next_canvas.mock_calls
            if call[0] == "create_rectangle" and call.kwargs.get("outline") == ""
        ]
        assert rects, piece_type
        center_x = (min(r[0] for r in rects) + max(r[2] for r in rects)) / 2
        center_y = (min(r[1] for r in rects) + max(r[3] for r in rects)) / 2
        assert abs(center_x - size / 2) <= 1, piece_type
        assert abs(center_y - size / 2) <= 1, piece_type


def test_snake_eating_plays_crunch_sound():
    from unittest.mock import MagicMock

    from kinito.assets import crunch_file_path
    from kinito.features.games.snake_ui import SnakeGame

    app = MagicMock()
    game = SnakeGame.__new__(SnakeGame)
    game.app = app
    game.state = snake_game.new_game(rng=random.Random(0))
    game.state["food"] = (game.state["snake"][0][0] + 1, game.state["snake"][0][1])
    game.highscore = 0
    game.canvas = MagicMock()
    game.status_label = MagicMock()
    game.window = MagicMock()
    game._running = True

    game._tick()

    app.play_sfx.assert_called_once_with(crunch_file_path)


def test_snake_eating_grows_and_scores():
    state = snake_game.new_game(rng=random.Random(0))
    head = state["snake"][0]
    state["food"] = (head[0] + 1, head[1])
    length_before = len(state["snake"])
    assert step(state) == "ate"
    assert state["score"] == 1
    assert len(state["snake"]) == length_before + 1
    assert state["food"] not in state["snake"]


def test_snake_wall_collision_kills():
    state = snake_game.new_game(rng=random.Random(0))
    state["snake"] = [(snake_game.GRID_SIZE - 1, 5)]
    state["direction"] = RIGHT
    state["pending_direction"] = RIGHT
    state["food"] = (0, 0)
    assert step(state) == "dead"
    assert state["alive"] is False


def test_snake_self_collision_kills():
    state = snake_game.new_game(rng=random.Random(0))
    # Head at (5,5) moving right into body at (6,5).
    state["snake"] = [(5, 5), (5, 6), (6, 6), (6, 5), (6, 4)]
    state["direction"] = RIGHT
    state["pending_direction"] = RIGHT
    state["food"] = (0, 0)
    assert step(state) == "dead"
    assert state["alive"] is False


def test_snake_tick_delay_decreases_with_floor():
    assert tick_delay_ms(0) == BASE_DELAY_MS
    assert tick_delay_ms(5) < BASE_DELAY_MS
    assert tick_delay_ms(100) == MIN_DELAY_MS


def test_connect_four_drop_stacks_from_bottom():
    board = c4.new_board()
    assert c4.drop_disc(board, 0, c4.PLAYER) == (c4.ROWS - 1, 0)
    assert c4.drop_disc(board, 0, c4.KINITO) == (c4.ROWS - 2, 0)
    assert board[c4.ROWS - 1][0] == c4.PLAYER
    assert board[c4.ROWS - 2][0] == c4.KINITO


def test_connect_four_full_column_rejects_drop():
    board = c4.new_board()
    for _ in range(c4.ROWS):
        assert c4.drop_disc(board, 3, c4.PLAYER) is not None
    assert c4.drop_disc(board, 3, c4.KINITO) is None


def test_connect_four_custom_board_sizes():
    for cols, rows in ((9, 7), (11, 8)):
        board = c4.new_board(rows, cols)
        assert len(board) == rows and len(board[0]) == cols
        assert c4.drop_disc(board, cols - 1, c4.PLAYER, rows, cols) == (rows - 1, cols - 1)
        assert c4.valid_columns(board, cols) == list(range(cols))
        # Fill a diagonal-ish win horizontally on the bottom row.
        board2 = c4.new_board(rows, cols)
        for col in range(4):
            c4.drop_disc(board2, col, c4.PLAYER, rows, cols)
        assert c4.check_winner(board2, rows, cols) == c4.PLAYER


def test_connect_four_ai_works_on_big_board():
    board = c4.new_board(7, 9)
    for col in range(3):
        c4.drop_disc(board, col, c4.KINITO, 7, 9)
    col = c4.choose_ai_column(board, rows=7, cols=9)
    assert col == 3


def test_connect_four_horizontal_win():
    board = c4.new_board()
    row = c4.ROWS - 1
    for col in range(4):
        board[row][col] = c4.PLAYER
    assert c4.check_winner(board) == c4.PLAYER


def test_connect_four_vertical_win():
    board = c4.new_board()
    for row in range(c4.ROWS - 4, c4.ROWS):
        board[row][2] = c4.KINITO
    assert c4.check_winner(board) == c4.KINITO


def test_connect_four_diagonal_win():
    board = c4.new_board()
    for i in range(4):
        board[c4.ROWS - 1 - i][i] = c4.PLAYER
    assert c4.check_winner(board) == c4.PLAYER


def test_connect_four_draw_when_full_without_four():
    board = [
        list("LRLRLRL"),
        list("LRLRLRL"),
        list("RLRLRLR"),
        list("RLRLRLR"),
        list("LRLRLRL"),
        list("LRLRLRL"),
    ]
    assert len(board) == c4.ROWS
    assert all(len(row) == c4.COLS for row in board)
    assert c4.check_winner(board) == "draw"


def test_connect_four_ai_takes_winning_column():
    board = c4.new_board()
    for col in range(3):
        board[c4.ROWS - 1][col] = c4.KINITO
    assert c4.winning_column(board, c4.KINITO) == 3
    assert c4.choose_ai_column(board) == 3


def test_connect_four_ai_blocks_player_win():
    board = c4.new_board()
    for col in range(3):
        board[c4.ROWS - 1][col] = c4.PLAYER
    assert c4.choose_ai_column(board) == 3


def test_connect_four_ai_opening_varies():
    """Empty-board replies should not always be the same center column."""
    board = c4.new_board()
    picks = {c4.choose_ai_column(board, rng=random.Random(seed)) for seed in range(40)}
    assert len(picks) >= 2
    assert picks <= {1, 2, 3, 4, 5}


def test_connect_four_ai_avoids_lonely_vertical_stack():
    """After one center disc, AI should often branch instead of stacking again."""
    board = c4.new_board()
    board[c4.ROWS - 1][3] = c4.KINITO
    picks = [c4.choose_ai_column(board, rng=random.Random(seed)) for seed in range(30)]
    assert any(col != 3 for col in picks)


def test_connect_four_ai_avoids_giving_immediate_win():
    """Do not play a column that lets the player win on the following drop."""
    board = c4.new_board()
    # Player on row ROWS-2 at cols 2-4. Dropping in col 1 fills the bottom so the
    # player can then drop in col 1 and complete four-in-a-row on that row.
    row = c4.ROWS - 2
    for col in (2, 3, 4):
        board[row][col] = c4.PLAYER
        board[c4.ROWS - 1][col] = c4.KINITO
    board[c4.ROWS - 1][5] = c4.KINITO

    trial = [r[:] for r in board]
    c4.drop_disc(trial, 1, c4.KINITO)
    assert c4.winning_column(trial, c4.PLAYER) == 1

    choice = c4.choose_ai_column(board, rng=random.Random(0))
    assert choice != 1


def test_ttt_ai_blocks_fork():
    # X at 0 and 5 with O in center can fork at 2; AI must stop that.
    board = [
        PLAYER,
        EMPTY,
        EMPTY,
        EMPTY,
        KINITO,
        PLAYER,
        EMPTY,
        EMPTY,
        EMPTY,
    ]
    move = choose_ai_move(board, rng=random.Random(0))
    assert move in (1, 2, 8)
    trial = board[:]
    trial[move] = KINITO
    from kinito.features.games.tic_tac_toe import _fork_move

    assert _fork_move(trial, PLAYER) is None


def test_hangman_words_are_playable():
    assert len(WORDS) >= 120
    for word in WORDS:
        assert 4 <= len(word) <= 10
        assert word.isalpha() and word.isupper()
        assert word.isascii()


def test_hangman_pick_word_from_list():
    word = pick_word(rng=random.Random(0))
    assert word in WORDS


def test_hangman_pick_word_avoids_used():
    used = set(WORDS[:-1])
    word = pick_word(rng=random.Random(1), used=used)
    assert word == WORDS[-1]


def test_hangman_letter_button_disabled_style():
    from unittest.mock import MagicMock

    from kinito.features.games.hangman import (
        _LETTER_BTN_DISABLED_BG,
        _LETTER_BTN_DISABLED_FG,
        _style_letter_button,
    )

    button = MagicMock()
    _style_letter_button(button, enabled=False)
    import tkinter as tk

    kwargs = button.config.call_args.kwargs
    assert kwargs["state"] == tk.DISABLED
    assert kwargs["bg"] == _LETTER_BTN_DISABLED_BG
    assert kwargs["fg"] == _LETTER_BTN_DISABLED_FG


def test_hangman_hit_reveals_letters():
    state = hangman_game.new_game("CAT")
    assert apply_guess(state, "a") == "hit"
    assert display_word(state) == "_ A _"
    assert state["misses"] == 0


def test_hangman_miss_increments():
    state = hangman_game.new_game("CAT")
    assert apply_guess(state, "z") == "miss"
    assert state["misses"] == 1
    assert display_word(state) == "_ _ _"


def test_hangman_repeat_guess_ignored():
    state = hangman_game.new_game("CAT")
    apply_guess(state, "z")
    before = dict(state)
    before["guessed"] = set(state["guessed"])
    before["revealed"] = list(state["revealed"])
    assert apply_guess(state, "z") == "repeat"
    assert state["misses"] == before["misses"]
    assert state["guessed"] == before["guessed"]


def test_hangman_win_when_all_revealed():
    state = hangman_game.new_game("HI")
    assert apply_guess(state, "h") == "hit"
    assert apply_guess(state, "i") == "hit"
    assert state["status"] == "won"
    assert display_word(state) == "H I"


def test_hangman_misses_never_exceed_max_on_rapid_wrong_guesses():
    state = hangman_game.new_game("AB")
    wrong = "CDEFGHIJKLMNOPQRSTUVWXYZ"
    for ch in wrong:
        apply_guess(state, ch)
    assert state["misses"] <= MAX_MISSES
    assert state["status"] == "lost"


def test_hangman_lose_at_max_misses():
    state = hangman_game.new_game("AB")
    for letter in "CDEFGH":
        apply_guess(state, letter)
    assert state["misses"] == MAX_MISSES
    assert state["status"] == "lost"
    assert display_word(state) == "A B"


def test_minesweeper_ensure_mines_avoids_safe_zone():
    state = ms.new_game()
    safe = 40  # center-ish
    ms.ensure_mines(state, safe, rng=random.Random(0))
    assert len(state["mines"]) == ms.MINE_COUNT
    assert safe not in state["mines"]
    for neighbor in ms._neighbors(safe):
        assert neighbor not in state["mines"]
    assert state["started"] is True


def test_minesweeper_flood_fill_on_zero():
    state = ms.new_game()
    # Place mines only in a corner so center opens wide.
    state["mines"] = {0, 1, 2, 9, 10, 18, 19, 20, 27, 28}
    state["started"] = True
    result = ms.reveal_cell(state, 80)  # bottom-right
    assert result in ("ok", "win")
    assert 80 in state["revealed"]
    assert len(state["revealed"]) > 1
    assert ms.neighbor_count(state, 80) == 0


def test_minesweeper_reveal_mine_loses():
    state = ms.new_game()
    state["mines"] = {5}
    state["started"] = True
    assert ms.reveal_cell(state, 5) == "lose"
    assert state["finished"] is True
    assert state["won"] is False


def test_minesweeper_clear_board_wins():
    state = ms.new_game()
    state["mines"] = {0}
    state["started"] = True
    result = "ok"
    for index in range(1, ms.CELL_COUNT):
        outcome = ms.reveal_cell(state, index)
        if outcome != "ignored":
            result = outcome
    assert result == "win"
    assert state["won"] is True
    assert state["finished"] is True


def test_minesweeper_flag_toggle_and_block_revealed():
    state = ms.new_game()
    state["mines"] = {10}
    state["started"] = True
    assert ms.toggle_flag(state, 0) is True
    assert 0 in state["flags"]
    assert ms.toggle_flag(state, 0) is True
    assert 0 not in state["flags"]
    ms.reveal_cell(state, 1)
    assert ms.toggle_flag(state, 1) is False


def test_minesweeper_flagged_cell_not_revealed():
    state = ms.new_game()
    state["mines"] = {0}
    state["started"] = True
    ms.toggle_flag(state, 5)
    assert ms.reveal_cell(state, 5) == "ignored"
    assert 5 not in state["revealed"]


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
    app.root.winfo_screenwidth.return_value = 1920
    app.root.winfo_screenheight.return_value = 1080
    app._centered_origin_on_primary = MagicMock(return_value=(760, 290))

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
    assert app.speak_game_line.call_args.kwargs.get("defer_if_speaking") is True


def test_speak_game_line_defers_while_speech_is_active():
    from unittest.mock import MagicMock

    from kinito.features.games import GamesMixin

    class GameSpeechStub(GamesMixin):
        pass

    stub = GameSpeechStub()
    stub._is_busy_with_speech = MagicMock(side_effect=[True, False])
    stub.speak = MagicMock()
    stub.root = MagicMock()

    stub.speak_game_line("Game closed.", defer_if_speaking=True)

    stub.speak.assert_not_called()
    stub.root.after.assert_called_once()
    stub.root.after.call_args.args[1]()
    stub.speak.assert_called_once_with(
        "Game closed.", show_bubble=True, skip_ai=True
    )


def test_is_game_active_with_open_window():
    from unittest.mock import MagicMock

    from kinito.features.games import GamesMixin

    app = GamesMixin()
    window = MagicMock()
    window.winfo_exists.return_value = True
    app._game_window = window
    assert app._is_game_active() is True


def test_is_game_active_with_number_guess():
    from kinito.features.games import GamesMixin

    app = GamesMixin()
    app._game_window = None
    app._number_guess_target = 42
    assert app._is_game_active() is True


def test_is_game_active_with_trivia_round():
    from kinito.features.games import GamesMixin

    app = GamesMixin()
    app._game_window = None
    app._number_guess_target = None
    app._trivia_round = 2
    app._trivia_used = {TRIVIA_QUESTIONS[0]}
    assert app._is_game_active() is True


def test_is_game_active_false_when_idle():
    from kinito.features.games import GamesMixin

    app = GamesMixin()
    app._game_window = None
    app._number_guess_target = None
    app._trivia_round = ROUND_SIZE
    app._trivia_used = set(TRIVIA_QUESTIONS[:ROUND_SIZE])
    assert app._is_game_active() is False


def test_tetris_move_blocked_by_wall():
    state = tetris_game.new_game(rng=random.Random(0))
    active = state["active"]
    # Horizontal I: cells at ox..ox+3
    active["type"] = "I"
    active["rotation"] = 0
    active["x"] = 0
    active["y"] = 5
    assert move(state, -1) == "noop"
    assert active["x"] == 0
    active["x"] = COLS - 4
    assert move(state, 1) == "noop"
    assert active["x"] == COLS - 4
    assert move(state, -1) == "ok"
    assert active["x"] == COLS - 5


def test_tetris_rotate_o_is_noop_and_t_rotates():
    state = tetris_game.new_game(rng=random.Random(1))
    active = state["active"]
    active["type"] = "O"
    active["rotation"] = 0
    active["x"] = 3
    active["y"] = 5
    assert rotate(state) == "noop"
    assert active["rotation"] == 0

    active["type"] = "T"
    assert rotate(state) == "ok"
    assert active["rotation"] == 1
    assert rotate(state) == "ok"
    assert active["rotation"] == 2


def test_tetris_soft_drop_scores_and_moves():
    state = tetris_game.new_game(rng=random.Random(2))
    y_before = state["active"]["y"]
    score_before = state["score"]
    assert soft_drop(state) == "ok"
    assert state["active"]["y"] == y_before + 1
    assert state["score"] == score_before + 1


def test_tetris_hard_drop_locks_and_spawns_next():
    state = tetris_game.new_game(rng=random.Random(3))
    next_type = state["next_type"]
    result = hard_drop(state)
    assert result == "locked"
    assert state["alive"] is True
    assert state["active"] is not None
    assert state["active"]["type"] == next_type
    locked = sum(1 for row in state["board"] for cell in row if cell is not None)
    assert locked == 4


def test_tetris_line_clear_updates_score_lines_level():
    state = tetris_game.new_game(rng=random.Random(4))
    # Horizontal I uses local y+1 — one soft_drop then lock onto a full bottom row.
    state["board"][ROWS - 1] = ["#aaa"] * COLS
    state["active"] = {"type": "I", "rotation": 0, "x": 3, "y": ROWS - 4}
    state["next_type"] = "T"
    state["bag"] = list(PIECE_TYPES)
    state["score"] = 0
    state["lines"] = 0
    state["level"] = 1
    assert soft_drop(state) == "ok"
    assert state["active"]["y"] == ROWS - 3
    state["score"] = 0  # ignore soft-drop bonus for clear-score assert
    result = soft_drop(state)
    assert result == "locked"
    assert state["lines"] == 1
    assert state["score"] == LINE_SCORES[1] * 1
    assert state["level"] == 1


def test_tetris_spawn_blocked_ends_game():
    state = tetris_game.new_game(rng=random.Random(5))
    # Block spawn cells without creating full lines (gap in column 0 every row).
    for y in range(ROWS):
        state["board"][y][0] = None
        for x in range(1, COLS):
            state["board"][y][x] = "#111"
    state["active"] = {"type": "O", "rotation": 0, "x": 3, "y": ROWS - 2}
    for x, y in tetris_game.cells_for("O", 0, 3, ROWS - 2):
        state["board"][y][x] = None
    state["next_type"] = "T"
    state["bag"] = ["I", "J", "L", "S", "Z"]
    assert soft_drop(state) == "dead"
    assert state["alive"] is False


def test_tetris_tick_delay_decreases_with_floor():
    assert tetris_tick_delay_ms(1) == TETRIS_BASE_DELAY_MS
    assert tetris_tick_delay_ms(5) < TETRIS_BASE_DELAY_MS
    assert tetris_tick_delay_ms(100) == TETRIS_MIN_DELAY_MS


def test_tetris_bag_delivers_all_seven_before_repeat():
    state = tetris_game.new_game(rng=random.Random(6))
    seen = [state["active"]["type"], state["next_type"]]
    while state["bag"]:
        seen.append(state["bag"].pop())
    assert sorted(seen) == sorted(PIECE_TYPES)
    tetris_game._refill_bag(state)
    assert sorted(state["bag"]) == sorted(PIECE_TYPES)


def test_tetris_step_moves_down():
    state = tetris_game.new_game(rng=random.Random(7))
    y_before = state["active"]["y"]
    assert tetris_step(state) == "ok"
    assert state["active"]["y"] == y_before + 1


def test_color_guess_new_round_has_unique_colors():
    rng = random.Random(42)
    for count in cg.DIFFICULTIES:
        state = cg.new_round(count, rng=rng)
        assert len(state["colors"]) == count
        assert len(set(state["colors"])) == count
        assert state["target_hex"] == state["colors"][state["target_index"]]
        assert state["status"] == "playing"
        assert state["removed"] == set()


def test_color_guess_wrong_guess_removes_only_that_index():
    state = cg.new_round(5, rng=random.Random(1))
    wrong = next(i for i in range(5) if i != state["target_index"])
    assert cg.apply_guess(state, wrong) == "wrong"
    assert wrong in state["removed"]
    assert state["status"] == "playing"


def test_color_guess_correct_sets_won():
    state = cg.new_round(5, rng=random.Random(2))
    target = state["target_index"]
    assert cg.apply_guess(state, target) == "correct"
    assert state["status"] == "won"


def test_color_guess_ignored_after_win_or_invalid():
    state = cg.new_round(5, rng=random.Random(3))
    cg.apply_guess(state, state["target_index"])
    assert cg.apply_guess(state, 0) == "ignored"
    assert cg.apply_guess(state, -1) == "ignored"
    assert cg.apply_guess(state, 99) == "ignored"

    state = cg.new_round(5, rng=random.Random(4))
    wrong = next(i for i in range(5) if i != state["target_index"])
    cg.apply_guess(state, wrong)
    assert cg.apply_guess(state, wrong) == "ignored"
