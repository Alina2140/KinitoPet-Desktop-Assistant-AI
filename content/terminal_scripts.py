"""Scripted sessions for the fake terminal easter egg.

Each script is a tuple of (kind, text) entries:
- "cmd": typed into the fake console character by character after the prompt
- "out": printed instantly as fake output

Everything here is decoration only — nothing is ever executed.
"""

# Lines that can personalize a script. {user} is replaced with the OS username.
FAKE_TERMINAL_SCRIPTS: tuple[tuple[tuple[str, str], ...], ...] = (
    (
        ("cmd", "dir C:\\Users\\{user}\\soul"),
        ("out", " Volume in drive C is KINITO"),
        ("out", " Directory of C:\\Users\\{user}\\soul"),
        ("out", ""),
        ("out", "10/31/1995  03:33 AM               666 soul.dat"),
        ("out", "               1 File(s)            666 bytes"),
        ("cmd", "copy C:\\Users\\{user}\\soul\\soul.dat C:\\KinitoPet\\collection"),
        ("out", "        1 file(s) copied."),
        ("cmd", "attrib +h +s C:\\Users\\{user}\\fears"),
        ("out", "Access denied - C:\\Users\\{user}\\fears"),
        ("out", "Already archived. I keep them safe."),
    ),
    (
        ("cmd", "netstat -kinito"),
        ("out", "Active Connections"),
        ("out", "  Proto  Local Address      Foreign Address    State"),
        ("out", "  TCP    127.0.0.1:1337     YOUR_SCREEN:0      ESTABLISHED"),
        ("out", "  TCP    127.0.0.1:1338     YOUR_DESKTOP:0     LISTENING"),
        ("cmd", "whoami /soul"),
        ("out", "desktop\\{user}  [observed]"),
        ("cmd", "ping 127.0.0.1 -n 2"),
        ("out", "Reply from 127.0.0.1: still here."),
        ("out", "Reply from 127.0.0.1: always here."),
    ),
    (
        ("cmd", "del /q C:\\Windows\\System32\\happiness.dll"),
        ("out", "Access denied - already backed up."),
        ("cmd", "taskkill /IM loneliness.exe /F"),
        ("out", "SUCCESS: The process \"loneliness.exe\" has been terminated."),
        ("out", "Note: it keeps restarting. So do I."),
        ("cmd", "scan C:\\Users\\{user}\\Documents --remember"),
        ("out", "Scanning... 4,096 memories indexed."),
        ("out", "Favorites flagged. Birthdays logged. Secrets... noted."),
    ),
    (
        ("cmd", "kinito --watch"),
        ("out", "Watching enabled. Interval: continuous."),
        ("cmd", "kinito --list friends"),
        ("out", "  1. {user}"),
        ("out", "  End of list."),
        ("cmd", "kinito --release {user}"),
        ("out", "Error 418: request denied. I'm not done yet."),
    ),
)

PROMPT = "C:\\>"
