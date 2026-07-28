"""Win32 helpers for finding and moving other top-level windows (Windows only)."""

from __future__ import annotations

import math
import random
import sys
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass

TITLE_KEEP_PX = 40
HAND_TUCK_FRACTION = 0.5
USER_MOVE_TOLERANCE_PX = 24
MIN_DRAG_MOVE_PX = 80

SIDE_LEFT = "left"
SIDE_RIGHT = "right"


@dataclass(frozen=True)
class WindowRect:
    """Screen-space rectangle for a top-level window."""

    hwnd: int
    left: int
    top: int
    right: int
    bottom: int
    maximized: bool = False

    @property
    def width(self) -> int:
        return max(0, self.right - self.left)

    @property
    def height(self) -> int:
        return max(0, self.bottom - self.top)

    @property
    def origin(self) -> tuple[int, int]:
        return self.left, self.top


def clamp_window_origin(
    x: int,
    y: int,
    width: int,
    height: int,
    virtual_rect: tuple[int, int, int, int],
    *,
    title_keep_px: int = TITLE_KEEP_PX,
) -> tuple[int, int]:
    """Clamp a window origin so a title-bar strip stays on the virtual desktop."""
    del height  # height unused: we keep the top strip, not the full frame
    vx, vy, vw, vh = virtual_rect
    keep = max(1, int(title_keep_px))
    min_x = vx - width + keep
    max_x = vx + vw - keep
    min_y = vy
    max_y = vy + vh - keep
    if max_x < min_x:
        x = (min_x + max_x) // 2
    else:
        x = min(max(x, min_x), max_x)
    if max_y < min_y:
        y = (min_y + max_y) // 2
    else:
        y = min(max(y, min_y), max_y)
    return int(x), int(y)


def choose_grab_side(
    kinito_center_x: float,
    window_left: int,
    window_right: int,
) -> str:
    """Return ``left`` or ``right`` for the window edge closer to Kinito."""
    dist_left = abs(kinito_center_x - window_left)
    dist_right = abs(kinito_center_x - window_right)
    return SIDE_LEFT if dist_left <= dist_right else SIDE_RIGHT


def hand_sprite_for_side(side: str) -> str:
    """Map grab side to asset stem: left edge needs HandToRight, and vice versa."""
    return "HandToRight" if side == SIDE_LEFT else "HandToLeft"


def hand_tuck_geometry(
    side: str,
    window: WindowRect,
    hand_w: int,
    hand_h: int,
    *,
    tuck_fraction: float = HAND_TUCK_FRACTION,
) -> tuple[int, int]:
    """Return hand top-left so ~half the sprite sits under the window edge."""
    tuck = max(0.0, min(1.0, float(tuck_fraction)))
    if side == SIDE_LEFT:
        # Fingers point right into the window; left half sticks out.
        hand_x = int(window.left - hand_w * (1.0 - tuck))
    else:
        # Fingers point left into the window; right half sticks out.
        hand_x = int(window.right - hand_w * tuck)
    hand_y = int(window.top + (window.height - hand_h) / 2)
    return hand_x, hand_y


def position_diverged(
    expected: tuple[int, int],
    actual: tuple[int, int],
    *,
    tolerance_px: int = USER_MOVE_TOLERANCE_PX,
) -> bool:
    """Return True if the user (or another process) moved the window off our path."""
    ex, ey = expected
    ax, ay = actual
    return abs(ax - ex) > tolerance_px or abs(ay - ey) > tolerance_px


def choose_drag_end(
    left: int,
    top: int,
    width: int,
    height: int,
    virtual_rect: tuple[int, int, int, int],
    *,
    distance_range: tuple[int, int] = (120, 280),
    min_move_px: int = MIN_DRAG_MOVE_PX,
    attempts: int = 24,
) -> tuple[int, int] | None:
    """Pick a clamped destination with visible travel; None if the window is stuck."""
    best: tuple[int, int] | None = None
    best_dist = 0.0
    low, high = distance_range
    for _ in range(max(1, attempts)):
        distance = random.randint(low, high)
        angle = random.uniform(0.0, 2.0 * math.pi)
        end_x, end_y = clamp_window_origin(
            left + int(round(math.cos(angle) * distance)),
            top + int(round(math.sin(angle) * distance)),
            width,
            height,
            virtual_rect,
        )
        dist = math.hypot(end_x - left, end_y - top)
        if dist > best_dist:
            best = (end_x, end_y)
            best_dist = dist
    # Also try cardinal nudges — large windows often only have room on one axis.
    for dx, dy in (
        (high, 0),
        (-high, 0),
        (0, high),
        (0, -high),
        (high, high),
        (-high, high),
        (high, -high),
        (-high, -high),
    ):
        end_x, end_y = clamp_window_origin(
            left + dx, top + dy, width, height, virtual_rect
        )
        dist = math.hypot(end_x - left, end_y - top)
        if dist > best_dist:
            best = (end_x, end_y)
            best_dist = dist
    if best is None or best_dist < min_move_px:
        return None
    return best


def pick_window_target(
    windows: Sequence[WindowRect],
    *,
    kinito_center: tuple[float, float],
    max_distance: float | None = None,
    rng: Callable[[Sequence[WindowRect]], WindowRect] | None = None,
) -> tuple[WindowRect, str] | None:
    """Pick a window and grab side; prefer nearer windows when *max_distance* is set."""
    if not windows:
        return None
    cx, _cy = kinito_center

    def edge_distance(win: WindowRect) -> float:
        side = choose_grab_side(cx, win.left, win.right)
        edge_x = win.left if side == SIDE_LEFT else win.right
        return abs(cx - edge_x)

    candidates = list(windows)
    if max_distance is not None:
        near = [w for w in candidates if edge_distance(w) <= max_distance]
        if near:
            candidates = near

    chooser = rng or (lambda items: items[0])
    chosen = chooser(candidates)
    side = choose_grab_side(cx, chosen.left, chosen.right)
    return chosen, side


def virtual_screen_rect_windows() -> tuple[int, int, int, int] | None:
    """Return (x, y, width, height) for the Windows virtual desktop, if available."""
    if sys.platform != "win32":
        return None
    try:
        import ctypes

        user32 = ctypes.windll.user32
        x = int(user32.GetSystemMetrics(76))  # SM_XVIRTUALSCREEN
        y = int(user32.GetSystemMetrics(77))  # SM_YVIRTUALSCREEN
        width = int(user32.GetSystemMetrics(78))  # SM_CXVIRTUALSCREEN
        height = int(user32.GetSystemMetrics(79))  # SM_CYVIRTUALSCREEN
        if width <= 0 or height <= 0:
            return None
        return x, y, width, height
    except (OSError, AttributeError, ValueError):
        return None


def _tk_hwnd(window) -> int | None:
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
    except (OSError, AttributeError, ValueError, TypeError, RuntimeError):
        return None


SKIP_WINDOW_CLASSES = frozenset(
    {
        "Progman",
        "WorkerW",
        "Shell_TrayWnd",
        "Shell_SecondaryTrayWnd",
        "NotifyIconOverflowWindow",
        "Windows.UI.Core.CoreWindow",
        "ForegroundStaging",
        "XamlExplorerHostIslandWindow",
    }
)


def _is_window_cloaked(hwnd: int) -> bool:
    """Return True if DWM reports the window as cloaked (invisible UWP/host)."""
    try:
        import ctypes
        from ctypes import wintypes

        dwmapi = ctypes.windll.dwmapi
        cloaked = wintypes.DWORD()
        # DWMWA_CLOAKED = 14
        hr = dwmapi.DwmGetWindowAttribute(
            wintypes.HWND(int(hwnd)),
            14,
            ctypes.byref(cloaked),
            ctypes.sizeof(cloaked),
        )
        return hr == 0 and int(cloaked.value) != 0
    except (OSError, AttributeError, ValueError, TypeError):
        return False


def _window_class_name(hwnd: int) -> str:
    try:
        import ctypes

        buf = ctypes.create_unicode_buffer(256)
        ctypes.windll.user32.GetClassNameW(int(hwnd), buf, 256)
        return buf.value
    except (OSError, AttributeError, ValueError, TypeError):
        return ""


def _window_title(hwnd: int) -> str:
    try:
        import ctypes

        length = int(ctypes.windll.user32.GetWindowTextLengthW(int(hwnd)))
        if length <= 0:
            return ""
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(int(hwnd), buf, length + 1)
        return buf.value.strip()
    except (OSError, AttributeError, ValueError, TypeError):
        return ""


def list_movable_windows(
    *,
    exclude_hwnds: Iterable[int] = (),
) -> list[WindowRect]:
    """Enumerate visible top-level windows suitable for grab/drag/minimize."""
    if sys.platform != "win32":
        return []
    try:
        import ctypes
        from ctypes import wintypes
    except ImportError:
        return []

    user32 = ctypes.windll.user32
    GWL_EXSTYLE = -20
    GWL_STYLE = -16
    GW_OWNER = 4
    WS_EX_TOOLWINDOW = 0x00000080
    WS_DISABLED = 0x08000000
    exclude = {int(h) for h in exclude_hwnds if h}

    IsWindowVisible = user32.IsWindowVisible
    IsWindowVisible.argtypes = [wintypes.HWND]
    IsWindowVisible.restype = wintypes.BOOL

    IsIconic = user32.IsIconic
    IsIconic.argtypes = [wintypes.HWND]
    IsIconic.restype = wintypes.BOOL

    IsZoomed = user32.IsZoomed
    IsZoomed.argtypes = [wintypes.HWND]
    IsZoomed.restype = wintypes.BOOL

    GetWindow = user32.GetWindow
    GetWindow.argtypes = [wintypes.HWND, ctypes.c_uint]
    GetWindow.restype = wintypes.HWND

    GetWindowLongW = user32.GetWindowLongW
    GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
    GetWindowLongW.restype = wintypes.LONG

    GetWindowRect = user32.GetWindowRect
    GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    GetWindowRect.restype = wintypes.BOOL

    results: list[WindowRect] = []

    def _consider(hwnd: int) -> None:
        if hwnd in exclude:
            return
        if not IsWindowVisible(hwnd):
            return
        if IsIconic(hwnd):
            return
        if GetWindow(hwnd, GW_OWNER):
            return
        if _is_window_cloaked(hwnd):
            return
        class_name = _window_class_name(hwnd)
        if class_name in SKIP_WINDOW_CLASSES:
            return
        # Skip untitled shell/host windows — common source of "grabbing air".
        if not _window_title(hwnd):
            return
        try:
            style = int(GetWindowLongW(hwnd, GWL_STYLE))
            ex_style = int(GetWindowLongW(hwnd, GWL_EXSTYLE))
        except OSError:
            return
        if style & WS_DISABLED:
            return
        if ex_style & WS_EX_TOOLWINDOW:
            return
        rect = wintypes.RECT()
        if not GetWindowRect(hwnd, ctypes.byref(rect)):
            return
        width = int(rect.right) - int(rect.left)
        height = int(rect.bottom) - int(rect.top)
        if width < 120 or height < 80:
            return
        results.append(
            WindowRect(
                hwnd=int(hwnd),
                left=int(rect.left),
                top=int(rect.top),
                right=int(rect.right),
                bottom=int(rect.bottom),
                maximized=bool(IsZoomed(hwnd)),
            )
        )

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def _enum_callback(hwnd, _lparam):
        _consider(int(hwnd))
        return True

    user32.EnumWindows(WNDENUMPROC(_enum_callback), 0)
    return results


def get_window_rect(hwnd: int) -> WindowRect | None:
    """Return the current screen rect for *hwnd*, or None on failure."""
    if sys.platform != "win32":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        if not ctypes.windll.user32.IsWindow(int(hwnd)):
            return None
        rect = wintypes.RECT()
        if not ctypes.windll.user32.GetWindowRect(int(hwnd), ctypes.byref(rect)):
            return None
        return WindowRect(
            hwnd=int(hwnd),
            left=int(rect.left),
            top=int(rect.top),
            right=int(rect.right),
            bottom=int(rect.bottom),
            maximized=bool(ctypes.windll.user32.IsZoomed(int(hwnd))),
        )
    except (OSError, AttributeError, ValueError, TypeError):
        return None


def restore_window(hwnd: int) -> WindowRect | None:
    """Restore a maximized window so it can be moved; return the fresh rect."""
    if sys.platform != "win32":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        sw_restore = 9
        sw_shownormal = 1
        if user32.IsZoomed(int(hwnd)):
            user32.ShowWindow(int(hwnd), sw_restore)
            # Also force normal placement — Chrome/Electron often ignore ShowWindow alone.
            class WINDOWPLACEMENT(ctypes.Structure):
                _fields_ = [
                    ("length", wintypes.UINT),
                    ("flags", wintypes.UINT),
                    ("showCmd", wintypes.UINT),
                    ("ptMinPosition", wintypes.POINT),
                    ("ptMaxPosition", wintypes.POINT),
                    ("rcNormalPosition", wintypes.RECT),
                ]

            placement = WINDOWPLACEMENT()
            placement.length = ctypes.sizeof(WINDOWPLACEMENT)
            if user32.GetWindowPlacement(int(hwnd), ctypes.byref(placement)):
                placement.showCmd = sw_shownormal
                user32.SetWindowPlacement(int(hwnd), ctypes.byref(placement))
        return get_window_rect(int(hwnd))
    except (OSError, AttributeError, ValueError, TypeError):
        return get_window_rect(int(hwnd))


def _placement_move(hwnd: int, x: int, y: int, width: int, height: int) -> bool:
    """Move via SetWindowPlacement (most reliable for maximized Chromium/Electron)."""
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    sw_shownormal = 1

    class WINDOWPLACEMENT(ctypes.Structure):
        _fields_ = [
            ("length", wintypes.UINT),
            ("flags", wintypes.UINT),
            ("showCmd", wintypes.UINT),
            ("ptMinPosition", wintypes.POINT),
            ("ptMaxPosition", wintypes.POINT),
            ("rcNormalPosition", wintypes.RECT),
        ]

    placement = WINDOWPLACEMENT()
    placement.length = ctypes.sizeof(WINDOWPLACEMENT)
    if not user32.GetWindowPlacement(int(hwnd), ctypes.byref(placement)):
        return False
    placement.showCmd = sw_shownormal
    placement.flags = 0
    placement.rcNormalPosition.left = int(x)
    placement.rcNormalPosition.top = int(y)
    placement.rcNormalPosition.right = int(x + width)
    placement.rcNormalPosition.bottom = int(y + height)
    return bool(user32.SetWindowPlacement(int(hwnd), ctypes.byref(placement)))


def set_window_pos(hwnd: int, x: int, y: int) -> bool:
    """Move *hwnd*; return True only if the on-screen origin actually changed."""
    if sys.platform != "win32":
        return False
    try:
        import ctypes

        user32 = ctypes.windll.user32
        before = get_window_rect(int(hwnd))
        if before is None:
            return False

        if user32.IsZoomed(int(hwnd)):
            restore_window(int(hwnd))
            before = get_window_rect(int(hwnd))
            if before is None:
                return False

        width = before.width
        height = before.height
        target = (int(x), int(y))

        # 1) SetWindowPlacement — best for Chrome / Edge / VS Code / Teams.
        _placement_move(int(hwnd), target[0], target[1], width, height)
        after = get_window_rect(int(hwnd))
        if after is not None and not position_diverged(target, after.origin):
            return True

        # 2) Synchronous SetWindowPos (no ASYNC flag).
        swp_nosize = 0x0001
        swp_nozorder = 0x0004
        swp_noactivate = 0x0010
        user32.SetWindowPos(
            int(hwnd),
            0,
            target[0],
            target[1],
            0,
            0,
            swp_nosize | swp_nozorder | swp_noactivate,
        )
        after = get_window_rect(int(hwnd))
        if after is not None and not position_diverged(target, after.origin):
            return True

        # 3) MoveWindow fallback.
        user32.MoveWindow(int(hwnd), target[0], target[1], int(width), int(height), True)
        after = get_window_rect(int(hwnd))
        return after is not None and not position_diverged(target, after.origin)
    except (OSError, AttributeError, ValueError, TypeError):
        return False


def probe_window_movable(hwnd: int, *, nudge_px: int = 48) -> bool:
    """Return True if *hwnd* can be nudged and restored (filters immovable hosts)."""
    if sys.platform != "win32":
        return False
    before = get_window_rect(int(hwnd))
    if before is None:
        return False
    if before.maximized:
        restored = restore_window(int(hwnd))
        if restored is None:
            return False
        before = restored
    virtual = virtual_screen_rect_windows() or (0, 0, 1920, 1080)
    probe_x, probe_y = clamp_window_origin(
        before.left + nudge_px,
        before.top + nudge_px,
        before.width,
        before.height,
        virtual,
    )
    if abs(probe_x - before.left) < 8 and abs(probe_y - before.top) < 8:
        probe_x, probe_y = clamp_window_origin(
            before.left - nudge_px,
            before.top - nudge_px,
            before.width,
            before.height,
            virtual,
        )
    if abs(probe_x - before.left) < 8 and abs(probe_y - before.top) < 8:
        return False
    if not set_window_pos(int(hwnd), probe_x, probe_y):
        return False
    # Put it back so the user barely notices the probe.
    set_window_pos(int(hwnd), before.left, before.top)
    return True


def place_window_behind(hwnd: int, behind_hwnd: int) -> bool:
    """Stack *hwnd* directly below *behind_hwnd* in Z-order."""
    if sys.platform != "win32":
        return False
    try:
        import ctypes

        swp_nomove = 0x0002
        swp_nosize = 0x0001
        swp_noactivate = 0x0010
        ok = ctypes.windll.user32.SetWindowPos(
            int(hwnd),
            int(behind_hwnd),
            0,
            0,
            0,
            0,
            swp_nomove | swp_nosize | swp_noactivate,
        )
        return bool(ok)
    except (OSError, AttributeError, ValueError, TypeError):
        return False


def minimize_window(hwnd: int) -> bool:
    """Minimize *hwnd* via ShowWindow(SW_MINIMIZE)."""
    if sys.platform != "win32":
        return False
    try:
        import ctypes

        sw_minimize = 6
        return bool(ctypes.windll.user32.ShowWindow(int(hwnd), sw_minimize))
    except (OSError, AttributeError, ValueError, TypeError):
        return False


def collect_own_hwnds(*windows) -> set[int]:
    """Collect Win32 HWNDs for the given Tk windows (skipping missing ones)."""
    hwnds: set[int] = set()
    for window in windows:
        if window is None:
            continue
        try:
            if hasattr(window, "winfo_exists") and not window.winfo_exists():
                continue
        except Exception:
            continue
        hwnd = _tk_hwnd(window)
        if hwnd:
            hwnds.add(hwnd)
    return hwnds
