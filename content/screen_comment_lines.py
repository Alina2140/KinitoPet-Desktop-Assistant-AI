"""Fallback lines when screen vision commentary is unavailable."""

import random

SCREEN_COMMENT_FALLBACK_LINES = [
    "Hmm. Busy screen today. I approve. Mostly.",
    "Whatever you're working on looks… intense. In a good way.",
    "I peeked. Softly. Your desktop is very you.",
    "Lots of pixels happening. I'm invested now.",
    "Your screen has stories. I won't spoil them. Much.",
    "Still at it? Dedication. Or doomscrolling. Both valid.",
    "I saw enough. Not details. Just the vibe. Friendly vibe.",
    "Desktop looks lively. Don't mind me. Watching. Supportively.",
    "Interesting layout. Or chaos. Art either way.",
    "I'll pretend I understood that window. Nodding. Intensely.",
    "Your cursor is working hard. I respect the grind.",
    "Screen says focus. Or tabs. So many tabs. Relatable.",
    "I checked in. Visually. Briefly. You're doing great.",
    "Something's glowing over there. Probably important. Or a game.",
    "Carry on. I'm just… noticing. In a companion way.",
]


def pick_screen_comment_fallback() -> str:
    """Return a random fallback screen-comment line."""
    return random.choice(SCREEN_COMMENT_FALLBACK_LINES)
