"""PIL-drawn die faces for the dice-guess response buttons."""

from __future__ import annotations

import tkinter as tk

DIE_FACE_SIZE = 30

_PIPS = {
    1: ((0.5, 0.5),),
    2: ((0.30, 0.30), (0.70, 0.70)),
    3: ((0.28, 0.28), (0.5, 0.5), (0.72, 0.72)),
    4: ((0.30, 0.30), (0.70, 0.30), (0.30, 0.70), (0.70, 0.70)),
    5: (
        (0.28, 0.28),
        (0.72, 0.28),
        (0.5, 0.5),
        (0.28, 0.72),
        (0.72, 0.72),
    ),
    6: (
        (0.30, 0.25),
        (0.70, 0.25),
        (0.30, 0.5),
        (0.70, 0.5),
        (0.30, 0.75),
        (0.70, 0.75),
    ),
}


def dice_face_image(master, value: int, size: int = DIE_FACE_SIZE) -> tk.PhotoImage | None:
    """Return a *size* px die face showing *value* pips (None without PIL)."""
    try:
        from PIL import Image, ImageDraw, ImageTk
    except Exception:
        return None
    try:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        margin = max(1, int(size * 0.04))
        draw.rounded_rectangle(
            (margin, margin, size - margin - 1, size - margin - 1),
            radius=int(size * 0.18),
            fill="#fdfdfd",
            outline="#202020",
            width=max(1, int(size * 0.05)),
        )
        r = max(2, int(size * 0.09))
        for fx, fy in _PIPS.get(value, ()):
            cx, cy = int(fx * size), int(fy * size)
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill="#202020")
        return ImageTk.PhotoImage(img, master=master)
    except Exception:
        return None


COIN_SIZE = 30


def _coin_base(draw, size: int) -> None:
    """Paint a gold coin body inside the current RGBA canvas."""
    m = max(1, int(size * 0.04))
    edge = "#8a6d1f"
    face = "#e8c452"
    draw.ellipse((m, m, size - m - 1, size - m - 1), fill=face, outline=edge,
                 width=max(1, int(size * 0.05)))
    inner = m + max(1, int(size * 0.10))
    draw.ellipse(
        (inner, inner, size - inner - 1, size - inner - 1),
        outline=edge,
        width=1,
    )


def _star_points(cx: float, cy: float, outer: float, inner: float) -> list:
    """Return polygon points of a five-pointed star."""
    import math

    points = []
    for i in range(10):
        radius = outer if i % 2 == 0 else inner
        angle = -math.pi / 2 + i * math.pi / 5
        points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return points


def coin_face_image(master, side: str, size: int = COIN_SIZE) -> tk.PhotoImage | None:
    """Return a *size* px coin for *side* ("heads" or "tails"), None without PIL."""
    try:
        from PIL import Image, ImageDraw, ImageTk
    except Exception:
        return None
    try:
        scale = 4
        big = size * scale
        img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        _coin_base(draw, big)
        dark = "#8a6d1f"
        c = big // 2
        if side == "heads":
            # Profile bust: head circle plus a small neck/shoulder wedge.
            hr = int(big * 0.20)
            draw.ellipse(
                (c - hr, c - int(big * 0.30) - hr // 2,
                 c + hr, c - int(big * 0.30) + hr * 3 // 2),
                fill=dark,
            )
            draw.polygon(
                [
                    (c - hr, c + int(big * 0.22)),
                    (c + hr, c + int(big * 0.22)),
                    (c + int(hr * 1.3), c + int(big * 0.34)),
                    (c - int(hr * 1.3), c + int(big * 0.34)),
                ],
                fill=dark,
            )
        else:
            # Tails: big five-pointed star.
            draw.polygon(
                _star_points(c, c, int(big * 0.30), int(big * 0.13)),
                fill=dark,
            )
        img = img.resize((size, size), Image.LANCZOS)
        return ImageTk.PhotoImage(img, master=master)
    except Exception:
        return None
