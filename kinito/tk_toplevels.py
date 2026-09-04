"""Helpers for child Toplevels under an overrideredirect assistant root.

On Windows, creating a Toplevel under a borderless/transparent root can briefly
teleport the parent and flash a default frame. Stage children off-screen and
invisible first, then reveal once geometry is final.

Large owned windows (especially on another monitor) can also keep dragging the
overrideredirect parent around for as long as they stay open — detach the Win32
owner link and hold/restore the assistant position while the popup lives.
"""

from __future__ import annotations

import sys
import tkinter as tk
from collections.abc import Callable

CHILD_TOPLEVEL_OFFSCREEN = "-10000-10000"
_HOLD_HEARTBEAT_MS = 50


def _toplevel_hwnd(window) -> int | None:
    """Resolve a Tk window to its top-level Win32 HWND."""
    if sys.platform != "win32":
        return None
    try:
        import ctypes

        hwnd = int(window.winfo_id())
        parent = ctypes.windll.user32.GetParent(hwnd)
        if parent:
            hwnd = int(parent)
        return hwnd
    except (OSError, AttributeError, ValueError, TypeError, RuntimeError, tk.TclError):
        return None


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


def _force_root_screen_position(root, pinned_x: int, pinned_y: int) -> None:
    """Move *root* with Win32 SetWindowPos so DPI/async remaps cannot ignore geometry()."""
    if sys.platform != "win32":
        return
    hwnd = _toplevel_hwnd(root)
    if not hwnd:
        return
    try:
        import ctypes

        # SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE
        ctypes.windll.user32.SetWindowPos(
            int(hwnd),
            0,
            int(pinned_x),
            int(pinned_y),
            0,
            0,
            0x0001 | 0x0004 | 0x0010,
        )
    except (OSError, AttributeError, ValueError, TypeError):
        pass


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
    _force_root_screen_position(root, int(pinned_x), int(pinned_y))


def hold_assistant_screen_position(
    app, pinned_x: int, pinned_y: int, *, token: object
) -> None:
    """Keep *pinned* applied until *token* is released (beats async Win32 remaps)."""
    try:
        app._assistant_position_hold = (int(pinned_x), int(pinned_y), token)
        gen = int(getattr(app, "_assistant_position_hold_gen", 0)) + 1
        app._assistant_position_hold_gen = gen
    except Exception:
        return
    restore_assistant_screen_position(app, pinned_x, pinned_y)
    _schedule_hold_heartbeat(app, gen)


def _schedule_hold_heartbeat(app, gen: int) -> None:
    """Re-enforce the hold on a timer — Configure alone misses some Win32 moves."""
    root = getattr(app, "root", None)
    if root is None:
        return

    def _tick():
        if getattr(app, "_assistant_position_hold_gen", None) != gen:
            return
        if not enforce_assistant_position_hold(app):
            return
        try:
            root.after(_HOLD_HEARTBEAT_MS, _tick)
        except tk.TclError:
            pass

    try:
        root.after(_HOLD_HEARTBEAT_MS, _tick)
    except tk.TclError:
        pass


def release_assistant_position_hold(
    app, *, token: object, restore: bool = True
) -> None:
    """Clear a hold created with *token*; optionally restore one last time."""
    hold = getattr(app, "_assistant_position_hold", None)
    if not isinstance(hold, tuple) or len(hold) != 3:
        try:
            app._assistant_position_hold = None
        except Exception:
            pass
        return
    pinned_x, pinned_y, held_token = hold
    if held_token is not token:
        return
    try:
        app._assistant_position_hold = None
        app._assistant_position_hold_gen = int(
            getattr(app, "_assistant_position_hold_gen", 0)
        ) + 1
    except Exception:
        pass
    if restore:
        restore_assistant_screen_position(app, pinned_x, pinned_y)


def clear_assistant_position_hold(app) -> None:
    """Drop any active hold without restoring (e.g. user started dragging)."""
    try:
        app._assistant_position_hold = None
        app._assistant_position_hold_gen = int(
            getattr(app, "_assistant_position_hold_gen", 0)
        ) + 1
    except Exception:
        pass


def enforce_assistant_position_hold(app) -> bool:
    """If a hold is active and the root drifted, snap it back. Return True if held."""
    hold = getattr(app, "_assistant_position_hold", None)
    if not isinstance(hold, tuple) or len(hold) < 2:
        return False
    try:
        pinned_x, pinned_y = int(hold[0]), int(hold[1])
    except (TypeError, ValueError):
        return False
    root = getattr(app, "root", None)
    if root is None:
        return True
    try:
        x = int(root.winfo_rootx())
        y = int(root.winfo_rooty())
    except (tk.TclError, TypeError, ValueError):
        restore_assistant_screen_position(app, pinned_x, pinned_y)
        return True
    if x != pinned_x or y != pinned_y:
        restore_assistant_screen_position(app, pinned_x, pinned_y)
    else:
        try:
            app.x = pinned_x
            app.y = pinned_y
        except Exception:
            pass
    return True


def schedule_assistant_position_restore(app, pinned_x: int, pinned_y: int) -> None:
    """Restore immediately and again shortly after Windows finishes mapping."""
    restore_assistant_screen_position(app, pinned_x, pinned_y)
    root = getattr(app, "root", None)
    if root is None:
        return
    try:
        for delay_ms in (1, 50, 200, 500):
            root.after(
                delay_ms,
                lambda x=pinned_x, y=pinned_y: restore_assistant_screen_position(
                    app, x, y
                ),
            )
    except tk.TclError:
        pass


def detach_toplevel_owner(popup: tk.Toplevel) -> None:
    """Clear the Win32 owner so large/remote popups cannot drag the assistant root."""
    if sys.platform != "win32":
        return
    hwnd = _toplevel_hwnd(popup)
    if not hwnd:
        return
    try:
        import ctypes

        # GWLP_HWNDPARENT = -8
        if ctypes.sizeof(ctypes.c_void_p) == 8:
            ctypes.windll.user32.SetWindowLongPtrW(int(hwnd), -8, 0)
        else:
            ctypes.windll.user32.SetWindowLongW(int(hwnd), -8, 0)
    except (OSError, AttributeError, ValueError, TypeError):
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
    # Break the owned-window link early — before geometry/reveal — so Windows does
    # not keep relocating the overrideredirect parent toward the popup's monitor.
    detach_toplevel_owner(popup)
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

        hwnd = _toplevel_hwnd(popup)
        if not hwnd:
            return
        # HWND_TOPMOST + NOMOVE/NOSIZE/NOACTIVATE
        ctypes.windll.user32.SetWindowPos(
            int(hwnd),
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
    # Re-detach in case Tk re-applied ownership while configuring the window.
    detach_toplevel_owner(popup)
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
    detach_toplevel_owner(popup)


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
