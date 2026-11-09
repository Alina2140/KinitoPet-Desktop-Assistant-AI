"""Small helpers for #rrggbb color strings."""

from __future__ import annotations

import re

_HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")

RAINBOW_COLOR = "rainbow"
RAINBOW_COLORS = (
    "#ef4444",
    "#f97316",
    "#facc15",
    "#22c55e",
    "#14b8a6",
    "#3b82f6",
    "#a855f7",
)


def rainbow_at(index: int) -> str:
    """Return the rainbow stripe color for *index* (cycles through RAINBOW_COLORS)."""
    return RAINBOW_COLORS[index % len(RAINBOW_COLORS)]


def normalize_hex_color(value: object, default: str) -> str:
    """Return *value* as lowercase #rrggbb (or "rainbow"), else *default*."""
    if isinstance(value, str):
        candidate = value.strip()
        if _HEX_COLOR.match(candidate):
            return candidate.lower()
        if candidate.lower() == RAINBOW_COLOR:
            return RAINBOW_COLOR
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


def darken_hex(color: str, amount: float) -> str:
    """Blend *color* toward black by *amount* (0 keeps it, 1 is black)."""
    amount = max(0.0, min(1.0, amount))
    return rgb_to_hex(*(round(channel * (1 - amount)) for channel in hex_to_rgb(color)))


def brightness(color: str) -> float:
    """Return the perceived brightness of *color* from 0 (black) to 1 (white)."""
    red, green, blue = hex_to_rgb(color)
    return (0.299 * red + 0.587 * green + 0.114 * blue) / 255
