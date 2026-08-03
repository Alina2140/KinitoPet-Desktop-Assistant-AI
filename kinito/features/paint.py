"""Kinito Paint: retro drawing window, save PNGs, and gallery viewer."""

from __future__ import annotations

import math
import os
import random
import shutil
import threading
import tkinter as tk
from datetime import datetime
from tkinter import Button, Frame, Label, Scrollbar, Toplevel, filedialog, messagebox

from PIL import Image, ImageDraw, ImageTk

from content import dialogue as dlg
from content import llm_prompts as prompts
from content import paint_lines
from kinito.assets import ensure_user_media_directories, list_image_files, paintings_directory
from kinito.features.games.base import center_toplevel
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

_TIP_SPECS = (
    ("circle", "large", 16),
    ("circle", "medium", 10),
    ("circle", "small", 4),
    ("rect", "large", 16),
    ("rect", "medium", 10),
    ("rect", "small", 4),
)

_TOOL_DEFS = (
    ("eraser", "Eraser"),
    ("pencil", "Pencil"),
    ("spray", "Spray"),
    ("line", "Line"),
    ("circle", "Circle"),
    ("rect", "Rect"),
)

_UI_BG = "#e6ded5"
_CANVAS_BG = "#ffffff"
_SELECTED_BG = "#ffff80"
_THUMB_SIZE = (96, 72)
_GALLERY_COLS = 3


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    value = color.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


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
        self._tip_buttons: list[tuple[Button, str, int]] = []
        self._color_preview: tk.Canvas | None = None
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
        for index, (tool_id, label) in enumerate(_TOOL_DEFS):
            row, col = divmod(index, 2)
            btn = Button(
                tools,
                text=label,
                width=7,
                font=("TkDefaultFont", 7),
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
        for index, (shape, _name, size) in enumerate(_TIP_SPECS):
            row, col = divmod(index, 3)
            glyph = "●" if shape == "circle" else "■"
            btn = Button(
                tips,
                text=glyph,
                font=("TkDefaultFont", 6 + size // 4),
                width=3,
                command=lambda s=shape, z=size: self._set_tip(s, z),
            )
            btn.grid(row=row, column=col, padx=1, pady=1)
            self._tip_buttons.append((btn, shape, size))

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
        for tool_id, btn in self._tool_buttons.items():
            if tool_id == tool:
                btn.configure(relief=tk.SUNKEN, bg=_SELECTED_BG)
            else:
                btn.configure(relief=tk.RAISED, bg=_UI_BG)

    def _set_tip(self, shape: str, size: int) -> None:
        self._tip_shape = shape
        self._tip_size = size
        for btn, tip_shape, tip_size in self._tip_buttons:
            if tip_shape == shape and tip_size == size:
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
        if self._tool == "line":
            self._preview_id = self.canvas.create_line(x0, y0, x1, y1, fill=color, width=2)
        elif self._tool == "circle":
            self._preview_id = self.canvas.create_oval(x0, y0, x1, y1, outline=color, width=2)
        elif self._tool == "rect":
            self._preview_id = self.canvas.create_rectangle(
                x0, y0, x1, y1, outline=color, width=2
            )

    def _commit_shape(self, x0: int, y0: int, x1: int, y1: int) -> None:
        assert self.canvas is not None
        self._clear_preview()
        color = self._color
        rgb = _hex_to_rgb(color)
        width = max(1, self._tip_size // 3)
        if self._tool == "line":
            self.canvas.create_line(x0, y0, x1, y1, fill=color, width=width)
            self._draw.line((x0, y0, x1, y1), fill=rgb, width=width)
        elif self._tool == "circle":
            self.canvas.create_oval(x0, y0, x1, y1, outline=color, width=width)
            self._draw.ellipse((x0, y0, x1, y1), outline=rgb, width=width)
        elif self._tool == "rect":
            self.canvas.create_rectangle(x0, y0, x1, y1, outline=color, width=width)
            self._draw.rectangle((x0, y0, x1, y1), outline=rgb, width=width)

    def _on_press(self, event) -> None:
        x, y = self._clamp(event.x, event.y)
        self._drawing = True
        self._last_xy = (x, y)
        self._last_spray_xy = None
        if self._tool in ("line", "circle", "rect"):
            self._shape_start = (x, y)
            return
        if self._tool == "spray":
            self._spray_at(x, y)
        else:
            self._stamp(x, y)
        self._dirty = True

    def _on_drag(self, event) -> None:
        if not self._drawing:
            return
        x, y = self._clamp(event.x, event.y)
        if self._tool in ("line", "circle", "rect") and self._shape_start is not None:
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
        if self._tool in ("line", "circle", "rect") and self._shape_start is not None:
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
        """Show a large preview with download and delete actions."""
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

        Label(window, text=name, bg=_UI_BG, font=("TkDefaultFont", 10, "bold")).pack(
            pady=(10, 4)
        )
        label = Label(window, image=photo, bg="black", bd=2, relief=tk.SUNKEN)
        label.image = photo
        label.pack(padx=12, pady=4)

        buttons = Frame(window, bg=_UI_BG)
        buttons.pack(pady=10)

        def download():
            dest = filedialog.asksaveasfilename(
                parent=window,
                title="Download painting",
                defaultextension=".png",
                initialfile=name,
                filetypes=[("PNG images", "*.png"), ("All files", "*.*")],
            )
            if not dest:
                return
            try:
                shutil.copy2(path, dest)
            except OSError:
                messagebox.showerror("Download failed", "Could not save the file.", parent=window)
                return
            self.speak_paint_line(dlg.pick_line(paint_lines.PAINT_SAVE_LINES))

        def delete():
            if not messagebox.askyesno(
                "Delete painting",
                f"Delete {name}?",
                parent=window,
            ):
                return
            try:
                os.remove(path)
            except OSError:
                messagebox.showerror("Delete failed", "Could not delete the file.", parent=window)
                return
            try:
                window.destroy()
            except tk.TclError:
                pass
            self._paint_detail_window = None
            self._show_paint_gallery()

        Button(buttons, text="Download", command=download, width=12).pack(side=tk.LEFT, padx=6)
        Button(buttons, text="Delete", command=delete, width=12).pack(side=tk.LEFT, padx=6)
        Button(buttons, text="Close", command=window.destroy, width=12).pack(side=tk.LEFT, padx=6)

        def on_close():
            self._paint_detail_window = None
            try:
                window.destroy()
            except tk.TclError:
                pass

        window.protocol("WM_DELETE_WINDOW", on_close)
