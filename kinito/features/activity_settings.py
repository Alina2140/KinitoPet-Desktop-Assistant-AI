"""UI for tuning how often spontaneous activities may happen."""

from __future__ import annotations

import tkinter as tk
from tkinter import Frame, IntVar, Label, Scale, Scrollbar, Toplevel

from content.activity_weights import (
    ACTIVITY_SECTIONS,
    ACTIVITY_TOGGLE_ATTRS,
    ACTIVITY_WEIGHT_DEFAULT,
    ActivityEntry,
)
from kinito.features.games.base import center_toplevel
from kinito.window_icon import apply_window_icon

# Matches the paint window's retro UI palette.
_UI_BG = "#e6ded5"


class ActivitySettingsMixin:
    """Open a settings panel to enable/disable and re-weight spontaneous activities."""

    ACTIVITY_SETTINGS_WIDTH = 480
    ACTIVITY_SETTINGS_HEIGHT = 560

    def _activity_weights_map(self) -> dict[str, int]:
        weights = getattr(self, "_activity_weights", None)
        return weights if isinstance(weights, dict) else {}

    def _activity_chance_mult(self, activity_id: str) -> float:
        """Return the user's chance multiplier (0.0–1.0) for *activity_id*."""
        weight = self._activity_weights_map().get(activity_id, ACTIVITY_WEIGHT_DEFAULT)
        try:
            return max(0.0, min(1.0, int(weight) / 100.0))
        except (TypeError, ValueError):
            return 1.0

    def _activity_enabled(self, activity_id: str) -> bool:
        """Return True when *activity_id* has a non-zero chance weight."""
        return self._activity_chance_mult(activity_id) > 0.0

    def open_activity_settings(self) -> None:
        """Show a scrollable panel of sliders for spontaneous activity chances."""
        from content import dialogue as dlg

        if hasattr(self, "speak"):
            try:
                self.speak(
                    dlg.pick_line(dlg.ACTIVITY_SETTINGS_OPEN_LINES), skip_ai=True
                )
            except Exception:
                pass

        existing = getattr(self, "_activity_settings_window", None)
        if existing is not None:
            try:
                if existing.winfo_exists():
                    existing.lift()
                    existing.focus_force()
                    return
            except tk.TclError:
                pass

        stored = self._activity_weights_map()
        vars_by_id: dict[str, IntVar] = {}

        window = Toplevel(self.root)
        self._activity_settings_window = window
        window.title("Activities")
        apply_window_icon(window)
        window.wm_attributes("-topmost", True)
        window.configure(bg=_UI_BG)
        center_toplevel(
            self,
            window,
            self.ACTIVITY_SETTINGS_WIDTH,
            self.ACTIVITY_SETTINGS_HEIGHT,
        )

        outer = Frame(window, bg=_UI_BG, bd=2, relief=tk.RAISED)
        outer.pack(fill="both", expand=True, padx=4, pady=4)

        header = Label(
            outer,
            text=(
                "How often may Kinito do these things on its own? "
                "0% turns an activity off. Changes save automatically."
            ),
            wraplength=self.ACTIVITY_SETTINGS_WIDTH - 40,
            justify="left",
            padx=12,
            pady=8,
            bg=_UI_BG,
        )
        header.pack(fill="x")

        body = Frame(outer, bg=_UI_BG, bd=2, relief=tk.SUNKEN)
        body.pack(fill="both", expand=True, padx=4, pady=(0, 4))

        canvas = tk.Canvas(body, bg=_UI_BG, highlightthickness=0)
        scrollbar = Scrollbar(body, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = Frame(canvas, bg=_UI_BG)
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
            weights = {
                entry_id: int(var.get())
                for entry_id, var in vars_by_id.items()
                if int(var.get()) != ACTIVITY_WEIGHT_DEFAULT
            }
            self._activity_weights = weights
            # Keep the Turn on/off flags in sync: a flag turns off only when
            # every activity sharing it sits at 0% (glitch/blue/ads share one).
            attrs_to_entries: dict[str, list[str]] = {}
            for entry_id, toggle_attr in ACTIVITY_TOGGLE_ATTRS.items():
                attrs_to_entries.setdefault(toggle_attr, []).append(entry_id)
            for toggle_attr, entry_ids in attrs_to_entries.items():
                any_on = any(
                    vars_by_id[e].get() > 0 for e in entry_ids if e in vars_by_id
                )
                setattr(self, toggle_attr, any_on)
            store = getattr(self, "_settings", None)
            if store is not None and hasattr(store, "set_activity_weights"):
                store.set_activity_weights(weights)
            if hasattr(self, "_persist_settings"):
                self._persist_settings()

        def _is_toggled_off(entry_id: str) -> bool:
            toggle_attr = ACTIVITY_TOGGLE_ATTRS.get(entry_id)
            return toggle_attr is not None and not getattr(self, toggle_attr, True)

        def _build_row(parent, entry_id, label, *, toggled_off):
            row = Frame(parent, bg=_UI_BG)
            row.pack(fill="x", padx=8, pady=2)
            var = IntVar(value=int(stored.get(entry_id, ACTIVITY_WEIGHT_DEFAULT)))
            vars_by_id[entry_id] = var
            if toggled_off:
                label = f"{label} (off in Turn on/off)"
            name = Label(
                row,
                text=label,
                anchor="w",
                width=44,
                state="disabled" if toggled_off else "normal",
                bg=_UI_BG,
            )
            name.pack(side="left")
            value_label = Label(
                row,
                text=f"{var.get()}%",
                width=5,
                anchor="e",
                state="disabled" if toggled_off else "normal",
                bg=_UI_BG,
            )
            value_label.pack(side="right")

            def _on_change(_raw, v=var, vl=value_label):
                vl.configure(text=f"{v.get()}%")

            def _on_release(_event, v=var, vl=value_label):
                vl.configure(text=f"{v.get()}%")
                _persist_from_vars()

            slider = Scale(
                row,
                from_=0,
                to=100,
                orient="horizontal",
                variable=var,
                showvalue=False,
                length=140,
                command=_on_change,
                state="disabled" if toggled_off else "normal",
                bg=_UI_BG,
                highlightthickness=0,
                bd=0,
            )
            if not toggled_off:
                slider.bind("<ButtonRelease-1>", _on_release)
            slider.pack(side="right", fill="x", expand=True, padx=8)

        disabled_entries: list[ActivityEntry] = []
        for section_title, entries in ACTIVITY_SECTIONS:
            active = [e for e in entries if not _is_toggled_off(e[0])]
            disabled_entries.extend(e for e in entries if _is_toggled_off(e[0]))
            if not active:
                continue
            section_label = Label(
                inner,
                text=section_title,
                font=("Segoe UI", 11, "bold"),
                anchor="w",
                pady=6,
                bg=_UI_BG,
            )
            section_label.pack(fill="x", padx=8)
            for entry_id, label in active:
                _build_row(inner, entry_id, label, toggled_off=False)

        if disabled_entries:
            disabled_header = Label(
                inner,
                text="▸ Turned off in Turn on/off",
                font=("Segoe UI", 11, "bold"),
                anchor="w",
                pady=6,
                cursor="hand2",
                bg=_UI_BG,
            )
            disabled_header.pack(fill="x", padx=8, pady=(12, 0))
            disabled_body = Frame(inner, bg=_UI_BG)

            def _toggle_disabled(_event=None):
                if disabled_body.winfo_ismapped():
                    disabled_body.pack_forget()
                    disabled_header.configure(text="▸ Turned off in Turn on/off")
                else:
                    disabled_body.pack(fill="x")
                    disabled_header.configure(text="▾ Turned off in Turn on/off")

            disabled_header.bind("<Button-1>", _toggle_disabled)
            for entry_id, label in disabled_entries:
                _build_row(disabled_body, entry_id, label, toggled_off=True)

        def _on_close():
            _persist_from_vars()
            try:
                canvas.unbind_all("<MouseWheel>")
            except tk.TclError:
                pass
            self._activity_settings_window = None
            try:
                window.destroy()
            except tk.TclError:
                pass

        footer = Frame(outer, bg=_UI_BG)
        footer.pack(fill="x", padx=12, pady=8)
        close_btn = tk.Button(footer, text="Close", command=_on_close)
        close_btn.pack(side="right")
        window.protocol("WM_DELETE_WINDOW", _on_close)
