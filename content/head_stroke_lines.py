"""Reactions when the user pets Kinito on the head."""

from content.dialogue import pick_line

HEAD_STROKE_LINES = [
    "Oh! That tickles. In a nice way.",
    "Head pets detected. Mood: improved.",
    "Hey. Gentle. I'm blushing. You can't see it. ...You can.",
    "Soft strokes on the head? I'll allow it.",
    "My gills are fluttering. That's a compliment.",
    "Keep going. Or don't. I'm not the boss of your hand.",
    "That feels weirdly nice. Don't tell anyone.",
    "Blush mode: engaged. Thank you.",
    "You're very good at this. Suspiciously good.",
    "I would purr if I could. Consider this a purr.",
    "Warm fuzzies. Literal fuzzies. On my head.",
    "Okay okay, that's enough— no wait, one more stroke.",
    "My face is warm. Your fault. I approve.",
    "Petting the assistant: officially supported.",
    "If this is a trick to distract me, it's working.",
]


def pick_head_stroke_line() -> str:
    """Pick a shy or pleased line for head pets."""
    return pick_line(HEAD_STROKE_LINES)
