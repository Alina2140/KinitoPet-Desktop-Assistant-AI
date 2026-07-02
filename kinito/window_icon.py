"""Apply the Kinito favicon to Tk windows and expose paths for other toolkits."""

from __future__ import annotations

import os
import tkinter as tk

from kinito.assets import favicon_path, icon_path

_cached_photo: tk.PhotoImage | None = None


def window_icon_path() -> str:
    """Return the absolute path to the preferred window icon."""
    return os.path.abspath(favicon_path)


def _load_photo() -> tk.PhotoImage | None:
    """Load and cache the favicon as a Tk PhotoImage."""
    global _cached_photo
    if _cached_photo is not None:
        return _cached_photo
    if not os.path.isfile(favicon_path):
        return None
    try:
        _cached_photo = tk.PhotoImage(file=favicon_path)
    except tk.TclError:
        _cached_photo = None
    return _cached_photo


def _apply_ico_fallback(window: tk.Misc, *, default: bool) -> None:
    """Fall back to Icon.ico when PNG favicon loading fails."""
    if not os.path.isfile(icon_path):
        return
    try:
        if default:
            window.iconbitmap(default=icon_path)
        else:
            window.iconbitmap(icon_path)
    except tk.TclError:
        pass


def apply_window_icon(window: tk.Misc, *, default: bool = False) -> None:
    """Set the Kinito favicon on *window*."""
    photo = _load_photo()
    if photo is not None:
        try:
            window.iconphoto(default, photo)
            return
        except tk.TclError:
            pass
    _apply_ico_fallback(window, default=default)


def set_default_window_icon(root: tk.Misc) -> None:
    """Use the Kinito favicon as the default icon for future Tk windows."""
    apply_window_icon(root, default=True)
