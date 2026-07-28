"""Live open/active app awareness via process names only (no window titles in dialogue)."""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

CACHE_TTL_S = 2.5

# Shell / system / background hosts that are almost always present and not useful.
IGNORED_EXE_NAMES = frozenset(
    {
        "applicationframehost.exe",
        "backgroundtaskhost.exe",
        "cmd.exe",
        "conhost.exe",
        "csrss.exe",
        "ctfmon.exe",
        "dllhost.exe",
        "dwm.exe",
        "explorer.exe",
        "fontdrvhost.exe",
        "lockapp.exe",
        "lsass.exe",
        "msiexec.exe",
        "powershell.exe",
        "pwsh.exe",
        "runtimebroker.exe",
        "searchapp.exe",
        "searchhost.exe",
        "securityhealthservice.exe",
        "securityhealthsystray.exe",
        "services.exe",
        "shellexperiencehost.exe",
        "sihost.exe",
        "smartscreen.exe",
        "smss.exe",
        "startmenuexperiencehost.exe",
        "svchost.exe",
        "systemsettings.exe",
        "taskhostw.exe",
        "taskmgr.exe",
        "textinputhost.exe",
        "unsecapp.exe",
        "widgetservice.exe",
        "widgets.exe",
        "windowsterminal.exe",
        "wsl.exe",
        "wslhost.exe",
        "wslservice.exe",
        "yourphone.exe",
    }
)

# Optional pretty names — unknown apps still appear via FileDescription / exe stem.
FRIENDLY_NAMES = {
    "brave.exe": "Brave",
    "chrome.exe": "Chrome",
    "code.exe": "VS Code",
    "cursor.exe": "Cursor",
    "devenv.exe": "Visual Studio",
    "discord.exe": "Discord",
    "excel.exe": "Excel",
    "firefox.exe": "Firefox",
    "idea64.exe": "IntelliJ",
    "ms-teams.exe": "Teams",
    "msedge.exe": "Edge",
    "notepad.exe": "Notepad",
    "notepad++.exe": "Notepad++",
    "obs64.exe": "OBS",
    "onenote.exe": "OneNote",
    "outlook.exe": "Outlook",
    "photoshop.exe": "Photoshop",
    "powerpnt.exe": "PowerPoint",
    "pycharm64.exe": "PyCharm",
    "rtkuwp.exe": "Realtek Audio",
    "slack.exe": "Slack",
    "spotify.exe": "Spotify",
    "steam.exe": "Steam",
    "teams.exe": "Teams",
    "telegram.exe": "Telegram",
    "vlc.exe": "VLC",
    "winword.exe": "Word",
    "zoom.exe": "Zoom",
}


@dataclass(frozen=True)
class AppSnapshot:
    """Deduplicated open apps plus the currently focused one (friendly names)."""

    active: str | None
    open_apps: tuple[str, ...]

    @property
    def has_apps(self) -> bool:
        return bool(self.active or self.open_apps)


def _title_case_stem(stem: str) -> str:
    stem = stem.strip()
    if not stem:
        return "Unknown"
    return stem[0].upper() + stem[1:] if len(stem) > 1 else stem.upper()


def file_description_name(exe_path: str) -> str | None:
    """Read FileDescription from the PE version resource, if available."""
    if sys.platform != "win32" or not exe_path:
        return None
    try:
        import ctypes
        from ctypes import wintypes

        version = ctypes.windll.version
        size = version.GetFileVersionInfoSizeW(exe_path, None)
        if not size:
            return None
        buffer = ctypes.create_string_buffer(size)
        if not version.GetFileVersionInfoW(exe_path, 0, size, buffer):
            return None

        class LANGANDCODEPAGE(ctypes.Structure):
            _fields_ = [("wLanguage", wintypes.WORD), ("wCodePage", wintypes.WORD)]

        translation = ctypes.POINTER(LANGANDCODEPAGE)()
        translation_len = wintypes.UINT()
        if not version.VerQueryValueW(
            buffer,
            r"\VarFileInfo\Translation",
            ctypes.byref(translation),
            ctypes.byref(translation_len),
        ):
            return None
        if translation_len.value < ctypes.sizeof(LANGANDCODEPAGE):
            return None
        lang = translation[0]
        path = (
            rf"\StringFileInfo\{lang.wLanguage:04x}{lang.wCodePage:04x}\FileDescription"
        )
        value = ctypes.c_wchar_p()
        value_len = wintypes.UINT()
        if not version.VerQueryValueW(
            buffer, path, ctypes.byref(value), ctypes.byref(value_len)
        ):
            return None
        text = (value.value or "").strip()
        return text or None
    except (OSError, AttributeError, ValueError, TypeError):
        return None


def friendly_app_name(exe_path_or_name: str) -> str:
    """Map an exe path or basename to a short display name (any app, not a whitelist)."""
    name = Path(exe_path_or_name).name
    key = name.lower()
    if key in FRIENDLY_NAMES:
        return FRIENDLY_NAMES[key]
    description = file_description_name(exe_path_or_name)
    if description:
        # Prefer the first clause of long descriptions.
        short = description.split(",")[0].strip()
        if short:
            return short
    return _title_case_stem(Path(name).stem)


def is_noise_process(exe_path_or_name: str) -> bool:
    """Return True for shell/system/terminal hosts we should not surface."""
    path = Path(exe_path_or_name)
    key = path.name.lower()
    if key in IGNORED_EXE_NAMES:
        return True
    # Generic Windows host helpers under System32 / SysWOW64.
    parent = str(path.parent).lower().replace("/", "\\")
    in_system = parent.endswith("\\windows\\system32") or parent.endswith(
        "\\windows\\syswow64"
    )
    return bool(
        in_system
        and (
            key.endswith("host.exe")
            or key
            in {
                "conhost.exe",
                "dllhost.exe",
                "taskhostw.exe",
                "runtimebroker.exe",
            }
        )
    )


def format_app_aware_line(template: str, snapshot: AppSnapshot) -> str:
    """Fill ``{active_app}`` / ``{open_apps}`` placeholders from a snapshot."""
    active = snapshot.active or "something"
    open_apps = ", ".join(snapshot.open_apps) if snapshot.open_apps else "nothing much"
    return template.format(active_app=active, open_apps=open_apps)


def build_snapshot_from_process_map(
    pid_to_exe: dict[int, str],
    *,
    foreground_pid: int | None,
    own_pid: int | None = None,
) -> AppSnapshot:
    """Build a snapshot from pid→exe paths (testable without Win32)."""
    self_pid = os.getpid() if own_pid is None else own_pid
    names: list[str] = []
    seen: set[str] = set()
    active: str | None = None

    for pid, exe_path in pid_to_exe.items():
        if pid == self_pid:
            continue
        if is_noise_process(exe_path):
            continue
        label = friendly_app_name(exe_path)
        if label not in seen:
            seen.add(label)
            names.append(label)
        if foreground_pid is not None and pid == foreground_pid:
            active = label

    names.sort(key=str.lower)
    if active is None and foreground_pid is not None:
        fg_exe = pid_to_exe.get(foreground_pid)
        if fg_exe and foreground_pid != self_pid and not is_noise_process(fg_exe):
            active = friendly_app_name(fg_exe)
    return AppSnapshot(active=active, open_apps=tuple(names))


class AppContextCache:
    """Short-lived RAM cache for open/active app snapshots."""

    def __init__(self, ttl_s: float = CACHE_TTL_S) -> None:
        self._ttl_s = ttl_s
        self._snapshot: AppSnapshot | None = None
        self._fetched_at: float = 0.0

    def clear(self) -> None:
        """Drop the cached snapshot."""
        self._snapshot = None
        self._fetched_at = 0.0

    def get(self, *, force: bool = False) -> AppSnapshot:
        """Return a fresh or cached snapshot."""
        now = time.monotonic()
        if (
            not force
            and self._snapshot is not None
            and now - self._fetched_at <= self._ttl_s
        ):
            return self._snapshot
        self._snapshot = capture_open_apps()
        self._fetched_at = now
        return self._snapshot


def capture_open_apps() -> AppSnapshot:
    """Enumerate visible titled top-level window apps on Windows; empty elsewhere."""
    if sys.platform != "win32":
        return AppSnapshot(active=None, open_apps=())
    try:
        return _capture_open_apps_win32()
    except (OSError, AttributeError, ValueError, TypeError):
        return AppSnapshot(active=None, open_apps=())


def _capture_open_apps_win32() -> AppSnapshot:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    GW_OWNER = 4
    GWL_EXSTYLE = -20
    WS_EX_TOOLWINDOW = 0x00000080

    GetWindowThreadProcessId = user32.GetWindowThreadProcessId
    GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    GetWindowThreadProcessId.restype = wintypes.DWORD

    IsWindowVisible = user32.IsWindowVisible
    IsWindowVisible.argtypes = [wintypes.HWND]
    IsWindowVisible.restype = wintypes.BOOL

    GetWindow = user32.GetWindow
    GetWindow.argtypes = [wintypes.HWND, wintypes.UINT]
    GetWindow.restype = wintypes.HWND

    GetForegroundWindow = user32.GetForegroundWindow
    GetForegroundWindow.argtypes = []
    GetForegroundWindow.restype = wintypes.HWND

    GetWindowLongW = user32.GetWindowLongW
    GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
    GetWindowLongW.restype = wintypes.LONG

    GetWindowTextLengthW = user32.GetWindowTextLengthW
    GetWindowTextLengthW.argtypes = [wintypes.HWND]
    GetWindowTextLengthW.restype = ctypes.c_int

    OpenProcess = kernel32.OpenProcess
    OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    OpenProcess.restype = wintypes.HANDLE

    CloseHandle = kernel32.CloseHandle
    CloseHandle.argtypes = [wintypes.HANDLE]
    CloseHandle.restype = wintypes.BOOL

    QueryFullProcessImageNameW = kernel32.QueryFullProcessImageNameW
    QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD),
    ]
    QueryFullProcessImageNameW.restype = wintypes.BOOL

    def _pid_for_hwnd(hwnd: int) -> int | None:
        pid = wintypes.DWORD()
        GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return int(pid.value) or None

    def _exe_for_pid(pid: int) -> str | None:
        handle = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return None
        try:
            size = wintypes.DWORD(260)
            buf = ctypes.create_unicode_buffer(size.value)
            if not QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
                size = wintypes.DWORD(1024)
                buf = ctypes.create_unicode_buffer(size.value)
                if not QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
                    return None
            return buf.value
        finally:
            CloseHandle(handle)

    def _is_candidate_window(hwnd: int) -> bool:
        if not IsWindowVisible(hwnd):
            return False
        if GetWindow(hwnd, GW_OWNER):
            return False
        # Untitled windows are usually shell/background hosts.
        if GetWindowTextLengthW(hwnd) <= 0:
            return False
        try:
            ex_style = GetWindowLongW(hwnd, GWL_EXSTYLE)
        except OSError:
            return False
        return not ex_style & WS_EX_TOOLWINDOW

    pid_to_exe: dict[int, str] = {}
    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def _enum_callback(hwnd, _lparam):
        if not _is_candidate_window(hwnd):
            return True
        pid = _pid_for_hwnd(hwnd)
        if pid is None or pid in pid_to_exe:
            return True
        exe_path = _exe_for_pid(pid)
        if exe_path:
            pid_to_exe[pid] = exe_path
        return True

    enum_proc = WNDENUMPROC(_enum_callback)
    user32.EnumWindows(enum_proc, 0)

    foreground_pid: int | None = None
    fg = GetForegroundWindow()
    if fg:
        foreground_pid = _pid_for_hwnd(fg)
        if foreground_pid is not None and foreground_pid not in pid_to_exe:
            exe_path = _exe_for_pid(foreground_pid)
            if (
                exe_path
                and not is_noise_process(exe_path)
                and IsWindowVisible(fg)
                and not (GetWindowLongW(fg, GWL_EXSTYLE) & WS_EX_TOOLWINDOW)
            ):
                pid_to_exe[foreground_pid] = exe_path

    return build_snapshot_from_process_map(pid_to_exe, foreground_pid=foreground_pid)
