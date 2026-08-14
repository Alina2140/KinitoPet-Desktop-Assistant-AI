"""Shared helpers for in-app mini-game windows."""

import sys
import tkinter as tk
from tkinter import Toplevel

from content import dialogue as dlg
from content import game_lines
from kinito.window_icon import apply_window_icon


def game_emoji_font(size: int = 24) -> tuple[str, int]:
    """Return a platform font that renders color emoji reliably."""
    if sys.platform == "win32":
        return ("Segoe UI Emoji", size)
    if sys.platform == "darwin":
        return ("Apple Color Emoji", size)
    return ("Noto Color Emoji", size)


def create_uniform_grid(
    parent,
    rows: int,
    cols: int,
    *,
    uniform: str,
) -> tk.Frame:
    """Create a grid whose rows/columns share equal space when resized."""
    grid = tk.Frame(parent)
    grid.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    for i in range(rows):
        grid.rowconfigure(i, weight=1, uniform=f"{uniform}_row")
    for i in range(cols):
        grid.columnconfigure(i, weight=1, uniform=f"{uniform}_col")
    return grid


def center_toplevel(app, window, width: int, height: int) -> None:
    """Position *window* centered on the primary monitor."""
    from kinito.window_targets import centered_origin_on_rect, primary_monitor_rect

    app.root.update_idletasks()
    x = y = None
    center = getattr(app, "_centered_origin_on_primary", None)
    if callable(center):
        try:
            origin = center(width, height)
        except Exception:
            origin = None
        if (
            isinstance(origin, tuple)
            and len(origin) == 2
            and all(isinstance(value, (int, float)) for value in origin)
        ):
            x, y = int(origin[0]), int(origin[1])
    if x is None or y is None:
        try:
            fallback = (
                0,
                0,
                int(app.root.winfo_screenwidth()),
                int(app.root.winfo_screenheight()),
            )
        except (tk.TclError, AttributeError, TypeError, ValueError):
            fallback = (
                int(app.root.winfo_vrootx()),
                int(app.root.winfo_vrooty()),
                int(app.root.winfo_vrootwidth()),
                int(app.root.winfo_vrootheight()),
            )
        x, y = centered_origin_on_rect(
            width, height, primary_monitor_rect(fallback=fallback)
        )
    window.geometry(f"{width}x{height}+{x}+{y}")


def open_game_window(
    app,
    title: str,
    width: int,
    height: int,
    *,
    min_width: int | None = None,
    min_height: int | None = None,
) -> Toplevel:
    """Create a centered, resizable game window and track it on *app*."""
    app._ensure_single_game_window()
    window = Toplevel(app.root)
    window.title(title)
    apply_window_icon(window)
    window.resizable(True, True)
    window.minsize(
        min_width if min_width is not None else max(280, width - 60),
        min_height if min_height is not None else max(320, height - 60),
    )
    center_toplevel(app, window, width, height)

    def on_close():
        if getattr(app, "_game_window", None) is not window:
            try:
                window.destroy()
            except tk.TclError:
                pass
            return
        app._game_window = None
        line = dlg.pick_line(game_lines.GAME_CLOSED_LINES)
        window.destroy()
        app.root.after(0, lambda: app.speak_game_line(line))

    window.protocol("WM_DELETE_WINDOW", on_close)
    window._kinito_close = on_close
    app._game_window = window
    return window
