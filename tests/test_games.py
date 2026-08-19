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
from kinito.features.games import color_guess as cg
from kinito.features.games import connect_four as c4
from kinito.features.games import hangman as hangman_game
from kinito.features.games import minesweeper as ms
from kinito.features.games import snake as snake_game
from kinito.features.games import tetris as tetris_game
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
from kinito.features.games.hangman import MAX_MISSES, apply_guess, display_word
from kinito.features.games.magic_8_ball import pick_answer
from kinito.features.games.memory import DEFAULT_PAIRS, build_deck, is_match
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
