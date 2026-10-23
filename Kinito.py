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


if __name__ == "__main__":
    main()
