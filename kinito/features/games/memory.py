"""Memory card-pair logic."""

import random

# Single-codepoint symbols only — ZWJ sequences (e.g. eye-in-speech-bubble) render as two glyphs.
DEFAULT_PAIRS = (
    "🫀",
    "👁",
    "👋",
    "🫁",
    "🦴",
    "🕷",
    "🥀",
    "🥩",
    "🧠",
    "🦷",
    "🩸",
    "💀",
    "🐍",
    "🕸️",
    "🪱",
    "🔪",
)

# How many pairs the player can choose before / during a game.
PAIR_OPTIONS = (8, 12, 16)
DEFAULT_PAIR_COUNT = 16

# (rows, cols) for each supported pair count (rows * cols == pair_count * 2).
_GRID_SHAPES: dict[int, tuple[int, int]] = {
    8: (4, 4),
    12: (4, 6),
    16: (4, 8),
}


def normalize_pair_count(pair_count: int | None) -> int:
    """Clamp *pair_count* to a supported option (default: full board)."""
    if pair_count in PAIR_OPTIONS:
        return int(pair_count)
    return DEFAULT_PAIR_COUNT


def select_pairs(pair_count: int | None = None) -> tuple[str, ...]:
    """Return the first *pair_count* symbols from the default pool."""
    count = normalize_pair_count(pair_count)
    return DEFAULT_PAIRS[:count]


def grid_shape(pair_count: int | None = None) -> tuple[int, int]:
    """Return (rows, cols) for the given pair count."""
    count = normalize_pair_count(pair_count)
    return _GRID_SHAPES[count]


def build_deck(pairs: tuple[str, ...] | None = None) -> list[str]:
    """Return a shuffled list of card symbols (each symbol appears twice)."""
    chosen = pairs if pairs is not None else DEFAULT_PAIRS
    deck = list(chosen) * 2
    random.shuffle(deck)
    return deck


def is_match(first: str, second: str) -> bool:
    """Return whether two revealed cards form a pair."""
    return first == second
