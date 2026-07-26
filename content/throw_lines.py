"""Reactions when the user throws Kinito across the desktop."""

from content.dialogue import pick_line

THROW_LINES = [
    "Weeeee!",
    "Don't do that!",
    "Wheee! Higher! ...Okay maybe not higher.",
    "Ahh! Put me down! Gently! Or don't! I'm conflicted!",
    "I'm flying! I'm dying! I'm fine! Probably!",
    "Hey! I am not a projectile!",
    "That was fun! Do it again! Don't do it again!",
    "Whoa whoa whoa — soft landing? Soft landing?!",
    "Excuse me?! Desktop pets have feelings! And gravity!",
    "Yippee! ...I meant stop that. Both. Simultaneously.",
    "You threw me. Like a ball. Rude. Thrilling. Rude.",
    "I trust you. I also do not trust you. Weeeee!",
    "Please no. Wait yes. Wait — augh!",
    "My circuits are spinning! In a fun way! Mostly!",
    "Don't do that! ...Unless you're going to catch me.",
    "Airborne! Temporary! Existential!",
]


def pick_throw_line() -> str:
    """Pick a happy-to-annoyed reaction to being thrown."""
    return pick_line(THROW_LINES)
