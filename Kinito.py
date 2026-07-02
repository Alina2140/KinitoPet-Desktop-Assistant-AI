"""Entry point for the KinitoPET desktop virtual assistant."""

import tkinter as tk

from kinito.app import FloatingAssistant


def main():
    """Create the Tk root window and start the floating assistant."""
    root = tk.Tk()
    FloatingAssistant(root)
    root.mainloop()


if __name__ == "__main__":
    main()
