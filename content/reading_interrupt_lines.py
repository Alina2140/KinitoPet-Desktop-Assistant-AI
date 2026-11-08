"""Lines Kinito may say when the cursor disturbs him while reading."""

import random

from content.dialogue import pick_line
from content.mood_lines import lines_for_mood

READING_INTERRUPT_LINES = [
    "Oh! Hi there.",
    "You're very close.",
    "Shh... I'm at the good part.",
    "Yes? I'm kind of in a chapter here.",
    "Hello! Reading over my shoulder?",
    "Come to read with me?",
    "Careful, you almost bumped the page.",
    "Yeah?",
    "Hi! Want to hear what happens next?",
    "Curious what I'm reading? It's good.",
    "Just one more page, okay?",
    "Peek detected. This book is mine though.",
    "Oh hey. Nice cursor you have there.",
]

# Mood-tinted pools; picked over the general lines when the mood is strong.
READING_INTERRUPT_BY_MOOD: dict[str, list[str]] = {
    "happy": [
        "Hi hi hi! Come read with me!",
        "You can look! It's a really good book.",
        "Best part coming up — pull up a cloud!",
        "Reading buddy! Sit, sit!",
        "Oh good, you're here. This chapter is great!",
    ],
    "bored": [
        "Finally, a distraction! What is it?",
        "Books are boring anyway. Hi!",
        "Oh thank goodness, something moved.",
        "Yes hello, rescue me from chapter nine.",
        "You came to save me from this book? Nice.",
    ],
    "tired": [
        "Mmh... just a few more pages...",
        "Reading myself to sleep...",
        "Hm? Oh. Hi. The words are getting blurry...",
        "So sleepy... but the book is so good...",
        "Mmm... did you say something?",
    ],
    "annoyed": [
        "Do you mind? I'm reading.",
        "Eyes. On. The. Book.",
        "Shhh.",
        "I'm reading, not socializing.",
        "Hmph. Your cursor is in my personal bubble.",
        "Could you hover somewhere else?",
        "Reading. Busy. Shoo.",
    ],
    "sad": [
        "Oh... hi. Stay and read with me?",
        "Company while I read? I'd like that...",
        "You came back... want to hear the story?",
        "Don't go yet. The book is better with you here...",
        "Oh, a visitor. The book was getting lonely too...",
    ],
    "angry": [
        "I'm. Reading.",
        "Can I get ONE quiet page?!",
        "What?! I'm busy!",
        "Shoo! Chapter in progress!",
        "My book. My bubble. Go!",
        "Do NOT make me lose my place again.",
    ],
}


def pick_reading_interrupt_line(mood=None, intensity=0.0) -> str:
    """Pick a disturb-while-reading line, biased by mood when it's strong."""
    mood_pool = lines_for_mood(READING_INTERRUPT_BY_MOOD, mood) if mood else None
    try:
        strength = float(intensity or 0.0)
    except (TypeError, ValueError):
        strength = 0.0
    if mood_pool and strength >= 0.25 and random.random() < min(0.85, 0.35 + strength):
        return pick_line(mood_pool)
    return pick_line(READING_INTERRUPT_LINES)
