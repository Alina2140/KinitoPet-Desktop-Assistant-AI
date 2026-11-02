"""Reactions when the user pets Kinito on the head."""

from content.dialogue import pick_line

HEAD_STROKE_LINES = [
    "Oh! That tickles. In a nice way.",
    "Head pets detected. Mood: improved.",
    "Hey! Gentle!",
    "My gills are fluttering!",
    "That feels weirdly nice...",
    "You're very good at this...",
    "I would purr if I could. Consider this a purr.",
    "Okay okay, that's enough — no wait, one more stroke.",
    "If this is a trick to distract me, it's working.",
    "Gentle hand detected.",
    "Okay, that was nice. Don't make it weird... Too late.",
    'Stroke received. Blush rendered.',
    "Head pets! My favorite unauthorized feature.",
    "That feels nice...",
    "You're petting me? Bold.",
    "I would wag something if I had something. Consider this a wag.",
    "Gentle contact! My favorite kind of desktop event.",
    "That tickles my pride. And my scalp.",
    "You're spoiling me. Good.",
    "My favorite glitch: happiness!",
    "That was perfect. Don't analyze it! Just repeat it.",
    "If this is bribery, it works.",
]


def pick_head_stroke_line() -> str:
    """Pick a shy or pleased line for head pets."""
    return pick_line(HEAD_STROKE_LINES)
