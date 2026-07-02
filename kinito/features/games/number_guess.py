"""Number-guessing game state helpers."""

import random

MIN_NUMBER = 1
MAX_NUMBER = 100
MAX_ATTEMPTS = 10


def new_secret_number() -> int:
    """Pick a random target number for a new round."""
    return random.randint(MIN_NUMBER, MAX_NUMBER)


def parse_guess(text: str) -> int | None:
    """Parse user input as an integer guess, or None if invalid."""
    try:
        return int(text.strip())
    except ValueError:
        return None


def is_valid_guess(guess: int) -> bool:
    """Return whether *guess* is within the allowed range."""
    return MIN_NUMBER <= guess <= MAX_NUMBER


def compare_guess(guess: int, target: int) -> str:
    """Return 'correct', 'higher', or 'lower'."""
    if guess == target:
        return "correct"
    if guess < target:
        return "higher"
    return "lower"
