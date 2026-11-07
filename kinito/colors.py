"""Small helpers for #rrggbb color strings."""

from __future__ import annotations

import re

_HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


def normalize_hex_color(value: object, default: str) -> str:
    """Return *value* as lowercase #rrggbb, or *default* when it is not a valid color."""
    if isinstance(value, str):
        candidate = value.strip()
        if _HEX_COLOR.match(candidate):
            return candidate.lower()
    return default


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    """Return the (red, green, blue) channels of a #rrggbb color."""
    return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)


def rgb_to_hex(red: int, green: int, blue: int) -> str:
    """Return a lowercase #rrggbb string, clamping each channel to 0–255."""
    return "#" + "".join(f"{max(0, min(255, int(c))):02x}" for c in (red, green, blue))


def lighten_hex(color: str, amount: float) -> str:
    """Blend *color* toward white by *amount* (0 keeps it, 1 is white)."""
    amount = max(0.0, min(1.0, amount))
    mixed = [round(channel + (255 - channel) * amount) for channel in hex_to_rgb(color)]
    return rgb_to_hex(*mixed)
