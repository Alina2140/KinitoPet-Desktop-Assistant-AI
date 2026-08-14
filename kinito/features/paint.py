"""Kinito Paint: retro drawing window, save PNGs, and gallery viewer."""

from __future__ import annotations

import io
import math
import os
import random
import shutil
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import Button, Frame, Label, Scrollbar, Toplevel, filedialog, messagebox, simpledialog

from PIL import Image, ImageDraw, ImageTk

from content import dialogue as dlg
from content import llm_prompts as prompts
from content import paint_lines
from kinito.assets import ensure_user_media_directories, list_image_files, paintings_directory
from kinito.features.games.base import center_toplevel
from kinito.llm.ollama_client import OllamaUnavailableError
from kinito.window_icon import apply_window_icon

# Win95-ish palette (two rows).
_PALETTE = (
    "#000000",
    "#808080",
    "#540505",
    "#5e5e0a",
    "#135913",
    "#105e5e",
    "#000054",
    "#420142",
    "#4a4a18",
    "#002b2b",
    "#197dff",
    "#002529",
    "#4100b3",
    "#542d1d",
    "#ffffff",
    "#c0c0c0",
    "#e30000",
    "#ffff54",
    "#14e314",
    "#45ffff",
    "#0000c9",
    "#d40dd4",
    "#ffffa1",
    "#00ff80",
    "#b3ffff",
    "#6565c7",
    "#eb097a",
    "#c46b47",
)

# Freehand stamp tips (circle/square brush). Name is unused; kept for readability.
_TIP_SPECS = (
    ("circle", "large", 16),
    ("circle", "medium", 10),
    ("circle", "small", 4),
    ("rect", "large", 16),
    ("rect", "medium", 10),
    ("rect", "small", 4),
)

# Shape tools live in the tip panel: each has three stroke thicknesses.
_SHAPE_TIP_SPECS = (
    ("line", "large", 16),
    ("line", "medium", 10),
    ("line", "small", 4),
    ("circle", "large", 16),
    ("circle", "medium", 10),
    ("circle", "small", 4),
    ("rect", "large", 16),
    ("rect", "medium", 10),
    ("rect", "small", 4),
)

_SHAPE_TOOLS = frozenset({"line", "circle", "rect"})

_TOOL_DEFS = (
    ("eraser", "Eraser"),
    ("pencil", "Pencil"),
    ("spray", "Spray"),
    ("fill", "Fill"),
)

_TOOL_ICON_SIZE = 22

# Fixed tip-button chrome so glyph size never changes cell size.
_TIP_BTN_FONT = ("TkDefaultFont", 10)
_TIP_BTN_WIDTH = 3
_TIP_BTN_HEIGHT = 1

_TIP_GLYPHS = {
    ("circle", 16): "⬤",
    ("circle", 10): "●",
    ("circle", 4): "•",
    ("rect", 16): "⬛",
    ("rect", 10): "■",
    ("rect", 4): "▪",
}

_SHAPE_GLYPHS = {
    ("line", 16): "/",
    ("line", 10): "/",
    ("line", 4): "/",
    ("circle", 16): "◯",
    ("circle", 10): "○",
    ("circle", 4): "∘",
    ("rect", 16): "⬜",
    ("rect", 10): "□",
    ("rect", 4): "▫",
}

_UI_BG = "#e6ded5"
_CANVAS_BG = "#ffffff"
_SELECTED_BG = "#ffff80"
_THUMB_SIZE = (96, 72)
_GALLERY_COLS = 3


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    value = color.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def _tool_icon_image(tool_id: str, size: int = _TOOL_ICON_SIZE) -> Image.Image:
    """Draw a tiny Win95-style tool glyph (transparent RGBA)."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    ink = (32, 32, 32, 255)
    mid = (90, 90, 90, 255)
    accent = (20, 20, 20, 255)

    if tool_id == "eraser":
        # Angled eraser block with a lighter pad.
        body = [(4, 14), (12, 6), (18, 12), (10, 20)]
        draw.polygon(body, fill=(220, 180, 180, 255), outline=ink)
        pad = [(10, 20), (18, 12), (20, 14), (12, 22)]
        draw.polygon(pad, fill=(245, 245, 245, 255), outline=ink)
    elif tool_id == "pencil":
        # Pencil shaft + tip.
        draw.polygon([(7, 18), (15, 4), (18, 6), (10, 20)], fill=(240, 200, 80, 255), outline=ink)
        draw.polygon([(7, 18), (10, 20), (6, 21)], fill=(180, 140, 60, 255), outline=ink)
        draw.polygon([(15, 4), (18, 6), (17, 3)], fill=accent)
        draw.line([(9, 16), (16, 6)], fill=mid, width=1)
    elif tool_id == "spray":
        # Spray can body + nozzle mist.
        draw.rectangle((7, 10, 15, 20), fill=(70, 140, 200, 255), outline=ink)
        draw.rectangle((9, 7, 13, 10), fill=mid, outline=ink)
        draw.rectangle((10, 5, 12, 7), fill=ink)
        for px, py in ((16, 4), (18, 6), (17, 8), (19, 5), (20, 7), (18, 9)):
            draw.point((px, py), fill=ink)
            draw.point((px + 1, py), fill=ink)
    elif tool_id == "fill":
        # Paint bucket tipped with a spill drop.
        draw.polygon(
            [(5, 8), (16, 8), (14, 18), (7, 18)],
            fill=(200, 90, 50, 255),
            outline=ink,
        )
        draw.arc((3, 5, 11, 13), start=200, end=340, fill=ink, width=1)
        draw.ellipse((14, 14, 19, 19), fill=(200, 90, 50, 255), outline=ink)
        draw.line([(16, 8), (18, 12)], fill=ink, width=1)
    else:
        draw.rectangle((4, 4, size - 5, size - 5), outline=ink)

    return img


def _thumbnail_image(path: str, size: tuple[int, int] = _THUMB_SIZE) -> Image.Image | None:
    """Load *path* and return a letterboxed RGB thumbnail, or None on failure."""
    try:
        img = Image.open(path).convert("RGB")
    except OSError:
        return None
    img.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, "#e0e0e0")
    offset = ((size[0] - img.width) // 2, (size[1] - img.height) // 2)
    canvas.paste(img, offset)
    return canvas


def _thumbnail_photo(path: str, size: tuple[int, int] = _THUMB_SIZE) -> ImageTk.PhotoImage | None:
    thumb = _thumbnail_image(path, size=size)
    if thumb is None:
        return None
    return ImageTk.PhotoImage(thumb)


def sanitize_painting_filename(raw: str) -> str | None:
    """Return a safe ``*.png`` filename, or None if empty/invalid."""
    if not isinstance(raw, str):
        return None
    trimmed = raw.strip()
    if not trimmed:
        return None
    base = os.path.basename(trimmed)
    stem, ext = os.path.splitext(base)
    if not stem:
        return None
    cleaned = "".join(
        ch if (ch.isalnum() or ch in {" ", "-", "_", "."}) else "_" for ch in stem
    )
    cleaned = " ".join(cleaned.split()).strip(" ._")
    if not cleaned:
        return None
    if len(cleaned) > 80:
        cleaned = cleaned[:80].rstrip(" ._")
    if not cleaned:
        return None
    return f"{cleaned}.png"


class PaintWindow:
    """Retro paint UI with tools, tips, palette, and PNG export."""

    CANVAS_W = 560
    CANVAS_H = 400
    WINDOW_W = 700
    WINDOW_H = 500
    SIDEBAR_W = 110
    COMMENT_FIRST_MS = (45000, 70000)
    COMMENT_REPEAT_MS = (60000, 120000)

    def __init__(self, app):
        self.app = app
        self.window: Toplevel | None = None
        self.canvas: tk.Canvas | None = None
        self._image = Image.new("RGB", (self.CANVAS_W, self.CANVAS_H), _CANVAS_BG)
        self._draw = ImageDraw.Draw(self._image)
        self._tool = "pencil"
        self._color = "#000000"
        self._tip_shape = "circle"
        self._tip_size = 10
        self._drawing = False
        self._last_xy: tuple[int, int] | None = None
        self._shape_start: tuple[int, int] | None = None
        self._preview_id: int | None = None
        self._tool_buttons: dict[str, Button] = {}
        self._tool_icons: dict[str, ImageTk.PhotoImage] = {}
        self._tip_buttons: list[tuple[Button, str, int]] = []
        self._shape_tip_buttons: list[tuple[Button, str, int]] = []
        self._color_preview: tk.Canvas | None = None
        self._canvas_photo: ImageTk.PhotoImage | None = None
        self._dirty = False
        self._saved_name: str | None = None
        self._line_timer = None
        self._last_spray_xy: tuple[int, int] | None = None

    def open(self) -> None:
        """Create or focus the paint window."""
        self.app._ensure_single_paint_window()
        window = Toplevel(self.app.root)
        self.window = window
        self.app._paint_window = window
        self.app._paint_session = self
        window.title("untitled - Paint")
        apply_window_icon(window)
        window.resizable(False, False)
        window.configure(bg=_UI_BG)
        center_toplevel(self.app, window, self.WINDOW_W, self.WINDOW_H)

        outer = Frame(window, bg=_UI_BG, bd=2, relief=tk.RAISED)
        outer.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        body = Frame(outer, bg=_UI_BG)
        body.pack(fill=tk.BOTH, expand=True, padx=4, pady=(4, 2))

        sidebar = Frame(body, bg=_UI_BG, width=self.SIDEBAR_W)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 6))
        sidebar.pack_propagate(False)

        tools = Frame(sidebar, bg=_UI_BG, bd=2, relief=tk.SUNKEN)
        tools.pack(fill=tk.X, pady=(0, 6))
        for col in range(2):
            tools.grid_columnconfigure(col, weight=1, uniform="tool")
        for row in range(2):
            tools.grid_rowconfigure(row, weight=1, uniform="tool")
        for index, (tool_id, _label) in enumerate(_TOOL_DEFS):
            row, col = divmod(index, 2)
            icon = ImageTk.PhotoImage(_tool_icon_image(tool_id))
            self._tool_icons[tool_id] = icon
            btn = Button(
                tools,
                image=icon,
                width=_TOOL_ICON_SIZE + 10,
                height=_TOOL_ICON_SIZE + 6,
                command=lambda t=tool_id: self._set_tool(t),
            )
            btn.grid(row=row, column=col, padx=1, pady=1, sticky="nsew")
            self._tool_buttons[tool_id] = btn

        self._color_preview = tk.Canvas(
            sidebar,
            width=self.SIDEBAR_W - 12,
            height=40,
            bg=self._color,
            highlightthickness=1,
            relief=tk.SUNKEN,
        )
        self._color_preview.pack(fill=tk.X, pady=(0, 6))

        tips = Frame(sidebar, bg=_UI_BG, bd=2, relief=tk.SUNKEN)
        tips.pack(fill=tk.X, pady=(0, 6))
        for col in range(3):
            tips.grid_columnconfigure(col, weight=1, uniform="tip")
        tip_row_count = (len(_TIP_SPECS) + 2) // 3 + (len(_SHAPE_TIP_SPECS) + 2) // 3
        for row in range(tip_row_count):
            tips.grid_rowconfigure(row, weight=1, uniform="tip")

        for index, (shape, _name, size) in enumerate(_TIP_SPECS):
            row, col = divmod(index, 3)
            btn = Button(
                tips,
                text=_TIP_GLYPHS[(shape, size)],
                font=_TIP_BTN_FONT,
                width=_TIP_BTN_WIDTH,
                height=_TIP_BTN_HEIGHT,
                command=lambda s=shape, z=size: self._set_tip(s, z),
            )
            btn.grid(row=row, column=col, padx=1, pady=1, sticky="nsew")
            self._tip_buttons.append((btn, shape, size))

        tip_rows = (len(_TIP_SPECS) + 2) // 3
        for index, (tool_id, _name, size) in enumerate(_SHAPE_TIP_SPECS):
            row, col = divmod(index, 3)
            btn = Button(
                tips,
                text=_SHAPE_GLYPHS[(tool_id, size)],
                font=_TIP_BTN_FONT,
                width=_TIP_BTN_WIDTH,
                height=_TIP_BTN_HEIGHT,
                command=lambda t=tool_id, z=size: self._set_shape_tool(t, z),
            )
            btn.grid(row=tip_rows + row, column=col, padx=1, pady=1, sticky="nsew")
            self._shape_tip_buttons.append((btn, tool_id, size))

        Button(sidebar, text="Save", command=self.save).pack(fill=tk.X, pady=(4, 0))
        Button(sidebar, text="Clear", command=self.clear_canvas).pack(fill=tk.X, pady=(4, 0))

        # Canvas + palette share a column so the palette aligns with the canvas.
        right = Frame(body, bg=_UI_BG)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        canvas_frame = Frame(right, bg=_UI_BG, bd=2, relief=tk.SUNKEN)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(
            canvas_frame,
            width=self.CANVAS_W,
            height=self.CANVAS_H,
            bg=_CANVAS_BG,
            highlightthickness=0,
            cursor="crosshair",
        )
        self.canvas.pack(padx=2, pady=2)
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

        palette = Frame(right, bg=_UI_BG, bd=2, relief=tk.SUNKEN)
        palette.pack(fill=tk.X, pady=(6, 6))
        for index, color in enumerate(_PALETTE):
            row, col = divmod(index, 14)
            swatch = Button(
                palette,
                bg=color,
                activebackground=color,
                width=2,
                height=1,
                relief=tk.RAISED,
                bd=1,
                command=lambda c=color: self._set_color(c),
            )
            swatch.grid(row=row, column=col, padx=1, pady=2)

        self._set_tool("pencil")
        self._set_tip("circle", 10)
        self._set_color("#000000")

        def on_close():
            self._cancel_line_timer()
            if getattr(self.app, "_paint_window", None) is not window:
                try:
                    window.destroy()
                except tk.TclError:
                    pass
                return
            self.app._paint_window = None
            if getattr(self.app, "_paint_session", None) is self:
                self.app._paint_session = None
            line = dlg.pick_line(paint_lines.PAINT_CLOSE_LINES)
            window.destroy()
            self.app.root.after(0, lambda: self.app.speak_paint_line(line))

        window.protocol("WM_DELETE_WINDOW", on_close)
        window._kinito_close = on_close

        self.app.root.after(
            0,
            lambda: self.app.speak_paint_line(dlg.pick_line(paint_lines.PAINT_OPEN_LINES)),
        )
        self._schedule_line_timer(first=True)

    def _cancel_line_timer(self) -> None:
        if self._line_timer is not None:
            try:
                self.app.root.after_cancel(self._line_timer)
            except (tk.TclError, ValueError):
                pass
            self._line_timer = None

    def _schedule_line_timer(self, *, first: bool = False) -> None:
        self._cancel_line_timer()
        if self.window is None:
            return
        low, high = self.COMMENT_FIRST_MS if first else self.COMMENT_REPEAT_MS
        delay_ms = random.randint(low, high)
        self._line_timer = self.app.root.after(delay_ms, self._on_line_timer)

    def _on_line_timer(self) -> None:
        self._line_timer = None
        if self.window is None:
            return
        try:
            if not self.window.winfo_exists():
                return
        except tk.TclError:
            return
        busy = getattr(self.app, "_is_busy_with_speech", lambda: False)()
        if not busy:
            line = dlg.pick_line(paint_lines.PAINT_WHILE_LINES)
            threading.Thread(
                target=lambda: self.app.speak_paint_line(line),
                daemon=True,
            ).start()
        self._schedule_line_timer(first=False)

    def _set_tool(self, tool: str) -> None:
        self._tool = tool
        self._refresh_tool_highlights()

    def _set_tip(self, shape: str, size: int) -> None:
        self._tip_shape = shape
        self._tip_size = size
        # Stamp tips belong to freehand tools; leave shapes/fill for their own buttons.
        if self._tool in _SHAPE_TOOLS or self._tool == "fill":
            self._tool = "pencil"
        self._refresh_tool_highlights()

    def _set_shape_tool(self, tool: str, size: int) -> None:
        """Select a shape tool (line/circle/rect) with a stroke thickness."""
        self._tool = tool
        self._tip_size = size
        self._refresh_tool_highlights()

    def _refresh_tool_highlights(self) -> None:
        for tool_id, btn in self._tool_buttons.items():
            if tool_id == self._tool:
                btn.configure(relief=tk.SUNKEN, bg=_SELECTED_BG)
            else:
                btn.configure(relief=tk.RAISED, bg=_UI_BG)

        freehand = self._tool not in _SHAPE_TOOLS
        for btn, tip_shape, tip_size in self._tip_buttons:
            if freehand and tip_shape == self._tip_shape and tip_size == self._tip_size:
                btn.configure(relief=tk.SUNKEN, bg=_SELECTED_BG)
            else:
                btn.configure(relief=tk.RAISED, bg=_UI_BG)

        for btn, shape_tool, tip_size in self._shape_tip_buttons:
            if (
                not freehand
                and shape_tool == self._tool
                and tip_size == self._tip_size
            ):
                btn.configure(relief=tk.SUNKEN, bg=_SELECTED_BG)
            else:
                btn.configure(relief=tk.RAISED, bg=_UI_BG)

    def _set_color(self, color: str) -> None:
        self._color = color
        if self._color_preview is not None:
            self._color_preview.configure(bg=color)

    def _active_color(self) -> str:
        return _CANVAS_BG if self._tool == "eraser" else self._color

    def _active_rgb(self) -> tuple[int, int, int]:
        return _hex_to_rgb(self._active_color())

    def _clamp(self, x: int, y: int) -> tuple[int, int]:
        return (
            max(0, min(self.CANVAS_W - 1, int(x))),
            max(0, min(self.CANVAS_H - 1, int(y))),
        )

    def _sync_canvas_from_image(self) -> None:
        """Replace canvas items with the current backing image (e.g. after fill)."""
        assert self.canvas is not None
        self.canvas.delete("all")
        self._preview_id = None
        self._canvas_photo = ImageTk.PhotoImage(self._image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self._canvas_photo)

    def _flood_fill_at(self, x: int, y: int) -> None:
        """Paint-bucket fill from (x, y) with the active color."""
        fill_rgb = self._active_rgb()
        target = self._image.getpixel((x, y))
        if target == fill_rgb:
            return
        ImageDraw.floodfill(self._image, (x, y), fill_rgb, thresh=0)
        self._sync_canvas_from_image()

    def _stamp(self, x: int, y: int) -> None:
        assert self.canvas is not None
        color = self._active_color()
        rgb = self._active_rgb()
        half = max(1, self._tip_size // 2)
        if self._tip_shape == "circle":
            self.canvas.create_oval(
                x - half, y - half, x + half, y + half, fill=color, outline=color
            )
            self._draw.ellipse((x - half, y - half, x + half, y + half), fill=rgb)
        else:
            self.canvas.create_rectangle(
                x - half, y - half, x + half, y + half, fill=color, outline=color
            )
            self._draw.rectangle((x - half, y - half, x + half, y + half), fill=rgb)

    def _stroke_to(self, x: int, y: int) -> None:
        if self._last_xy is None:
            self._stamp(x, y)
            self._last_xy = (x, y)
            return
        x0, y0 = self._last_xy
        steps = max(abs(x - x0), abs(y - y0), 1)
        for i in range(steps + 1):
            t = i / steps
            self._stamp(int(x0 + (x - x0) * t), int(y0 + (y - y0) * t))
        self._last_xy = (x, y)

    def _spray_at(self, x: int, y: int) -> None:
        """Scatter a few tip-sized stamps; throttle so slow motion stays airy."""
        # Skip when the cursor barely moved — B1-Motion fires very often.
        min_step = max(3, self._tip_size)
        if self._last_spray_xy is not None:
            lx, ly = self._last_spray_xy
            if (x - lx) ** 2 + (y - ly) ** 2 < min_step * min_step:
                return
        self._last_spray_xy = (x, y)

        # Cloud wider than the tip so stamps don't pile into a solid blob.
        radius = max(6, self._tip_size * 3)
        # Few particles per event; tip size/shape come from _stamp.
        count = 1 if self._tip_size <= 4 else (2 if self._tip_size <= 10 else 3)
        for _ in range(count):
            angle = random.random() * math.tau
            dist = random.random() * radius
            px, py = self._clamp(
                x + int(math.cos(angle) * dist),
                y + int(math.sin(angle) * dist),
            )
            self._stamp(px, py)

    def _clear_preview(self) -> None:
        if self.canvas is not None and self._preview_id is not None:
            self.canvas.delete(self._preview_id)
        self._preview_id = None

    def _preview_shape(self, x0: int, y0: int, x1: int, y1: int) -> None:
        assert self.canvas is not None
        self._clear_preview()
        color = self._color
        width = max(1, self._tip_size // 3)
        if self._tool == "line":
            self._preview_id = self.canvas.create_line(
                x0, y0, x1, y1, fill=color, width=width
            )
        elif self._tool == "circle":
            self._preview_id = self.canvas.create_oval(
                x0, y0, x1, y1, outline=color, width=width
            )
        elif self._tool == "rect":
            self._preview_id = self.canvas.create_rectangle(
                x0, y0, x1, y1, outline=color, width=width
            )

    def _commit_shape(self, x0: int, y0: int, x1: int, y1: int) -> None:
        assert self.canvas is not None
        self._clear_preview()
        color = self._color
        rgb = _hex_to_rgb(color)
        width = max(1, self._tip_size // 3)
        # PIL ellipse/rectangle require ordered corners; drag may go any direction.
        left, right = sorted((x0, x1))
        top, bottom = sorted((y0, y1))
        if self._tool == "line":
            self.canvas.create_line(x0, y0, x1, y1, fill=color, width=width)
            self._draw.line((x0, y0, x1, y1), fill=rgb, width=width)
        elif self._tool == "circle":
            self.canvas.create_oval(left, top, right, bottom, outline=color, width=width)
            self._draw.ellipse((left, top, right, bottom), outline=rgb, width=width)
        elif self._tool == "rect":
            self.canvas.create_rectangle(
                left, top, right, bottom, outline=color, width=width
            )
            self._draw.rectangle((left, top, right, bottom), outline=rgb, width=width)

    def _on_press(self, event) -> None:
        x, y = self._clamp(event.x, event.y)
        self._drawing = True
        self._last_xy = (x, y)
        self._last_spray_xy = None
        if self._tool in _SHAPE_TOOLS:
            self._shape_start = (x, y)
            return
        if self._tool == "fill":
            self._flood_fill_at(x, y)
            self._dirty = True
            return
        if self._tool == "spray":
            self._spray_at(x, y)
        else:
            self._stamp(x, y)
        self._dirty = True

    def _on_drag(self, event) -> None:
        if not self._drawing:
            return
        if self._tool == "fill":
            return
        x, y = self._clamp(event.x, event.y)
        if self._tool in _SHAPE_TOOLS and self._shape_start is not None:
            self._preview_shape(self._shape_start[0], self._shape_start[1], x, y)
            return
        if self._tool == "spray":
            self._spray_at(x, y)
        else:
            self._stroke_to(x, y)
        self._dirty = True

    def _on_release(self, event) -> None:
        if not self._drawing:
            return
        x, y = self._clamp(event.x, event.y)
        self._drawing = False
        if self._tool == "fill":
            self._last_xy = None
            return
        if self._tool in _SHAPE_TOOLS and self._shape_start is not None:
            self._commit_shape(self._shape_start[0], self._shape_start[1], x, y)
            self._shape_start = None
            self._dirty = True
            return
        self._last_xy = None
        self._last_spray_xy = None

    def clear_canvas(self) -> None:
        """Reset canvas and backing image to white."""
        if self.canvas is not None:
            self.canvas.delete("all")
        self._image = Image.new("RGB", (self.CANVAS_W, self.CANVAS_H), _CANVAS_BG)
        self._draw = ImageDraw.Draw(self._image)
        self._dirty = False
        self._saved_name = None
        if self.window is not None:
            try:
                self.window.title("untitled - Paint")
            except tk.TclError:
                pass

    def save(self) -> str | None:
        """Write the current painting to UserMedia/paintings and speak a save line."""
        ensure_user_media_directories()
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"paint_{stamp}.png"
        path = os.path.join(paintings_directory, name)
        try:
            self._image.save(path, format="PNG")
        except OSError:
            return None
        self._saved_name = name
        self._dirty = False
        if self.window is not None:
            try:
                self.window.title(f"{name} - Paint")
            except tk.TclError:
                pass
        line = dlg.pick_line(paint_lines.PAINT_SAVE_LINES)
        self.app.root.after(0, lambda: self.app.speak_paint_line(line))
        return path


class PaintMixin:
    """Actions menu entry points for Paint and the painting gallery."""

    PAINT_COMMENT_RETRY_MS = 400
    PAINT_RECALL_CHANCE = 1 / 350
    PAINT_RECALL_COOLDOWN_SECONDS = 900
    PAINT_RECALL_MAX_EDGE = 896
    PAINT_RECALL_JPEG_QUALITY = 70

    def offer_paint_picker(self):
        """Speak the Paint submenu (Draw / My Paintings)."""
        self.speak(dlg.PAINT_PICKER_QUESTION, 45, True)

    def speak_paint_line(self, line: str) -> None:
        """Speak a paint commentary line (allowed while Paint is open)."""
        self.speak(line, ai_hint=prompts.PAINT_PROMPT)

    def _is_paint_active(self) -> bool:
        window = getattr(self, "_paint_window", None)
        if window is None:
            return False
        try:
            if window.winfo_exists():
                return True
            self._paint_window = None
            self._paint_session = None
        except tk.TclError:
            self._paint_window = None
            self._paint_session = None
        return False

    def _is_paint_only_active(self) -> bool:
        """True when Paint is open and no mini-game window/session is active."""
        if not self._is_paint_active():
            return False
        return not super()._is_game_active()

    def _is_game_active(self) -> bool:
        if self._is_paint_active():
            return True
        return super()._is_game_active()

    def _ensure_single_paint_window(self) -> None:
        session = getattr(self, "_paint_session", None)
        if session is not None and hasattr(session, "_cancel_line_timer"):
            session._cancel_line_timer()
        window = getattr(self, "_paint_window", None)
        if window is None:
            self._paint_session = None
            return
        try:
            if window.winfo_exists():
                close = getattr(window, "_kinito_close", None)
                if callable(close):
                    close()
                else:
                    window.destroy()
            self._paint_window = None
            self._paint_session = None
        except tk.TclError:
            self._paint_window = None
            self._paint_session = None

    def open_paint(self) -> None:
        """Open the Paint drawing window on the UI thread."""
        self.root.after(0, lambda: PaintWindow(self).open())

    def open_paint_gallery(self) -> None:
        """List saved paintings or speak an empty-gallery line."""
        ensure_user_media_directories()
        paths = [p for p in list_image_files(paintings_directory) if p.lower().endswith(".png")]
        if not paths:
            self.speak_paint_line(dlg.pick_line(paint_lines.PAINT_GALLERY_EMPTY_LINES))
            return
        self.speak_paint_line(dlg.pick_line(paint_lines.PAINT_GALLERY_OPEN_LINES))
        self.root.after(0, lambda: self._show_paint_gallery(paths))

    def _list_painting_paths(self) -> list[str]:
        ensure_user_media_directories()
        return [p for p in list_image_files(paintings_directory) if p.lower().endswith(".png")]

    def _show_paint_gallery(self, paths: list[str] | None = None) -> None:
        existing = getattr(self, "_paint_gallery_window", None)
        if existing is not None:
            try:
                if existing.winfo_exists():
                    existing.destroy()
            except tk.TclError:
                pass
            self._paint_gallery_window = None

        if paths is None:
            paths = self._list_painting_paths()
        if not paths:
            self.speak_paint_line(dlg.pick_line(paint_lines.PAINT_GALLERY_EMPTY_LINES))
            return

        width, height = 420, 380
        window = Toplevel(self.root)
        self._paint_gallery_window = window
        window.title("My Paintings")
        apply_window_icon(window)
        window.configure(bg=_UI_BG)
        window.wm_attributes("-topmost", True)
        center_toplevel(self, window, width, height)

        Label(window, text="Select a painting:", bg=_UI_BG, anchor="w").pack(
            fill=tk.X, padx=10, pady=(10, 4)
        )

        body = Frame(window, bg=_UI_BG)
        body.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        canvas = tk.Canvas(body, bg=_UI_BG, highlightthickness=0)
        scrollbar = Scrollbar(body, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        grid = Frame(canvas, bg=_UI_BG)
        inner_id = canvas.create_window((0, 0), window=grid, anchor="nw")
        photos: list[ImageTk.PhotoImage] = []

        def _on_grid_configure(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_configure(event):
            canvas.itemconfigure(inner_id, width=event.width)

        grid.bind("<Configure>", _on_grid_configure)
        canvas.bind("<Configure>", _on_canvas_configure)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-event.delta / 120), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        for index, path in enumerate(paths):
            row, col = divmod(index, _GALLERY_COLS)
            cell = Frame(grid, bg=_UI_BG, bd=1, relief=tk.RAISED, padx=4, pady=4)
            cell.grid(row=row, column=col, padx=6, pady=6, sticky="n")
            photo = _thumbnail_photo(path)
            name = os.path.basename(path)
            if photo is not None:
                photos.append(photo)
                btn = Button(
                    cell,
                    image=photo,
                    bg=_UI_BG,
                    activebackground=_SELECTED_BG,
                    relief=tk.FLAT,
                    command=lambda p=path: self._open_painting_detail(p),
                )
                btn.image = photo
                btn.pack()
            else:
                Button(
                    cell,
                    text="?",
                    width=10,
                    height=4,
                    command=lambda p=path: self._open_painting_detail(p),
                ).pack()
            Label(
                cell,
                text=name,
                bg=_UI_BG,
                wraplength=_THUMB_SIZE[0] + 8,
                font=("TkDefaultFont", 7),
                justify="center",
            ).pack(pady=(4, 0))

        window._thumb_photos = photos

        Button(window, text="Close", command=window.destroy).pack(pady=(0, 10))

        def on_close():
            try:
                canvas.unbind_all("<MouseWheel>")
            except tk.TclError:
                pass
            self._paint_gallery_window = None
            try:
                window.destroy()
            except tk.TclError:
                pass

        window.protocol("WM_DELETE_WINDOW", on_close)

    def _open_painting_detail(self, path: str) -> None:
        """Show a large preview with download, rename, and delete actions."""
        if not os.path.isfile(path):
            self._show_paint_gallery()
            return

        existing = getattr(self, "_paint_detail_window", None)
        if existing is not None:
            try:
                if existing.winfo_exists():
                    existing.destroy()
            except tk.TclError:
                pass

        try:
            img = Image.open(path).convert("RGB")
        except OSError:
            return

        name = os.path.basename(path)
        max_w, max_h = 520, 390
        preview = img.copy()
        preview.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(preview)

        window = Toplevel(self.root)
        self._paint_detail_window = window
        window.title(name)
        apply_window_icon(window)
        window.configure(bg=_UI_BG)
        window.wm_attributes("-topmost", True)
        center_toplevel(self, window, max_w + 40, max_h + 120)

        title_label = Label(
            window, text=name, bg=_UI_BG, font=("TkDefaultFont", 10, "bold")
        )
        title_label.pack(pady=(10, 4))
        label = Label(window, image=photo, bg="black", bd=2, relief=tk.SUNKEN)
        label.image = photo
        label.pack(padx=12, pady=4)

        buttons = Frame(window, bg=_UI_BG)
        buttons.pack(pady=10)

        state = {"path": path, "name": name}

        def download():
            dest = filedialog.asksaveasfilename(
                parent=window,
                title="Download painting",
                defaultextension=".png",
                initialfile=state["name"],
                filetypes=[("PNG images", "*.png"), ("All files", "*.*")],
            )
            if not dest:
                return
            try:
                shutil.copy2(state["path"], dest)
            except OSError:
                messagebox.showerror(
                    "Download failed", "Could not save the file.", parent=window
                )
                return
            self.speak_paint_line(dlg.pick_line(paint_lines.PAINT_SAVE_LINES))

        def rename():
            current = state["name"]
            stem = os.path.splitext(current)[0]
            answer = simpledialog.askstring(
                "Rename painting",
                "New name:",
                initialvalue=stem,
                parent=window,
            )
            if answer is None:
                return
            new_name = sanitize_painting_filename(answer)
            if new_name is None:
                messagebox.showerror(
                    "Rename failed",
                    "Please enter a valid name.",
                    parent=window,
                )
                return
            if new_name.casefold() == current.casefold():
                return
            directory = os.path.dirname(state["path"])
            new_path = os.path.join(directory, new_name)
            if os.path.exists(new_path):
                messagebox.showerror(
                    "Rename failed",
                    f'A painting named "{new_name}" already exists.',
                    parent=window,
                )
                return
            try:
                os.rename(state["path"], new_path)
            except OSError:
                messagebox.showerror(
                    "Rename failed", "Could not rename the file.", parent=window
                )
                return
            state["path"] = new_path
            state["name"] = new_name
            title_label.configure(text=new_name)
            window.title(new_name)
            self.speak_paint_line(dlg.pick_line(paint_lines.PAINT_RENAME_LINES))

        def delete():
            if not messagebox.askyesno(
                "Delete painting",
                f"Delete {state['name']}?",
                parent=window,
            ):
                return
            try:
                os.remove(state["path"])
            except OSError:
                messagebox.showerror(
                    "Delete failed", "Could not delete the file.", parent=window
                )
                return
            try:
                window.destroy()
            except tk.TclError:
                pass
            self._paint_detail_window = None
            self._show_paint_gallery()

        def close_detail():
            self._paint_detail_window = None
            try:
                window.destroy()
            except tk.TclError:
                pass
            # Rebuild gallery so renames show up in the thumbnails list.
            self._show_paint_gallery()

        Button(buttons, text="Download", command=download, width=10).pack(
            side=tk.LEFT, padx=4
        )
        Button(buttons, text="Rename", command=rename, width=10).pack(
            side=tk.LEFT, padx=4
        )
        Button(buttons, text="Delete", command=delete, width=10).pack(
            side=tk.LEFT, padx=4
        )
        Button(buttons, text="Close", command=close_detail, width=10).pack(
            side=tk.LEFT, padx=4
        )

        window.protocol("WM_DELETE_WINDOW", close_detail)

    def maybe_trigger_paint_recall(self) -> bool:
        """Roll for a random saved-painting popup with commentary."""
        if not getattr(self, "_paint_recall_enabled", True):
            return False
        if getattr(self, "_focus_mode", False):
            return False
        if getattr(self, "_is_game_active", lambda: False)():
            return False
        if (
            self.paused
            or getattr(self, "_is_position_locked_by_user", lambda: self.is_dragging)()
            or getattr(self, "_camera_active", False)
            or getattr(self, "_browser_active", False)
        ):
            return False
        if getattr(self, "_is_busy_with_speech", lambda: False)():
            return False
        if self._is_paint_gallery_open():
            return False
        paths = self._list_painting_paths()
        if not paths:
            return False
        last_at = getattr(self, "_last_paint_recall_at", 0.0)
        if time.monotonic() - last_at < self.PAINT_RECALL_COOLDOWN_SECONDS:
            return False
        if random.random() >= self.PAINT_RECALL_CHANCE:
            return False
        self._last_paint_recall_at = time.monotonic()
        self.root.after(0, self._start_paint_recall)
        return True

    def toggle_paint_recall(self):
        """Enable or disable spontaneous painting popups."""
        self._paint_recall_enabled = not getattr(self, "_paint_recall_enabled", True)
        if hasattr(self, "_persist_settings"):
            self._persist_settings()
        lines = (
            dlg.PAINT_RECALL_ON_LINES
            if self._paint_recall_enabled
            else dlg.PAINT_RECALL_OFF_LINES
        )
        self.speak(dlg.pick_line(lines), skip_ai=True)

    def _is_paint_gallery_open(self) -> bool:
        for attr in ("_paint_gallery_window", "_paint_detail_window", "_paint_recall_popup"):
            window = getattr(self, attr, None)
            if not isinstance(window, Toplevel):
                continue
            try:
                if window.winfo_exists():
                    return True
            except tk.TclError:
                setattr(self, attr, None)
        return False

    def _start_paint_recall(self):
        """Pick a painting and prepare comment off the UI thread."""
        if not getattr(self, "_running", True):
            return
        if not getattr(self, "_paint_recall_enabled", True):
            return
        paths = self._list_painting_paths()
        if not paths:
            return
        path = random.choice(paths)
        threading.Thread(
            target=self._paint_recall_worker,
            args=(path,),
            daemon=True,
        ).start()

    def _paint_recall_worker(self, path: str):
        """Build a comment (vision if available), then show popup + speak."""
        line = dlg.pick_line(paint_lines.PAINT_RECALL_LINES)
        try:
            image_bytes = self._painting_jpeg_bytes(path)
            if image_bytes:
                vision_line = self._vision_paint_recall(image_bytes)
                if vision_line:
                    line = vision_line
        except Exception:
            pass

        if not getattr(self, "_running", True):
            return
        if not getattr(self, "_paint_recall_enabled", True):
            return
        self.root.after(
            0,
            lambda spoken=line, painting=path: self._present_paint_recall(painting, spoken),
        )

    def _present_paint_recall(self, path: str, line: str):
        """Speak the comment and open a non-modal painting popup."""
        if getattr(self, "_is_busy_with_speech", lambda: False)():
            return
        if not os.path.isfile(path):
            return
        existing = getattr(self, "_paint_recall_popup", None)
        if existing is not None:
            try:
                if existing.winfo_exists():
                    existing.destroy()
            except tk.TclError:
                pass
            self._paint_recall_popup = None

        self.speak(line, skip_ai=True)
        title = os.path.basename(path)

        def _on_close():
            self._paint_recall_popup = None

        self._open_paint_recall_popup(path, title=title, on_close=_on_close)

    def _open_paint_recall_popup(self, path: str, *, title: str, on_close) -> None:
        """Show the painting in a topmost non-modal popup."""
        try:
            img = Image.open(path)
        except OSError:
            on_close()
            return

        self.root.update_idletasks()
        query = getattr(self, "_query_primary_screen_rect", None)
        if callable(query):
            screen_x, screen_y, screen_w, screen_h = query()
        else:
            screen_x = self.root.winfo_vrootx()
            screen_y = self.root.winfo_vrooty()
            screen_w = self.root.winfo_vrootwidth()
            screen_h = self.root.winfo_vrootheight()

        img_w, img_h = img.size
        max_w = max(int(screen_w * 0.55), 1)
        max_h = max(int(screen_h * 0.55), 1)
        scale = min(1.0, max_w / max(img_w, 1), max_h / max(img_h, 1))
        width = max(1, int(img_w * scale))
        height = max(1, int(img_h * scale))
        if scale < 1.0:
            img = img.resize((width, height), Image.Resampling.LANCZOS)

        popup = Toplevel(self.root)
        self._paint_recall_popup = popup
        popup.title(title)
        apply_window_icon(popup)
        popup.wm_attributes("-topmost", True)
        popup.configure(bg="black")

        tk_img = ImageTk.PhotoImage(img)
        label = Label(popup, image=tk_img, bd=0, highlightthickness=0, bg="black")
        label.image = tk_img
        label.pack(fill="both", expand=True)

        center = getattr(self, "_centered_origin_on_primary", None)
        if callable(center):
            x, y = center(width, height)
        else:
            x = screen_x + (screen_w - width) // 2
            y = screen_y + (screen_h - height) // 2
        popup.geometry(f"{width}x{height}+{int(x)}+{int(y)}")

        def _handle_close():
            on_close()
            try:
                popup.destroy()
            except tk.TclError:
                pass

        popup.protocol("WM_DELETE_WINDOW", _handle_close)

    def _painting_jpeg_bytes(self, path: str) -> bytes | None:
        """Load a saved painting into JPEG bytes for local vision (RAM only)."""
        buffer = None
        image = None
        try:
            image = Image.open(path).convert("RGB")
            max_edge = self.PAINT_RECALL_MAX_EDGE
            width, height = image.size
            scale = min(1.0, max_edge / max(width, height))
            if scale < 1.0:
                image = image.resize(
                    (max(1, int(width * scale)), max(1, int(height * scale))),
                )
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=self.PAINT_RECALL_JPEG_QUALITY)
            return buffer.getvalue()
        except Exception:
            return None
        finally:
            if buffer is not None:
                buffer.close()
            image = None

    def _vision_paint_recall(self, image_bytes: bytes) -> str | None:
        """Ask local Ollama vision for a short painting comment."""
        client = getattr(self, "_ollama_client", None)
        if client is None or not client.is_available():
            return None
        try:
            reply = client.chat_with_image(
                prompts.PAINT_RECALL_VISION_PROMPT,
                image_bytes,
                system=prompts.PAINT_RECALL_VISION_SYSTEM,
                max_tokens=80,
            )
        except OllamaUnavailableError:
            return None
        cleaned = (reply or "").strip()
        if not cleaned:
            return None
        if len(cleaned) > 280:
            cleaned = cleaned[:277].rstrip() + "…"
        return cleaned
