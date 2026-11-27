"""Entry point for the KinitoPET desktop virtual assistant."""

# DPI awareness must be set before Tk loads / creates any HWND.
from kinito.dpi import enable_per_monitor_dpi_awareness

enable_per_monitor_dpi_awareness()

import tkinter as tk  # noqa: E402

from kinito.app import FloatingAssistant  # noqa: E402


def main():
    """Create the Tk root window and start the floating assistant."""
    root = tk.Tk()
    FloatingAssistant(root)
    root.mainloop()
    # The Tk mainloop is over, but library driver threads (TTS engine,
    # pygame/SDL audio) can keep the interpreter alive for seconds. App
    # threads are daemons and state is already persisted — exit hard.
    import os

    os._exit(0)


if __name__ == "__main__":
    main()
