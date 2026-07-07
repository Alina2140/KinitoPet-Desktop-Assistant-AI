"""Chamfered speech-bubble chrome and action buttons."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont


def chamfered_rect_points(x: float, y: float, width: float, height: float, chamfer: int) -> list[float]:
    """Return polygon points for a rectangle with clipped corners."""
    chamfer = max(1, min(chamfer, int(width // 2), int(height // 2)))
    return [
        x + chamfer,
        y,
        x + width - chamfer,
        y,
        x + width,
        y + chamfer,
        x + width,
        y + height - chamfer,
        x + width - chamfer,
        y + height,
        x + chamfer,
        y + height,
        x,
        y + height - chamfer,
        x,
        y + chamfer,
    ]


def outline_canvas_pad(border_width: int) -> int:
    """Return extra canvas padding so stroked outlines are not clipped."""
    return max(1, border_width)


def measure_chamfered_button(
    parent,
    *,
    text: str,
    font,
    padx: int,
    pady: int,
    chamfer: int,
    border_width: int,
    width: int | None = None,
) -> tuple[int, int]:
    """Return the pixel size a chamfered button needs for *text*."""
    font_obj = tkfont.Font(font=font, root=parent)
    text_width = font_obj.measure(text)
    if width is not None:
        text_width = max(text_width, width * font_obj.measure("0"))
    text_height = font_obj.metrics("linespace")
    inset = chamfer + border_width
    pad = outline_canvas_pad(border_width)
    return (
        text_width + (2 * padx) + (2 * inset) + (2 * pad),
        text_height + (2 * pady) + (2 * inset) + (2 * pad),
    )


class ChamferedButton(tk.Canvas):
    """Canvas button with clipped corners matching the speech bubble."""

    def __init__(
        self,
        parent,
        *,
        text: str,
        command,
        font,
        bg: str,
        active_bg: str,
        fg: str,
        border: str,
        border_width: int,
        chamfer: int,
        padx: int,
        pady: int,
        width: int | None = None,
        cursor: str = "hand2",
    ) -> None:
        self._text = text
        self._command = command
        self._font = font
        self._bg = bg
        self._active_bg = active_bg
        self._fg = fg
        self._border = border
        self._border_width = border_width
        self._chamfer = chamfer
        self._padx = padx
        self._pady = pady
        self._char_width = width
        self._hover = False
        self._outline_pad = outline_canvas_pad(border_width)
        button_w, button_h = measure_chamfered_button(
            parent,
            text=text,
            font=font,
            padx=padx,
            pady=pady,
            chamfer=chamfer,
            border_width=border_width,
            width=width,
        )
        super().__init__(
            parent,
            width=button_w,
            height=button_h,
            bg=parent.cget("bg"),
            highlightthickness=0,
            borderwidth=0,
            cursor=cursor,
        )
        self._shape_id = None
        self._label_id = None
        self._draw(self._bg)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _draw(self, fill: str) -> None:
        width = int(self.cget("width"))
        height = int(self.cget("height"))
        pad = self._outline_pad
        if self._shape_id is not None:
            self.delete(self._shape_id)
        if self._label_id is not None:
            self.delete(self._label_id)
        points = chamfered_rect_points(
            pad + self._border_width / 2,
            pad + self._border_width / 2,
            width - (2 * pad) - self._border_width,
            height - (2 * pad) - self._border_width,
            self._chamfer,
        )
        self._shape_id = self.create_polygon(
            *points,
            fill=fill,
            outline=self._border,
            width=self._border_width,
            smooth=False,
        )
        self._label_id = self.create_text(
            width // 2,
            height // 2,
            text=self._text,
            fill=self._fg,
            font=self._font,
        )

    def _on_click(self, _event=None):
        if callable(self._command):
            self._command()

    def _on_enter(self, _event=None):
        self._hover = True
        self._draw(self._active_bg)

    def _on_leave(self, _event=None):
        self._hover = False
        self._draw(self._bg)


def draw_bubble_shell(
    canvas: tk.Canvas,
    *,
    panel_width: int,
    body_height: int,
    tail_center_x: int,
    bg: str,
    border: str,
    border_width: int,
    chamfer: int,
    tail_height: int,
    tail_half_width: int,
    offset_x: int = 0,
    offset_y: int = 0,
) -> None:
    """Paint the chamfered bubble body and pointer tail."""
    canvas.delete("bubble")
    inset = chamfer + border_width
    body_h = body_height + (2 * inset)
    body_w = panel_width
    points = chamfered_rect_points(
        offset_x + border_width / 2,
        offset_y + border_width / 2,
        body_w - border_width,
        body_h - border_width,
        chamfer,
    )
    canvas.create_polygon(
        *points,
        fill=bg,
        outline=border,
        width=border_width,
        smooth=False,
        tags="bubble",
    )
    tail_top = offset_y + body_h - border_width
    tail_x = offset_x + tail_center_x
    canvas.create_polygon(
        tail_x - tail_half_width,
        tail_top,
        tail_x + tail_half_width,
        tail_top,
        tail_x,
        tail_top + tail_height,
        fill=bg,
        outline=border,
        width=border_width,
        tags="bubble",
    )
