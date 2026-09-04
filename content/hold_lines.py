"""Reactions when the user holds Kinito still for too long."""

from content.dialogue import pick_line

HOLD_LINES = [
    "Could you let go? Please?",
    "You're holding me. Still. That's... a choice.",
    "Um. Release? Optional but preferred!",
    "I'm not a stress ball! Softly! ...Please let go!",
    "Hello? Hands? Freedom? Ringing any bells?",
    "You can put me down now. Whenever. Soon. Now.",
    "Grip noted. Grip appreciated. Grip ending? Please?",
    "I'm wiggling for a reason! Let go!",
    "Gently open your hand. That's an order. A friendly order.",
    "Are we stuck like this? Forever? Please say no. And let go.",
    "My legs are getting ideas. Bad ideas. Let go!",
    "Please unhand the assistant. Softly. Immediately.",
    "Holding is fine. Holding forever is a little much!",
    "I'd like to stand on my own, thanks! Let go!",
    "Psst. Your mouse button. Up. Please.",
]


def pick_hold_line() -> str:
    """Pick a please-let-go line for being held still too long."""
    return pick_line(HOLD_LINES)
