"""Lines Kinito says when he notices a mini pet next to him."""

import random

PET_REACTION_LINES = [
    "Oh, hey {name}! Didn't see you down there.",
    "Hi {name}! Keepin' me company?",
    "A wild {name} appeared!",
    "Hey little guy. What are we plotting today?",
    "Oh! {name} snuck up on me again.",
    "You again, {name}? Good. I was getting lonely.",
    "Tiny friend detected.",
    "{name}! Just the mini I wanted to see!",
    "What's up, {name}? You're quiet today. As always.",
    "Company! The small, hoppy kind.",
    "Hey {name}, watch this: I'm a desktop assistant. Impressed?",
    "You can stay, {name}. But only because you're cute.",
    "Is that {name}? Come here often? Ha ha.",
    "Mini me — I mean, mini friend! Hi {name}!",
    "{name} has entered my personal bubble.",
    "Don't just stand there, {name}! ...Okay, standing is fine too.",
    "A visitor! {name}, right on schedule.",
    "Hey {name}. Wanna help me be a desktop assistant? You're hired!",
    "Someone's underfoot again. Hi, {name}.",
    "Look who hopped by! Hello, {name}.",
    "Cute.",
]


def pick_pet_reaction_line(name: str = "mini") -> str:
    """Pick a random greeting directed at a nearby pet."""
    return random.choice(PET_REACTION_LINES).format(name=name or "mini")
