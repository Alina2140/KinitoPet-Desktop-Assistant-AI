"""Helpers for child Toplevels under an overrideredirect assistant root.

On Windows, creating a Toplevel under a borderless/transparent root can briefly
teleport the parent and flash a default frame. Stage children off-screen and
invisible first, then reveal once geometry is final.
"""

from __future__ import annotations

import sys
import tkinter as tk
from collections.abc import Callable

CHILD_TOPLEVEL_OFFSCREEN = "-10000-10000"


def pin_assistant_screen_position(app) -> tuple[int, int]:
    """Remember the assistant's logical screen position around Toplevel setup."""
    root = getattr(app, "root", None)
    try:
        pinned_x = int(getattr(app, "x", root.winfo_x() if root is not None else 0))
        pinned_y = int(getattr(app, "y", root.winfo_y() if root is not None else 0))
    except (tk.TclError, TypeError, ValueError, AttributeError):
        pinned_x, pinned_y = 0, 0
    try:
        app.x = pinned_x
        app.y = pinned_y
    except Exception:
        pass
    return pinned_x, pinned_y


def restore_assistant_screen_position(app, pinned_x: int, pinned_y: int) -> None:
    """Re-apply *pinned_x*/*pinned_y* to the overrideredirect root window."""
    try:
        app.x = int(pinned_x)
        app.y = int(pinned_y)
    except Exception:
        pass
    root = getattr(app, "root", None)
    if root is None:
        return
    try:
        if not root.winfo_exists():
            return
        root.geometry(f"+{int(pinned_x)}+{int(pinned_y)}")
    except (tk.TclError, TypeError, ValueError):
        pass


def schedule_assistant_position_restore(app, pinned_x: int, pinned_y: int) -> None:
    """Restore immediately and again shortly after Windows finishes mapping."""
    restore_assistant_screen_position(app, pinned_x, pinned_y)
    root = getattr(app, "root", None)
    if root is None:
        return
    try:
        root.after(
            1,
            lambda: restore_assistant_screen_position(app, pinned_x, pinned_y),
        )
        root.after(
            50,
            lambda: restore_assistant_screen_position(app, pinned_x, pinned_y),
        )
    except tk.TclError:
        pass


def create_staged_toplevel(root: tk.Misc) -> tk.Toplevel:
    """Create a withdrawn, invisible Toplevel parked off-screen."""
    popup = tk.Toplevel(root)
    try:
        popup.withdraw()
    except tk.TclError:
        pass
    try:
        popup.attributes("-alpha", 0.0)
    except tk.TclError:
        pass
    try:
        popup.geometry(CHILD_TOPLEVEL_OFFSCREEN)
    except tk.TclError:
        pass
    return popup


def deiconify_toplevel_noactivate(popup: tk.Toplevel) -> None:
    """Show *popup* without stealing focus from the assistant root."""
    try:
        popup.wm_attributes("-topmost", True)
        popup.deiconify()
    except tk.TclError:
        return
    if sys.platform != "win32":
        return
    try:
        import ctypes

        hwnd = int(popup.winfo_id())
        parent = ctypes.windll.user32.GetParent(hwnd)
        if parent:
            hwnd = parent
        # HWND_TOPMOST + NOMOVE/NOSIZE/NOACTIVATE
        ctypes.windll.user32.SetWindowPos(
            hwnd,
            -1,
            0,
            0,
            0,
            0,
            0x0002 | 0x0001 | 0x0010,
        )
    except (OSError, AttributeError, ValueError, TypeError, tk.TclError):
        pass


def reveal_staged_toplevel(
    popup: tk.Toplevel,
    *,
    geometry: str | None = None,
    noactivate: bool = False,
) -> None:
    """Apply final *geometry* (if any), then make the staged popup visible."""
    if geometry is not None:
        try:
            popup.geometry(geometry)
        except tk.TclError:
            pass
    if noactivate:
        deiconify_toplevel_noactivate(popup)
    else:
        try:
            popup.wm_attributes("-topmost", True)
            popup.deiconify()
        except tk.TclError:
            pass
    try:
        popup.attributes("-alpha", 1.0)
    except tk.TclError:
        pass


def open_child_toplevel(
    app,
    *,
    factory: Callable[[tk.Misc], tk.Toplevel] | None = None,
) -> tuple[tk.Toplevel, tuple[int, int]]:
    """Pin the assistant, create a staged child Toplevel, return both."""
    pinned = pin_assistant_screen_position(app)
    root = app.root
    popup = (factory or create_staged_toplevel)(root)
    return popup, pinned
