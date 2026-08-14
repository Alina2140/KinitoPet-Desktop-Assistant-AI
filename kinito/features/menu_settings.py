"""UI for choosing which menu buttons are visible."""

from __future__ import annotations

import tkinter as tk
from tkinter import BooleanVar, Checkbutton, Frame, Label, Scrollbar, Toplevel

from content.menu_visibility import (
    LOCKED_MENU_BUTTON_IDS,
    MENU_VISIBILITY_SECTIONS,
)
from kinito.window_icon import apply_window_icon


class MenuSettingsMixin:
    """Open a settings panel to show/hide menu buttons."""

    MENU_SETTINGS_WIDTH = 520
    MENU_SETTINGS_HEIGHT = 560

    def open_menu_button_settings(self) -> None:
        """Show a scrollable checkbox panel for menu button visibility."""
        from content import dialogue as dlg

        if hasattr(self, "speak"):
            try:
                self.speak(dlg.pick_line(dlg.MENU_BUTTONS_OPEN_LINES), skip_ai=True)
            except Exception:
                pass

        existing = getattr(self, "_menu_settings_window", None)
        if existing is not None:
            try:
                if existing.winfo_exists():
                    existing.lift()
                    existing.focus_force()
                    return
            except tk.TclError:
                pass

        hidden = set(getattr(self, "_hidden_menu_buttons", set()))
        vars_by_id: dict[str, BooleanVar] = {}

        window = Toplevel(self.root)
        self._menu_settings_window = window
        window.title("Menu Buttons")
        apply_window_icon(window)
        window.wm_attributes("-topmost", True)
        window.geometry(f"{self.MENU_SETTINGS_WIDTH}x{self.MENU_SETTINGS_HEIGHT}")

        self.root.update_idletasks()
        center = getattr(self, "_centered_origin_on_primary", None)
        if callable(center):
            x, y = center(self.MENU_SETTINGS_WIDTH, self.MENU_SETTINGS_HEIGHT)
        else:
            vroot_x = self.root.winfo_vrootx()
            vroot_y = self.root.winfo_vrooty()
            vroot_w = self.root.winfo_vrootwidth()
            vroot_h = self.root.winfo_vrootheight()
            x = vroot_x + (vroot_w - self.MENU_SETTINGS_WIDTH) // 2
            y = vroot_y + (vroot_h - self.MENU_SETTINGS_HEIGHT) // 2
        window.geometry(
            f"{self.MENU_SETTINGS_WIDTH}x{self.MENU_SETTINGS_HEIGHT}+{int(x)}+{int(y)}"
        )

        header = Label(
            window,
            text="Show or hide menu buttons. Changes save automatically.",
            wraplength=self.MENU_SETTINGS_WIDTH - 40,
            justify="left",
            padx=12,
            pady=8,
        )
        header.pack(fill="x")

        body = Frame(window)
        body.pack(fill="both", expand=True, padx=8, pady=4)

        canvas = tk.Canvas(body, highlightthickness=0)
        scrollbar = Scrollbar(body, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = Frame(canvas)
        inner_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_inner_configure(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_configure(event):
            canvas.itemconfigure(inner_id, width=event.width)

        inner.bind("<Configure>", _on_inner_configure)
        canvas.bind("<Configure>", _on_canvas_configure)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-event.delta / 120), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _persist_from_vars():
            new_hidden = {
                entry_id
                for entry_id, var in vars_by_id.items()
                if not var.get() and entry_id not in LOCKED_MENU_BUTTON_IDS
            }
            self._hidden_menu_buttons = new_hidden
            if hasattr(self, "_persist_settings"):
                self._persist_settings()

        for section_title, entries in MENU_VISIBILITY_SECTIONS:
            section_label = Label(
                inner,
                text=section_title,
                font=("Segoe UI", 11, "bold"),
                anchor="w",
                pady=6,
            )
            section_label.pack(fill="x", padx=8)

            row_frame = None
            for index, (entry_id, label, _aliases) in enumerate(entries):
                if index % 2 == 0:
                    row_frame = Frame(inner)
                    row_frame.pack(fill="x", padx=8, pady=2)
                cell = Frame(row_frame)
                cell.pack(side="left", fill="x", expand=True, padx=4)
                locked = entry_id in LOCKED_MENU_BUTTON_IDS
                var = BooleanVar(value=(entry_id not in hidden) or locked)
                vars_by_id[entry_id] = var
                check = Checkbutton(
                    cell,
                    text=label + (" (always on)" if locked else ""),
                    variable=var,
                    anchor="w",
                    command=_persist_from_vars,
                    state=("disabled" if locked else "normal"),
                )
                check.pack(fill="x")

        def _on_close():
            try:
                canvas.unbind_all("<MouseWheel>")
            except tk.TclError:
                pass
            self._menu_settings_window = None
            try:
                window.destroy()
            except tk.TclError:
                pass

        footer = Frame(window)
        footer.pack(fill="x", padx=12, pady=8)
        close_btn = tk.Button(footer, text="Close", command=_on_close)
        close_btn.pack(side="right")
        window.protocol("WM_DELETE_WINDOW", _on_close)
