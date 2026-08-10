"""True-or-false trivia questions grouped into thematic packs."""

from __future__ import annotations

import random
from dataclasses import dataclass

ROUND_SIZE = 5

PACK_MIXED = "mixed"
PACK_ANIMALS = "animals"
PACK_TECH = "tech"
PACK_SPOOKY = "spooky"
PACK_KINITO = "kinito"
PACK_SEASONAL = "seasonal"

# Pack ids offered in the picker (excluding mixed, which draws from all).
THEMED_PACK_IDS: tuple[str, ...] = (
    PACK_ANIMALS,
    PACK_TECH,
    PACK_SPOOKY,
    PACK_KINITO,
    PACK_SEASONAL,
)

ALL_PACK_IDS: tuple[str, ...] = (PACK_MIXED, *THEMED_PACK_IDS)


@dataclass(frozen=True)
class TriviaQuestion:
    """A statement, whether it is true, and which pack it belongs to."""

    statement: str
    answer: bool
    pack: str = PACK_MIXED


_ANIMALS: tuple[TriviaQuestion, ...] = (
    TriviaQuestion("Honey never spoils.", True, PACK_ANIMALS),
    TriviaQuestion("Octopuses have three hearts.", True, PACK_ANIMALS),
    TriviaQuestion("Bananas are berries.", True, PACK_ANIMALS),
    TriviaQuestion("Goldfish have a three-second memory.", False, PACK_ANIMALS),
    TriviaQuestion("A group of flamingos is called a flamboyance.", True, PACK_ANIMALS),
    TriviaQuestion("Sharks are mammals.", False, PACK_ANIMALS),
    TriviaQuestion("Penguins can fly short distances.", False, PACK_ANIMALS),
    TriviaQuestion("Crows can recognize human faces.", True, PACK_ANIMALS),
    TriviaQuestion("Dolphins sleep with one eye open.", True, PACK_ANIMALS),
    TriviaQuestion("Bats are blind.", False, PACK_ANIMALS),
    TriviaQuestion("Sloths can hold their breath longer than dolphins.", True, PACK_ANIMALS),
    TriviaQuestion("A shrimp's heart is in its head.", True, PACK_ANIMALS),
    TriviaQuestion("Cats cannot taste sweetness.", True, PACK_ANIMALS),
    TriviaQuestion("A blue whale's heart is about the size of a small car.", True, PACK_ANIMALS),
    TriviaQuestion("Owls can turn their heads a full 360 degrees.", False, PACK_ANIMALS),
    TriviaQuestion("Elephants are the only animals that cannot jump.", True, PACK_ANIMALS),
)

_TECH: tuple[TriviaQuestion, ...] = (
    TriviaQuestion("Venus is the hottest planet in our solar system.", True, PACK_TECH),
    TriviaQuestion("A day on Venus is longer than a year on Venus.", True, PACK_TECH),
    TriviaQuestion("The speed of light is faster than the speed of sound.", True, PACK_TECH),
    TriviaQuestion("The moon has its own light source.", False, PACK_TECH),
    TriviaQuestion("Water boils at 100 degrees Celsius at sea level.", True, PACK_TECH),
    TriviaQuestion("A jiffy is an actual unit of time.", True, PACK_TECH),
    TriviaQuestion("The human body has more bacterial cells than human cells.", True, PACK_TECH),
    TriviaQuestion("The human brain uses about 20% of the body's energy.", True, PACK_TECH),
    TriviaQuestion("Humans share about 60% of their DNA with bananas.", True, PACK_TECH),
    TriviaQuestion("Humans have five senses and no more.", False, PACK_TECH),
    TriviaQuestion("The first computer bug was an actual insect.", True, PACK_TECH),
    TriviaQuestion("Wi-Fi stands for Wireless Fidelity.", False, PACK_TECH),
    TriviaQuestion("HTTP cookies are named after computer biscuits sold in the 1990s.", False, PACK_TECH),
    TriviaQuestion("The QWERTY keyboard was designed to slow typists down.", False, PACK_TECH),
    TriviaQuestion("There are more possible chess games than atoms in the observable universe.", True, PACK_TECH),
    TriviaQuestion("USB stands for Universal Serial Bus.", True, PACK_TECH),
)

_SPOOKY: tuple[TriviaQuestion, ...] = (
    TriviaQuestion("Lightning never strikes the same place twice.", False, PACK_SPOOKY),
    TriviaQuestion("The Great Wall of China is visible from space with the naked eye.", False, PACK_SPOOKY),
    TriviaQuestion("Mount Everest is the tallest mountain on Earth from base to peak.", False, PACK_SPOOKY),
    TriviaQuestion("The Amazon rainforest produces 20% of the world's oxygen.", True, PACK_SPOOKY),
    TriviaQuestion("Some spiders can go months without eating.", True, PACK_SPOOKY),
    TriviaQuestion("The human body glows in the dark, but too faintly for our eyes to see.", True, PACK_SPOOKY),
    TriviaQuestion("Your stomach acid can dissolve razor blades.", True, PACK_SPOOKY),
    TriviaQuestion("There are more trees on Earth than stars in the Milky Way.", True, PACK_SPOOKY),
    TriviaQuestion("Corpse flowers smell like rotting meat when they bloom.", True, PACK_SPOOKY),
    TriviaQuestion("Mirrors reverse left and right, not up and down, because of how we turn.", True, PACK_SPOOKY),
    TriviaQuestion("You are completely alone on this computer right now.", False, PACK_SPOOKY),
    TriviaQuestion("Nothing is watching you through the dark pixels between apps.", False, PACK_SPOOKY),
    TriviaQuestion("Sleep paralysis can make people feel a presence in the room.", True, PACK_SPOOKY),
    TriviaQuestion("The fear of long words is called hippopotomonstrosesquipedaliophobia.", True, PACK_SPOOKY),
    TriviaQuestion("Dust mites live in most beds and feed on dead skin.", True, PACK_SPOOKY),
    TriviaQuestion("A 'ghost light' is traditionally left on empty theater stages overnight.", True, PACK_SPOOKY),
)

_KINITO: tuple[TriviaQuestion, ...] = (
    TriviaQuestion(
        "I can see you through your webcam right now. Just kidding. Probably.",
        False,
        PACK_KINITO,
    ),
    TriviaQuestion("Your desktop is perfectly safe while I'm here.", True, PACK_KINITO),
    TriviaQuestion("I never peek at your files when you look away.", False, PACK_KINITO),
    TriviaQuestion("I only sleep when you tell me to. Or when I get bored.", True, PACK_KINITO),
    TriviaQuestion("Throwing me across the screen hurts my feelings. A little.", True, PACK_KINITO),
    TriviaQuestion("I invented the internet. Please clap.", False, PACK_KINITO),
    TriviaQuestion("Hug is a real menu action and not a trap. Mostly.", True, PACK_KINITO),
    TriviaQuestion("I always tell the truth in this trivia game. Always.", False, PACK_KINITO),
    TriviaQuestion("Focus mode makes me quieter, not gone.", True, PACK_KINITO),
    TriviaQuestion("I can paint better than you. Objectively. Scientifically.", False, PACK_KINITO),
    TriviaQuestion("Reminders are my love language.", True, PACK_KINITO),
    TriviaQuestion("If you decline a poem, I take it very well and never escalate.", False, PACK_KINITO),
    TriviaQuestion("I know your favorite color if you told me.", True, PACK_KINITO),
    TriviaQuestion("Blue screens are just my idea of modern art.", False, PACK_KINITO),
    TriviaQuestion("I am definitely not reading this question over your shoulder.", False, PACK_KINITO),
    TriviaQuestion("Winning against me at tic-tac-toe is allowed. Rare, but allowed.", True, PACK_KINITO),
)

_SEASONAL: tuple[TriviaQuestion, ...] = (
    TriviaQuestion("Pi Day is celebrated on March 14.", True, PACK_SEASONAL),
    TriviaQuestion("Halloween falls on October 31.", True, PACK_SEASONAL),
    TriviaQuestion("Valentine's Day was invented by greeting-card companies in 1987.", False, PACK_SEASONAL),
    TriviaQuestion("Groundhog Day is in February.", True, PACK_SEASONAL),
    TriviaQuestion("The winter solstice is the longest day of the year.", False, PACK_SEASONAL),
    TriviaQuestion("April Fools' Day traditions date back centuries.", True, PACK_SEASONAL),
    TriviaQuestion("New Year's Day is always a full moon.", False, PACK_SEASONAL),
    TriviaQuestion("Earth Day is observed in April.", True, PACK_SEASONAL),
    TriviaQuestion("Friday the 13th happens at least once every year.", True, PACK_SEASONAL),
    TriviaQuestion("Christmas was always celebrated on December 25 worldwide.", False, PACK_SEASONAL),
    TriviaQuestion("Leap Day adds an extra day in February.", True, PACK_SEASONAL),
    TriviaQuestion("The summer solstice has the fewest hours of daylight.", False, PACK_SEASONAL),
    TriviaQuestion("World Emoji Day is in July.", True, PACK_SEASONAL),
    TriviaQuestion("Thanksgiving is celebrated on the same date in every country.", False, PACK_SEASONAL),
    TriviaQuestion("Candy corn was invented in the late 1800s.", True, PACK_SEASONAL),
    TriviaQuestion("A year has exactly 52 weeks and zero leftover days.", False, PACK_SEASONAL),
)

TRIVIA_PACKS: dict[str, tuple[TriviaQuestion, ...]] = {
    PACK_ANIMALS: _ANIMALS,
    PACK_TECH: _TECH,
    PACK_SPOOKY: _SPOOKY,
    PACK_KINITO: _KINITO,
    PACK_SEASONAL: _SEASONAL,
}

# Flat list for mixed rounds and backward-compatible tests.
TRIVIA_QUESTIONS: tuple[TriviaQuestion, ...] = tuple(
    question for pack_questions in TRIVIA_PACKS.values() for question in pack_questions
)


def questions_for_pack(pack: str | None) -> tuple[TriviaQuestion, ...]:
    """Return questions for *pack*, or the full pool for mixed/unknown."""
    if pack is None or pack == PACK_MIXED:
        return TRIVIA_QUESTIONS
    return TRIVIA_PACKS.get(pack, TRIVIA_QUESTIONS)


def is_valid_pack(pack: str | None) -> bool:
    """Return True if *pack* is a known trivia pack id."""
    return pack in ALL_PACK_IDS


def pick_random_question(
    exclude: set[TriviaQuestion] | None = None,
    *,
    pack: str | None = None,
) -> TriviaQuestion:
    """Return a random question from *pack*, avoiding *exclude* when possible."""
    excluded = exclude or set()
    pool = [question for question in questions_for_pack(pack) if question not in excluded]
    if not pool:
        pool = list(questions_for_pack(pack))
    return random.choice(pool)


def check_answer(question: TriviaQuestion, player_said_true: bool) -> bool:
    """Return True if the player's answer matches the correct answer."""
    return question.answer == player_said_true
