"""Windows per-monitor DPI helpers for the floating assistant.

Without per-monitor awareness, Windows bitmap-scales the overrideredirect
assistant window when it crosses monitors with different display scaling — Kinito
appears gigantic or tiny. Call :func:`enable_per_monitor_dpi_awareness`
before creating the first Tk window.
"""

from __future__ import annotations

import sys

# Win10 1703+ awareness contexts (special HANDLE values).
_DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4
_DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE = -3
# shcore SetProcessDpiAwareness
_PROCESS_PER_MONITOR_DPI_AWARE = 2

_BASE_DPI = 96


def enable_per_monitor_dpi_awareness() -> bool:
    """Opt into per-monitor DPI so Windows does not stretch our windows.

    Must run before the first GUI window (and ideally before ``tk.Tk()``).
    Returns True when awareness was set successfully.
    """
    if sys.platform != "win32":
        return False
    try:
        import ctypes

        user32 = ctypes.windll.user32
        if hasattr(user32, "SetProcessDpiAwarenessContext"):
            for context in (
                _DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2,
                _DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE,
            ):
                if user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(context)):
                    return True
        if hasattr(ctypes.windll, "shcore"):
            hr = int(
                ctypes.windll.shcore.SetProcessDpiAwareness(
                    _PROCESS_PER_MONITOR_DPI_AWARE
                )
            )
            # S_OK, or E_ACCESSDENIED if already set by something else.
            return hr == 0 or (hr & 0xFFFFFFFF) == 0x80070005
    except (OSError, AttributeError, ValueError, TypeError):
        return False
    return False


def window_dpi(hwnd: int | None) -> int:
    """Return the monitor DPI for *hwnd*, or system/base DPI as fallback."""
    if sys.platform != "win32" or not hwnd:
        return _BASE_DPI
    try:
        import ctypes

        user32 = ctypes.windll.user32
        if hasattr(user32, "GetDpiForWindow"):
            dpi = int(user32.GetDpiForWindow(int(hwnd)) or 0)
            if dpi > 0:
                return dpi
        if hasattr(user32, "GetDpiForSystem"):
            dpi = int(user32.GetDpiForSystem() or 0)
            if dpi > 0:
                return dpi
    except (OSError, AttributeError, ValueError, TypeError):
        pass
    return _BASE_DPI


def dpi_at_point(x: float, y: float) -> int:
    """Return effective DPI for the monitor containing (*x*, *y*)."""
    if sys.platform != "win32":
        return _BASE_DPI
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        # MONITOR_DEFAULTTONEAREST
        monitor = user32.MonitorFromPoint(
            wintypes.POINT(int(round(x)), int(round(y))),
            2,
        )
        if not monitor:
            return _BASE_DPI
        if hasattr(ctypes.windll, "shcore") and hasattr(
            ctypes.windll.shcore, "GetDpiForMonitor"
        ):
            dpi_x = ctypes.c_uint(0)
            dpi_y = ctypes.c_uint(0)
            # MDT_EFFECTIVE_DPI = 0
            hr = int(
                ctypes.windll.shcore.GetDpiForMonitor(
                    monitor, 0, ctypes.byref(dpi_x), ctypes.byref(dpi_y)
                )
            )
            if hr == 0 and int(dpi_x.value) > 0:
                return int(dpi_x.value)
    except (OSError, AttributeError, ValueError, TypeError):
        pass
    return _BASE_DPI


def max_monitor_dpi() -> int:
    """Return the highest effective DPI among connected monitors."""
    if sys.platform != "win32":
        return _BASE_DPI
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        if not (
            hasattr(ctypes.windll, "shcore")
            and hasattr(ctypes.windll.shcore, "GetDpiForMonitor")
        ):
            return _BASE_DPI

        found: list[int] = []

        def _callback(monitor, _dc, _rect, _data):
            dpi_x = ctypes.c_uint(0)
            dpi_y = ctypes.c_uint(0)
            hr = int(
                ctypes.windll.shcore.GetDpiForMonitor(
                    monitor, 0, ctypes.byref(dpi_x), ctypes.byref(dpi_y)
                )
            )
            if hr == 0 and int(dpi_x.value) > 0:
                found.append(int(dpi_x.value))
            return 1

        MonitorEnumProc = ctypes.WINFUNCTYPE(
            ctypes.c_int,
            wintypes.HMONITOR,
            wintypes.HDC,
            ctypes.POINTER(wintypes.RECT),
            wintypes.LPARAM,
        )
        if user32.EnumDisplayMonitors(0, 0, MonitorEnumProc(_callback), 0) and found:
            return max(found)
    except (OSError, AttributeError, ValueError, TypeError):
        pass
    return _BASE_DPI


def toplevel_hwnd(window) -> int | None:
    """Resolve the Win32 HWND for a Tk window (follow parent if needed)."""
    if sys.platform != "win32" or window is None:
        return None
    import tkinter as tk

    try:
        import ctypes

        hwnd = int(window.winfo_id())
        parent = ctypes.windll.user32.GetParent(hwnd)
        if parent:
            hwnd = int(parent)
        return hwnd
    except (OSError, AttributeError, ValueError, TypeError, tk.TclError):
        return None


def force_window_client_size(
    window,
    width: int,
    height: int,
    x: int = 0,
    y: int = 0,
    *,
    move: bool = False,
) -> None:
    """Pin *window* to *width*×*height*.

    By default only the size is forced (``move=False``). Repositioning during a
    DPI/monitor hop fights Tk's drag coordinates and causes a visible snap.
    """
    import tkinter as tk

    width = max(int(width), 1)
    height = max(int(height), 1)
    try:
        if move:
            window.geometry(f"{width}x{height}+{int(x)}+{int(y)}")
        else:
            # Keep the current origin; only correct a stretched client size.
            window.geometry(f"{width}x{height}")
    except tk.TclError:
        return
    if sys.platform != "win32":
        return
    hwnd = toplevel_hwnd(window)
    if not hwnd:
        return
    try:
        import ctypes

        # SWP_NOZORDER | SWP_NOACTIVATE; optionally SWP_NOMOVE
        flags = 0x0004 | 0x0010
        pos_x, pos_y = int(x), int(y)
        if not move:
            flags |= 0x0002  # SWP_NOMOVE
            pos_x, pos_y = 0, 0
        ctypes.windll.user32.SetWindowPos(
            int(hwnd),
            0,
            pos_x,
            pos_y,
            width,
            height,
            flags,
        )
    except (OSError, AttributeError, ValueError, TypeError):
        pass
