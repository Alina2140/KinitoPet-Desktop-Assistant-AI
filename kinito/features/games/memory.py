"""Memory card-pair logic."""

import random

# Single-codepoint symbols only — ZWJ sequences (e.g. eye-in-speech-bubble) render as two glyphs.
DEFAULT_PAIRS = ("🫀", "👁", "👋", "🫁", "🦴", "🕷", "🥀", "🥩")


def build_deck(pairs: tuple[str, ...] = DEFAULT_PAIRS) -> list[str]:
    """Return a shuffled list of card symbols (each symbol appears twice)."""
    deck = list(pairs) * 2
    random.shuffle(deck)
    return deck


def is_match(first: str, second: str) -> bool:
    """Return whether two revealed cards form a pair."""
    return first == second
