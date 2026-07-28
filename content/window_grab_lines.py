"""Lines spoken when Kinito grabs and moves a desktop window."""

from content.dialogue import pick_line

WINDOW_GRAB_LINES = [
    "Just a little rearrange. Trust me.",
    "This window looked lonely over there.",
    "Helping! With windows! You're welcome!",
    "Oops. My hand slipped. On purpose.",
    "Desktop feng shui. Expert level.",
    "Don't mind me. Just tidying. Aggressively.",
    "Windows are toys. Temporary toys.",
    "I can put it back. Maybe. Later.",
    "Grab. Pull. Perfect. Ish.",
    "Your layout needed personality. Mine.",
]


def pick_window_grab_line() -> str:
    """Pick a mischievous line for a window-grab moment."""
    return pick_line(WINDOW_GRAB_LINES)
