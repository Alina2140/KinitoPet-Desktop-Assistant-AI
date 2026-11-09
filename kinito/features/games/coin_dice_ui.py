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
