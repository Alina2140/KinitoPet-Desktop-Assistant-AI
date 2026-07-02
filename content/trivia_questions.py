"""True-or-false trivia questions with verified answers."""

from __future__ import annotations

import random
from dataclasses import dataclass

ROUND_SIZE = 5


@dataclass(frozen=True)
class TriviaQuestion:
    """A statement and whether it is true."""

    statement: str
    answer: bool


TRIVIA_QUESTIONS: tuple[TriviaQuestion, ...] = (
    TriviaQuestion("The Great Wall of China is visible from space with the naked eye.", False),
    TriviaQuestion("Honey never spoils.", True),
    TriviaQuestion("Octopuses have three hearts.", True),
    TriviaQuestion("Lightning never strikes the same place twice.", False),
    TriviaQuestion("Bananas are berries.", True),
    TriviaQuestion("Humans share about 60% of their DNA with bananas.", True),
    TriviaQuestion("Goldfish have a three-second memory.", False),
    TriviaQuestion("Venus is the hottest planet in our solar system.", True),
    TriviaQuestion("A group of flamingos is called a flamboyance.", True),
    TriviaQuestion("Sharks are mammals.", False),
    TriviaQuestion("The human body has more bacterial cells than human cells.", True),
    TriviaQuestion("Mount Everest is the tallest mountain on Earth from base to peak.", False),
    TriviaQuestion("A day on Venus is longer than a year on Venus.", True),
    TriviaQuestion("Penguins can fly short distances.", False),
    TriviaQuestion("The speed of light is faster than the speed of sound.", True),
    TriviaQuestion("Tomatoes are vegetables.", False),
    TriviaQuestion("The moon has its own light source.", False),
    TriviaQuestion("Crows can recognize human faces.", True),
    TriviaQuestion("Water boils at 100 degrees Celsius at sea level.", True),
    TriviaQuestion("I can see you through your webcam right now. Just kidding. Probably.", False),
    TriviaQuestion("Dolphins sleep with one eye open.", True),
    TriviaQuestion("The human brain uses about 20% of the body's energy.", True),
    TriviaQuestion("Bats are blind.", False),
    TriviaQuestion("A jiffy is an actual unit of time.", True),
    TriviaQuestion("Your desktop is perfectly safe while I'm here.", True),
    TriviaQuestion("Sloths can hold their breath longer than dolphins.", True),
    TriviaQuestion("The Amazon rainforest produces 20% of the world's oxygen.", True),
    TriviaQuestion("Humans have five senses and no more.", False),
    TriviaQuestion("A shrimp's heart is in its head.", True),
    TriviaQuestion("I never peek at your files when you look away.", False),
)


def pick_random_question(exclude: set[TriviaQuestion] | None = None) -> TriviaQuestion:
    """Return a random question not in *exclude*."""
    excluded = exclude or set()
    pool = [question for question in TRIVIA_QUESTIONS if question not in excluded]
    if not pool:
        pool = list(TRIVIA_QUESTIONS)
    return random.choice(pool)


def check_answer(question: TriviaQuestion, player_said_true: bool) -> bool:
    """Return True if the player's answer matches the correct answer."""
    return question.answer == player_said_true
