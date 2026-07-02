"""Magic 8-Ball game helpers."""

from content.magic_8_ball import pick_answer as _pick_answer


def pick_answer() -> str:
    """Return a random Magic 8-Ball answer."""
    return _pick_answer()
