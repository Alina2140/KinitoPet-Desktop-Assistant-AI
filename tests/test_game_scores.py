"""Tests for persistent mini-game highscores."""

from __future__ import annotations

import json
import os

import pytest

from kinito.features.games.scores import (
    DEFAULT_SCORES,
    TRIVIA_STREAK_THRESHOLD,
    GameScoresStore,
)


@pytest.fixture
def scores_dir(tmp_path):
    return str(tmp_path / "user_media")


@pytest.fixture
def store(scores_dir):
    return GameScoresStore(directory=scores_dir)


def test_defaults_when_missing(store):
    assert store.snake_highscore() == 0
    assert store.tetris_highscore() == 0
    assert store.memory_best_moves() is None
    assert store.number_guess_best_attempts() is None
    assert store.battleships_best_shots() is None
    assert store.trivia_best_score() == 0
    assert store.trivia_streak() == 0
    for key, value in DEFAULT_SCORES.items():
        assert store.get(key) == value


def test_record_snake_score_persists(store, scores_dir):
    assert store.record_snake_score(12) is True
    assert store.snake_highscore() == 12
    assert store.record_snake_score(8) is False
    assert store.snake_highscore() == 12
    assert store.record_snake_score(20) is True
    reloaded = GameScoresStore(directory=scores_dir)
    assert reloaded.snake_highscore() == 20


def test_record_tetris_score_persists(store, scores_dir):
    assert store.record_tetris_score(1200) is True
    assert store.tetris_highscore() == 1200
    assert store.record_tetris_score(800) is False
    assert store.tetris_highscore() == 1200
    assert store.record_tetris_score(2400) is True
    reloaded = GameScoresStore(directory=scores_dir)
    assert reloaded.tetris_highscore() == 2400


def test_record_memory_moves_keeps_lowest(store, scores_dir):
    assert store.record_memory_moves(18) is True
    assert store.memory_best_moves() == 18
    assert store.record_memory_moves(22) is False
    assert store.memory_best_moves() == 18
    assert store.record_memory_moves(14) is True
    reloaded = GameScoresStore(directory=scores_dir)
    assert reloaded.memory_best_moves() == 14


def test_record_number_guess_attempts_keeps_lowest(store, scores_dir):
    assert store.record_number_guess_attempts(6) is True
    assert store.number_guess_best_attempts() == 6
    assert store.record_number_guess_attempts(7) is False
    assert store.record_number_guess_attempts(3) is True
    reloaded = GameScoresStore(directory=scores_dir)
    assert reloaded.number_guess_best_attempts() == 3


def test_record_battleships_shots_keeps_lowest(store, scores_dir):
    assert store.record_battleships_shots(8) is True
    assert store.battleships_best_shots() == 8
    assert store.record_battleships_shots(9) is False
    assert store.record_battleships_shots(5) is True
    reloaded = GameScoresStore(directory=scores_dir)
    assert reloaded.battleships_best_shots() == 5


def test_record_trivia_score_best_and_streak(store, scores_dir):
    summary = store.record_trivia_score(4, total=5)
    assert summary["new_best"] is True
    assert summary["best"] == 4
    assert summary["streak"] == 1

    summary = store.record_trivia_score(5, total=5)
    assert summary["new_best"] is True
    assert summary["best"] == 5
    assert summary["streak"] == 2

    summary = store.record_trivia_score(TRIVIA_STREAK_THRESHOLD - 1, total=5)
    assert summary["new_best"] is False
    assert summary["best"] == 5
    assert summary["streak"] == 0

    reloaded = GameScoresStore(directory=scores_dir)
    assert reloaded.trivia_best_score() == 5
    assert reloaded.trivia_streak() == 0


def test_invalid_file_falls_back(scores_dir):
    os.makedirs(scores_dir, exist_ok=True)
    path = os.path.join(scores_dir, "game_scores.json")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("{not-json")
    store = GameScoresStore(directory=scores_dir)
    assert store.snake_highscore() == 0


def test_ignores_invalid_types(scores_dir):
    os.makedirs(scores_dir, exist_ok=True)
    path = os.path.join(scores_dir, "game_scores.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "version": 1,
                "snake_highscore": "nope",
                "memory_best_moves": True,
                "trivia_best_score": 3.0,
                "trivia_streak": -2,
            },
            handle,
        )
    store = GameScoresStore(directory=scores_dir)
    assert store.snake_highscore() == 0
    assert store.memory_best_moves() is None
    assert store.trivia_best_score() == 3
    assert store.trivia_streak() == 0
