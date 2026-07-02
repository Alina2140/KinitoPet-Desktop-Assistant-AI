"""Safe helpers for recurring Tk ``after`` callbacks."""

import tkinter as tk


def root_is_alive(root, *, running: bool = True) -> bool:
    """Return whether *root* still exists and the app is running."""
    if not running:
        return False
    try:
        return bool(root.winfo_exists())
    except tk.TclError:
        return False


def cancel_after(root, owner, attr: str) -> None:
    """Cancel a pending ``after`` job stored on *owner* under *attr*."""
    timer_id = getattr(owner, attr, None)
    if timer_id is None:
        return
    try:
        root.after_cancel(timer_id)
    except (tk.TclError, ValueError):
        pass
    setattr(owner, attr, None)


def schedule_after(root, owner, attr: str, delay_ms: int, callback) -> None:
    """Schedule *callback* once, replacing any previous job in *attr*."""
    cancel_after(root, owner, attr)
    if not root_is_alive(root, running=getattr(owner, "_running", True)):
        return
    setattr(owner, attr, root.after(delay_ms, callback))
