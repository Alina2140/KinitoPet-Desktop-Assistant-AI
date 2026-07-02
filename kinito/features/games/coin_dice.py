"""Coin flip and dice roll game logic."""

import random
from typing import Literal

HEADS = "heads"
TAILS = "tails"


def flip_coin() -> str:
    """Return 'heads' or 'tails'."""
    return random.choice([HEADS, TAILS])


def roll_dice() -> int:
    """Return a random integer from 1 to 6."""
    return random.randint(1, 6)


def coin_outcome(guess: str, result: str) -> Literal["win", "lose"]:
    """Compare the player's guess to the coin result."""
    if guess.lower() == result:
        return "win"
    return "lose"


def dice_outcome(guess: int, roll: int) -> Literal["win", "lose"]:
    """Compare the player's guess to the dice roll."""
    if guess == roll:
        return "win"
    return "lose"
