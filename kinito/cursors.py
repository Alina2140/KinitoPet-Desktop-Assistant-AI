"""Swap the Windows system arrow cursor for Kinito-themed cursors.

PNG art from gameAssets/cursors/ is wrapped in .cur files at runtime and
installed with SetSystemCursor, so the custom arrow appears everywhere while
Kinito runs. The previous cursors are restored on style change or shutdown
via SystemParametersInfo(SPI_SETCURSORS).
"""

from __future__ import annotations

import ctypes
import os
import struct
import tempfile
import threading
from ctypes import wintypes

from kinito.assets import cursors_directory

CURSOR_STYLE_SYSTEM = "system"
CURSOR_STYLE_POINTER = "pointer"
CURSOR_STYLE_HAND = "hand"
CURSOR_STYLE_SQUID = "squid"
CURSOR_STYLES = (
    CURSOR_STYLE_SYSTEM,
    CURSOR_STYLE_POINTER,
    CURSOR_STYLE_HAND,
    CURSOR_STYLE_SQUID,
)

# style -> ((idle file, hotspot), (pressed file, hotspot) | None)
_CURSOR_ART = {
    CURSOR_STYLE_POINTER: ("cursorHandPointer.png", (0, 0), None, None),
    CURSOR_STYLE_HAND: (
        "cursorHandOpen.png",
        (15, 4),
        "cursorHandGrab.png",
        (13, 4),
    ),
    CURSOR_STYLE_SQUID: ("cursorSquid.png", (0, 0), None, None),
}

_OCR_NORMAL = 32512
_SPI_SETCURSORS = 0x0057
_WH_MOUSE_LL = 14
_WM_LBUTTONDOWN = 0x0201
_WM_LBUTTONUP = 0x0202
_WM_RBUTTONDOWN = 0x0204
_WM_RBUTTONUP = 0x0205
_WM_MBUTTONDOWN = 0x0207
_WM_MBUTTONUP = 0x0208
_WM_QUIT = 0x0012
_IMAGE_CURSOR = 2
_LR_LOADFROMFILE = 0x0010

_user32 = ctypes.windll.user32
_kernel32 = ctypes.windll.kernel32

_LowLevelMouseProc = ctypes.WINFUNCTYPE(
    wintypes.LPARAM, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM
)
_kernel32.GetCurrentThreadId.restype = wintypes.DWORD
_user32.SetWindowsHookExW.restype = wintypes.HANDLE
_user32.SetWindowsHookExW.argtypes = (
    ctypes.c_int,
    _LowLevelMouseProc,
    wintypes.HINSTANCE,
    wintypes.DWORD,
)
_user32.LoadImageW.restype = wintypes.HANDLE
_user32.LoadImageW.argtypes = (
    wintypes.HINSTANCE,
    wintypes.LPCWSTR,
    wintypes.UINT,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.UINT,
)
_user32.CallNextHookEx.restype = wintypes.LPARAM
_user32.CallNextHookEx.argtypes = (
    wintypes.HANDLE,
    ctypes.c_int,
    wintypes.WPARAM,
    wintypes.LPARAM,
)
_user32.UnhookWindowsHookEx.argtypes = (wintypes.HANDLE,)
_user32.PostThreadMessageW.argtypes = (
    wintypes.DWORD,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
)
_user32.SetSystemCursor.argtypes = (wintypes.HANDLE, wintypes.DWORD)
_user32.CopyIcon.restype = wintypes.HANDLE
_user32.CopyIcon.argtypes = (wintypes.HANDLE,)
_user32.DestroyCursor.argtypes = (wintypes.HANDLE,)
_user32.SystemParametersInfoW.argtypes = (
    wintypes.UINT,
    wintypes.UINT,
    wintypes.LPVOID,
    wintypes.UINT,
)


def _png_size(png_bytes: bytes) -> tuple[int, int]:
    """Read width/height from a PNG header without decoding."""
    if png_bytes[:8] != b"\x89PNG\r\n\x1a\n":
        return (32, 32)
    return struct.unpack(">II", png_bytes[16:24])


def _write_cur_file(directory: str, name: str, png_path: str, hotspot) -> str:
    """Wrap *png_path* in a .cur container and return the file path."""
    with open(png_path, "rb") as handle:
        png = handle.read()
    width, height = _png_size(png)
    header = struct.pack("<HHH", 0, 2, 1)
    entry = struct.pack(
        "<BBBBHHII",
        width if width < 256 else 0,
        height if height < 256 else 0,
        0,
        0,
        int(hotspot[0]),
        int(hotspot[1]),
        len(png),
        22,
    )
    path = os.path.join(directory, name)
    with open(path, "wb") as handle:
        handle.write(header + entry + png)
    return path


def _load_cursor(cur_path: str):
    """Load a .cur file as an HCURSOR, or None on failure."""
    handle = _user32.LoadImageW(
        None, cur_path, _IMAGE_CURSOR, 0, 0, _LR_LOADFROMFILE
    )
    return handle or None


def _set_arrow_cursor(hcursor) -> None:
    """Replace the system arrow cursor with a copy of *hcursor*.

    SetSystemCursor destroys the handle it is given, so hand it a CopyIcon
    duplicate — the hook reuses the originals for every click transition.
    """
    if not hcursor:
        return
    copy = _user32.CopyIcon(hcursor)
    if copy:
        _user32.SetSystemCursor(copy, _OCR_NORMAL)


class _CursorSwapper:
    """Owns the temp .cur files, the mouse hook, and restore-on-exit."""

    _CUR_DIR_NAME = "kinito_cursors"

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cur_dir = os.path.join(tempfile.gettempdir(), self._CUR_DIR_NAME)
        self._hook = None
        self._hook_proc = None
        self._hook_thread_id = 0
        self._idle_handle = None
        self._down_handle = None
        self._applied = CURSOR_STYLE_SYSTEM

    def apply(self, style: str) -> bool:
        """Install *style*'s cursor (or restore the system arrow)."""
        with self._lock:
            self._stop_hook()
            self.restore()
            if style not in _CURSOR_ART:
                self._applied = CURSOR_STYLE_SYSTEM
                return False
            idle_file, idle_hot, down_file, down_hot = _CURSOR_ART[style]
            idle_png = os.path.join(cursors_directory, idle_file)
            if not os.path.isfile(idle_png):
                self._applied = CURSOR_STYLE_SYSTEM
                return False
            try:
                os.makedirs(self._cur_dir, exist_ok=True)
                idle_cur = _write_cur_file(
                    self._cur_dir, f"{style}_idle.cur", idle_png, idle_hot
                )
                self._idle_handle = _load_cursor(idle_cur)
                down_cur = None
                if down_file is not None:
                    down_png = os.path.join(cursors_directory, down_file)
                    if os.path.isfile(down_png):
                        down_cur = _write_cur_file(
                            self._cur_dir,
                            f"{style}_down.cur",
                            down_png,
                            down_hot or idle_hot,
                        )
                        self._down_handle = _load_cursor(down_cur)
            except OSError:
                self._applied = CURSOR_STYLE_SYSTEM
                return False
            if self._idle_handle is None:
                self._applied = CURSOR_STYLE_SYSTEM
                return False
            _set_arrow_cursor(self._idle_handle)
            self._applied = style
            if self._down_handle is not None:
                self._start_hook()
            return True

    def restore(self) -> None:
        """Bring back the user's normal cursors."""
        self._stop_hook()
        try:
            _user32.SystemParametersInfoW(_SPI_SETCURSORS, 0, None, 0)
        except Exception:
            pass
        for handle in (self._idle_handle, self._down_handle):
            if handle:
                _user32.DestroyCursor(handle)
        self._idle_handle = None
        self._down_handle = None
        self._applied = CURSOR_STYLE_SYSTEM

    def _start_hook(self) -> None:
        """Watch global mouse buttons so open-hand turns into grab while held."""

        def _proc(nCode, wParam, lParam):
            try:
                if nCode == 0:
                    if wParam in (
                        _WM_LBUTTONDOWN,
                        _WM_RBUTTONDOWN,
                        _WM_MBUTTONDOWN,
                    ):
                        _set_arrow_cursor(self._down_handle)
                    elif wParam in (_WM_LBUTTONUP, _WM_RBUTTONUP, _WM_MBUTTONUP):
                        _set_arrow_cursor(self._idle_handle)
            except Exception:
                pass
            try:
                return _user32.CallNextHookEx(None, nCode, wParam, lParam)
            except Exception:
                return 0

        self._hook_proc = _LowLevelMouseProc(_proc)
        ready = threading.Event()

        def _thread_main():
            self._hook = _user32.SetWindowsHookExW(
                _WH_MOUSE_LL, self._hook_proc, None, 0
            )
            self._hook_thread_id = _kernel32.GetCurrentThreadId()
            ready.set()
            msg = wintypes.MSG()
            while _user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                _user32.TranslateMessage(ctypes.byref(msg))
                _user32.DispatchMessageW(ctypes.byref(msg))
            if self._hook is not None:
                _user32.UnhookWindowsHookEx(self._hook)
                self._hook = None

        thread = threading.Thread(target=_thread_main, daemon=True)
        thread.start()
        ready.wait(timeout=2.0)

    def _stop_hook(self) -> None:
        thread_id = self._hook_thread_id
        self._hook_thread_id = 0
        if thread_id:
            try:
                _user32.PostThreadMessageW(thread_id, _WM_QUIT, 0, 0)
            except Exception:
                pass


_cursor_swapper: _CursorSwapper | None = None


def _swapper() -> _CursorSwapper:
    global _cursor_swapper
    if _cursor_swapper is None:
        _cursor_swapper = _CursorSwapper()
    return _cursor_swapper


def apply_cursor_style(style: str) -> bool:
    """Switch the system arrow cursor to *style* (or restore for 'system')."""
    if os.name != "nt":
        return False
    try:
        return _swapper().apply(style)
    except Exception:
        return False


def restore_system_cursors() -> None:
    """Restore the original system cursors (call on shutdown)."""
    if os.name != "nt" or _cursor_swapper is None:
        return
    try:
        _cursor_swapper.restore()
    except Exception:
        pass


def cursor_style_image(master, style: str, size: int = 36):
    """Return a *size*-high PhotoImage preview of *style*, or None."""
    try:
        from PIL import Image, ImageDraw, ImageTk
    except Exception:
        return None
    try:
        if style == CURSOR_STYLE_SYSTEM:
            img = Image.new("RGBA", (round(size * 0.78), size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            s = size / 32.0
            arrow = [(4, 2), (4, 26), (11, 19), (15, 30), (19, 28), (15, 17), (24, 17)]
            pts = [(x * s, y * s) for x, y in arrow]
            draw.polygon(pts, fill="white", outline="#202020")
        else:
            art = _CURSOR_ART.get(style)
            if not art:
                return None
            png_path = os.path.join(cursors_directory, art[0])
            img = Image.open(png_path).convert("RGBA")
            scale = size / img.height
            img = img.resize(
                (max(1, round(img.width * scale)), size), Image.NEAREST
            )
        # Pure-white fill vanishes on the cream button — tint it off-white.
        px = img.load()
        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = px[x, y]
                if a and r >= 235 and g >= 235 and b >= 235:
                    px[x, y] = (222, 226, 234, a)
        return ImageTk.PhotoImage(img, master=master)
    except Exception:
        return None


def normalize_cursor_style(value: object) -> str:
    """Return *value* if it is a known cursor style, else 'system'."""
    style = str(value).strip().lower() if isinstance(value, str) else ""
    return style if style in CURSOR_STYLES else CURSOR_STYLE_SYSTEM


# Last-resort restore: if the app dies without a clean shutdown path, still
# hand the user's normal cursor back instead of leaving Kinito art behind.
if os.name == "nt":
    import atexit

    atexit.register(restore_system_cursors)
