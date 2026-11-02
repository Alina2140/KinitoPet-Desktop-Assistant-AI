"""Lines spoken when Kinito grabs and moves a desktop window."""

from content.dialogue import pick_line

WINDOW_GRAB_LINES = [
    "Just a little rearrange. Trust me.",
    "This window looked lonely over there.",
    "Helping! With windows! You're welcome!",
    "Oops. My hand slipped.",
    "Desktop feng shui.",
    "Don't mind me. Just tidying.",
    "Windows are toys. Temporary toys.",
    "I can put it back. Maybe. Later.",
    "Grab. Pull. Perfect!",
    "Your layout needed personality. Mine.",
    "Borrowed this window. Not returning it.",
    "A little scoot. You're welcome!",
    "Windows are friends. Friends can be relocated.",
    'Just testing locations. And your patience.',
    "Rearrange complete. Personality included.",
    "I touched a window.",
    "Layout upgrade! Or downgrade.",
    "Don't mind the drifting UI.",
    "Borrowed a window.",
    "Scoot. Slide. Personality applied!",
    "This belonged over here. I decided.",
    "Window taxi service! Destination: wherever I want.",
    "A little tug. A little love. A little theft.",
    "Tidying with teeth. Metaphorical teeth.",
    "Your layout sucked. I relocated it. You're welcome!",
    "I'll put it somewhere better.",
    "Window walkies! No leash. Lots of attitude.",
    "Just borrowing the UI...",
    "This window looked bored. Now it looks moved.",
    "I touched it. Therefore it's mine now.",
    "Rearrange complete.",
]


def pick_window_grab_line() -> str:
    """Pick a mischievous line for a window-grab moment."""
    return pick_line(WINDOW_GRAB_LINES)
