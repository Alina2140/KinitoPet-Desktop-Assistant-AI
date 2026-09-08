"""Reactions when the user spins the cursor around Kinito."""

from content.dialogue import pick_line

DIZZY_LINES = [
    "Whoa— stop spinning! I'm getting dizzy!",
    "The room is rotating. You're doing that. Please stop.",
    "Round and round and— okay I need a minute.",
    "My eyes are spinning faster than my thoughts!",
    "If this is a game, I lose. Vertigo: 1. Kinito: 0.",
    "Circles! So many circles! Fewer circles!",
    "I can still see you. Unfortunately. Everything else is blurry.",
    "Are we orbiting? Am I the planet? I don't like this astronomy!",
    "Hold still! Or let me hold still! Something hold still!",
    "Dizzy. Very dizzy. Was that fun for you? Rude.",
    "My balance.exe has stopped responding.",
    "Spinning is for tops. I am not a top. Help.",
    "Okay okay okay— world, please stop moving. Thanks in advance.",
    "You circled me. Multiple times. That was a choice. A dizzy choice.",
    "I followed you with my eyes and now my eyes want a nap.",
]


def pick_dizzy_line() -> str:
    """Pick a dizzy reaction for being orbited by the cursor."""
    return pick_line(DIZZY_LINES)
