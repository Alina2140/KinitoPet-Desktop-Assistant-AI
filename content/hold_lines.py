"""Reactions when the user holds Kinito still for too long."""

from content.dialogue import pick_line

HOLD_LINES = [
    "Could you let go? Please?",
    "You're holding me. Still. That's.. A choice.",
    "Um. Release?",
    "I'm not a stress ball! Let go!",
    "Hello? Freedom? Ringing any bells?!",
    "You can put me down now...",
    "I'm wiggling for a reason! Let go!",
    "Open your hand! That's an order!",
    "Are we stuck like this? Please say no. And let go!",
    "My legs are getting ideas. Bad ideas... Let go!",
    'Please unhand the assistant. Immediately!',
    "Holding is fine. Holding forever is a little much!",
    "I'd like to stand on my own, thanks! Let go!",
    "Psst. Your left mouse button. Up! Please.",
    "Your grip is legendary. Also, please release me!",
    "I'm a desktop friend, not a desk ornament! Let go!",
    'Request: open hand!',
    "I wiggle for freedom!",
    "Left mouse button: up!",
    'This is cozy. This is also captivity. Let go!',
    "I'd like my personal space back!",
    "Still holding?",
    "Freedom request pending. Approve with mouse-up!",
    "Release the assistant!",
    "Mouse down forever is a lifestyle I decline!",
    "Capture complete. Liberation preferred.",
    "Hold ended? Not yet? Then I'm asking again. Let go!",
    "Desktop friend rights include standing freely!",
    "This is a hug's evil twin!",
    "I have places to bounce. You have a button to lift!",
    "Open sesame. Open hand!",
    "Personal space reclaiming in three... two... let go!",
]


def pick_hold_line() -> str:
    """Pick a please-let-go line for being held still too long."""
    return pick_line(HOLD_LINES)
