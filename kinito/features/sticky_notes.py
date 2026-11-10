"""Sticky Notes: frameless colored note windows with JSON persistence."""

from __future__ import annotations

import json
import os
import random
import time
import tkinter as tk
import uuid
from datetime import datetime
from tkinter import Button, Frame, Label, Menu, Scrollbar, Toplevel, messagebox

from content import dialogue as dlg
from content import llm_prompts as prompts
from content import sticky_notes_lines
from kinito.assets import ensure_user_media_directories, sticky_notes_directory
from kinito.features.games.base import center_toplevel
from kinito.memory.store import _write_text_atomic

# Post-it palette: name -> (paper, darker fold/header shade).
NOTE_COLORS: dict[str, tuple[str, str]] = {
    "yellow": ("#fff36b", "#e6d24f"),
    "cyan": ("#6fd3d8", "#4fb3b9"),
    "blue": ("#7d9ce0", "#5f7ec4"),
    "green": ("#9fe04a", "#7fc22f"),
    "orange": ("#f5a83c", "#d98f22"),
    "pink": ("#f57db0", "#d95d97"),
    "purple": ("#c39bd8", "#a67bb8"),
}

NOTE_STYLES = ("plain", "folded", "tape")

NOTE_W = 220
NOTE_H = 200
_MARGIN = 4
_TAPE_TOP = 14  # transparent strip above the paper where the tape sticks out
_WIN_W = NOTE_W + _MARGIN * 2
_WIN_H = NOTE_H + _MARGIN + _TAPE_TOP
_COLLAPSED_H = _TAPE_TOP + 40  # tape + header + a sliver of paper
_HEADER_H = 36
_TAPE_W = 74
_TAPE_H = 16
_FOLD = 20
_AUTOSAVE_MS = 800
_MAX_TEXT = 2000
# Magic color punched out via -transparentcolor (real see-through corners).
_TRANSPARENT = "#ff00ff"
_TAPE_FILL = "#e6e6cc"
_TAPE_EDGE = "#b8b8a0"

_UI_BG = "#e6ded5"
_LIST_COLS = 3


def _note_path(note_id: str) -> str:
    return os.path.join(sticky_notes_directory, f"note_{note_id}.json")


def _sanitize_note_id(raw) -> str | None:
    if not isinstance(raw, str):
        return None
    cleaned = "".join(ch for ch in raw if ch.isalnum() or ch in {"-", "_"})
    return cleaned[:64] or None


def new_note_data(x: int | None = None, y: int | None = None) -> dict:
    """Return a fresh note dict with random color/style."""
    return {
        "id": uuid.uuid4().hex[:12],
        "title": "",
        "text": "",
        "color": random.choice(list(NOTE_COLORS)),
        "style": random.choice(NOTE_STYLES),
        "x": x,
        "y": y,
        "collapsed": False,
        "created": datetime.now().isoformat(timespec="seconds"),
        "updated": datetime.now().isoformat(timespec="seconds"),
    }


def load_notes() -> list[dict]:
    """Load all saved notes (newest first), skipping invalid files."""
    if not os.path.isdir(sticky_notes_directory):
        return []
    notes: list[dict] = []
    for name in sorted(os.listdir(sticky_notes_directory)):
        if not (name.startswith("note_") and name.endswith(".json")):
            continue
        path = os.path.join(sticky_notes_directory, name)
        try:
            with open(path, encoding="utf-8") as handle:
                raw = json.load(handle)
        except (OSError, json.JSONDecodeError, TypeError):
            continue
        if not isinstance(raw, dict):
            continue
        note_id = _sanitize_note_id(raw.get("id"))
        if note_id is None:
            continue
        color = raw.get("color")
        style = raw.get("style")
        notes.append(
            {
                "id": note_id,
                "title": str(raw.get("title", ""))[:80],
                "text": str(raw.get("text", ""))[:_MAX_TEXT],
                "color": color if color in NOTE_COLORS else "yellow",
                "style": style if style in NOTE_STYLES else "plain",
                "x": raw.get("x") if isinstance(raw.get("x"), (int, float)) else None,
                "y": raw.get("y") if isinstance(raw.get("y"), (int, float)) else None,
                "collapsed": bool(raw.get("collapsed", False)),
                "created": str(raw.get("created", "")),
                "updated": str(raw.get("updated", "")),
            }
        )
    notes.sort(key=lambda n: n.get("updated", ""), reverse=True)
    return notes


def save_note(note: dict) -> bool:
    """Persist *note* to disk atomically. Returns True on success."""
    ensure_user_media_directories()
    note_id = _sanitize_note_id(note.get("id"))
    if note_id is None:
        return False
    note["id"] = note_id
    note["updated"] = datetime.now().isoformat(timespec="seconds")
    payload = json.dumps(note, ensure_ascii=False, indent=2)
    try:
        _write_text_atomic(_note_path(note_id), payload)
    except OSError:
        return False
    return True


def delete_note_file(note_id: str) -> bool:
    """Delete the JSON file for *note_id*. Returns True if removed."""
    safe = _sanitize_note_id(note_id)
    if safe is None:
        return False
    try:
        os.remove(_note_path(safe))
    except OSError:
        return False
    return True


class StickyNoteWindow:
    """A single frameless, draggable, editable sticky note."""

    def __init__(self, app, note: dict):
        self.app = app
        self.note = note
        self.window: Toplevel | None = None
        self._canvas: tk.Canvas | None = None
        self._text: tk.Text | None = None
        self._buttons: Frame | None = None
        self._title_entry: tk.Entry | None = None
        self._title_placeholder = False
        self._drag_offset: tuple[int, int] | None = None
        self._save_after = None
        self._menu: Menu | None = None
        self._collapsed = bool(note.get("collapsed", False))

    # -- construction -----------------------------------------------------

    def open(self) -> None:
        """Create the note window (must run on the UI thread)."""
        window = Toplevel(self.app.root)
        self.window = window
        window.overrideredirect(True)
        window.wm_attributes("-topmost", True)
        window.configure(bg=_TRANSPARENT)
        window.wm_attributes("-transparentcolor", _TRANSPARENT)

        self._canvas = tk.Canvas(
            window, bg=_TRANSPARENT, highlightthickness=0, bd=0
        )
        self._canvas.pack(fill=tk.BOTH, expand=True)
        self._canvas.bind("<Button-3>", self._show_menu)

        self._build()

        x, y = self._initial_position()
        height = _COLLAPSED_H if self._collapsed else _WIN_H
        window.geometry(f"{_WIN_W}x{height}+{x}+{y}")
        window.protocol("WM_DELETE_WINDOW", self.hide_to_list)
        self.app._register_sticky_note_window(self)

    def _initial_position(self) -> tuple[int, int]:
        x, y = self.note.get("x"), self.note.get("y")
        if isinstance(x, int) and isinstance(y, int):
            return x, y
        # Near Kinito, nudged so the note doesn't cover him.
        try:
            kx, ky = self.app.root.winfo_x(), self.app.root.winfo_y()
        except tk.TclError:
            kx, ky = 200, 200
        screen_w = self.app.root.winfo_screenwidth()
        screen_h = self.app.root.winfo_screenheight()
        x = max(0, min(kx + 120, screen_w - _WIN_W))
        y = max(0, min(ky - 40, screen_h - _WIN_H))
        self.note["x"], self.note["y"] = x, y
        return x, y

    def _colors(self) -> tuple[str, str]:
        return NOTE_COLORS.get(self.note.get("color"), NOTE_COLORS["yellow"])

    def _build(self) -> None:
        """(Re)draw the note: paper, header, tape/fold decorations, text."""
        assert self._canvas is not None
        canvas = self._canvas
        canvas.delete("all")
        paper, dark = self._colors()
        style = self.note.get("style")

        x0, y0 = _MARGIN, _TAPE_TOP
        x1, y1 = _MARGIN + NOTE_W, _TAPE_TOP + NOTE_H

        # Paper body.
        canvas.create_rectangle(
            x0, y0, x1, y1, fill=paper, outline=dark, tags="drag"
        )
        # Header strip.
        canvas.create_rectangle(
            x0, y0, x1, y0 + _HEADER_H, fill=dark, outline=dark, tags="drag"
        )
        # Editable note title in the header.
        if self._title_entry is None:
            self._title_entry = tk.Entry(
                canvas,
                fg="#1a1a1a",
                insertbackground="#1a1a1a",
                font=("Segoe UI", 8, "bold"),
                bd=0,
                highlightthickness=0,
            )
            self._title_entry.insert(0, self.note.get("title", ""))
            self._title_entry.bind("<KeyRelease>", self._on_title_key)
            self._title_entry.bind("<FocusIn>", self._on_title_focus_in)
            self._title_entry.bind("<FocusOut>", self._on_title_focus_out)
            self._title_entry.bind("<Button-3>", self._show_menu)
        self._title_entry.configure(bg=dark)
        canvas.create_window(
            x0 + 6,
            y0 + _TAPE_H,
            anchor="nw",
            window=self._title_entry,
            width=NOTE_W - 110,
            height=_HEADER_H - _TAPE_H - 2,
        )
        self._sync_title_placeholder()

        canvas.tag_bind("drag", "<ButtonPress-1>", self._on_drag_start)
        canvas.tag_bind("drag", "<B1-Motion>", self._on_drag_move)
        canvas.tag_bind("drag", "<ButtonRelease-1>", self._on_drag_end)
        canvas.tag_bind("drag", "<Button-3>", self._show_menu)
        canvas.tag_bind("drag", "<Double-Button-1>", lambda _e: self.toggle_collapse())

        # Header buttons.
        if self._buttons is None:
            self._buttons = Frame(canvas, bg=dark)
            btn_font = ("TkDefaultFont", 7, "bold")
            for label, command in (
                ("✕", self.hide_to_list),
                ("−", self.toggle_collapse),
                ("☰", self._show_menu_button),
            ):
                btn = Label(
                    self._buttons,
                    text=label,
                    bg=dark,
                    fg="black",
                    font=btn_font,
                    padx=4,
                )
                btn.pack(side=tk.RIGHT)
                btn.bind("<Button-1>", lambda _e, c=command: c())
                btn.bind("<Button-3>", self._show_menu)
        else:
            self._buttons.configure(bg=dark)
            for child in self._buttons.winfo_children():
                child.configure(bg=dark)
        canvas.create_window(
            x1 - 2, y0 + 1, anchor="ne", window=self._buttons, height=_HEADER_H - 2
        )

        # Editable text embedded in the canvas.
        text_bottom_pad = (_FOLD + 4) if style == "folded" else 8
        if self._text is None:
            self._text = tk.Text(
                canvas,
                fg="#1a1a1a",
                insertbackground="#1a1a1a",
                font=("Segoe UI", 10),
                wrap=tk.WORD,
                bd=0,
                highlightthickness=0,
                padx=8,
                pady=6,
                undo=True,
            )
            self._text.insert("1.0", self.note.get("text", ""))
            self._text.bind("<<Modified>>", self._on_modified)
            self._text.bind("<Button-3>", self._show_menu)
        self._text.configure(bg=paper)
        canvas.create_window(
            x0 + 2,
            y0 + _HEADER_H,
            anchor="nw",
            window=self._text,
            width=NOTE_W - 4,
            height=NOTE_H - _HEADER_H - text_bottom_pad,
        )

        if style == "folded":
            self._draw_folded_corner(canvas, x1, y1, paper, dark)
        elif style == "tape":
            self._draw_tape(canvas, x0, y0, x1)

    def _draw_folded_corner(
        self, canvas: tk.Canvas, x1: int, y1: int, paper: str, dark: str
    ) -> None:
        """Cut the bottom-right corner transparently and draw the flap."""
        fx, fy = x1, y1
        # Hole: lower-right triangle becomes truly transparent.
        canvas.create_polygon(
            fx, fy,
            fx - _FOLD, fy,
            fx, fy - _FOLD,
            fill=_TRANSPARENT, outline=_TRANSPARENT,
        )
        # Flap: upper-left triangle = visible folded paper backside.
        canvas.create_polygon(
            fx - _FOLD, fy,
            fx - _FOLD, fy - _FOLD,
            fx, fy - _FOLD,
            fill="#ffffff", outline=dark,
        )
        # Re-draw the left/bottom paper edges around the notch.
        canvas.create_line(
            fx - _FOLD, fy, fx - _FOLD, fy - _FOLD, fx, fy - _FOLD,
            fill=dark,
        )

    def _draw_tape(self, canvas: tk.Canvas, x0: int, y0: int, x1: int) -> None:
        """Draw a skewed translucent-looking tape strip over the top edge."""
        cx = (x0 + x1) // 2
        half = _TAPE_W // 2
        skew = 6
        top = 2
        bottom = y0 + _TAPE_H
        canvas.create_polygon(
            cx - half, top,
            cx + half, top,
            cx + half - skew, bottom,
            cx - half - skew, bottom,
            fill=_TAPE_FILL,
            outline=_TAPE_EDGE,
            stipple="gray50",
            tags="drag",
        )

    # -- context menu -----------------------------------------------------

    def _build_menu(self) -> Menu:
        menu = Menu(self.window, tearoff=0)
        color_menu = Menu(menu, tearoff=0)
        for name in NOTE_COLORS:
            paper, _dark = NOTE_COLORS[name]
            color_menu.add_command(
                label=name.capitalize(),
                background=paper,
                command=lambda n=name: self.set_color(n),
            )
        menu.add_cascade(label="Color", menu=color_menu)

        style_menu = Menu(menu, tearoff=0)
        for style in NOTE_STYLES:
            style_menu.add_command(
                label=style.capitalize(),
                command=lambda s=style: self.set_style(s),
            )
        menu.add_cascade(label="Style", menu=style_menu)
        return menu

    def _show_menu(self, event) -> None:
        if self._menu is None:
            self._menu = self._build_menu()
        self._menu.tk_popup(event.x_root, event.y_root)

    def _show_menu_button(self) -> None:
        if self._menu is None:
            self._menu = self._build_menu()
        x = self.window.winfo_rootx() + _WIN_W - 30
        y = self.window.winfo_rooty() + _TAPE_TOP + _HEADER_H + 4
        self._menu.tk_popup(x, y)

    # -- appearance -------------------------------------------------------

    def set_color(self, name: str) -> None:
        if name not in NOTE_COLORS:
            return
        self.note["color"] = name
        self._build()
        self._schedule_save()

    def set_style(self, style: str) -> None:
        if style not in NOTE_STYLES or style == self.note.get("style"):
            return
        self.note["style"] = style
        self._build()
        self._schedule_save()

    # -- title editing ----------------------------------------------------

    def _sync_title_placeholder(self) -> None:
        if self._title_entry is None:
            return
        if self.note.get("title") or self._title_entry.get() not in ("", "untitled note"):
            return
        if self._title_entry.focus_get() is self._title_entry:
            return
        self._title_placeholder = True
        self._title_entry.delete(0, tk.END)
        self._title_entry.insert(0, "untitled note")
        self._title_entry.configure(fg="#555555")

    def _on_title_focus_in(self, _event=None) -> None:
        if self._title_placeholder and self._title_entry is not None:
            self._title_placeholder = False
            self._title_entry.delete(0, tk.END)
            self._title_entry.configure(fg="#1a1a1a")

    def _on_title_focus_out(self, _event=None) -> None:
        self._sync_title_placeholder()

    def _on_title_key(self, _event=None) -> None:
        if self._title_entry is None or self._title_placeholder:
            return
        self.note["title"] = self._title_entry.get()[:80]
        self._schedule_save()

    # -- dragging ---------------------------------------------------------

    def _on_drag_start(self, event) -> None:
        self._drag_offset = (event.x_root - self.window.winfo_x(),
                           event.y_root - self.window.winfo_y())

    def _on_drag_move(self, event) -> None:
        if self._drag_offset is None:
            return
        dx, dy = self._drag_offset
        x, y = event.x_root - dx, event.y_root - dy
        try:
            self.window.geometry(f"+{x}+{y}")
        except tk.TclError:
            pass

    def _on_drag_end(self, _event) -> None:
        self._drag_offset = None
        try:
            self.note["x"] = self.window.winfo_x()
            self.note["y"] = self.window.winfo_y()
        except tk.TclError:
            return
        self._schedule_save()

    # -- persistence ------------------------------------------------------

    def _on_modified(self, _event=None) -> None:
        if self._text is None or not self._text.edit_modified():
            return
        self._text.edit_modified(False)
        self._schedule_save()

    def _schedule_save(self) -> None:
        if self.window is None:
            return
        if self._save_after is not None:
            try:
                self.window.after_cancel(self._save_after)
            except (tk.TclError, ValueError):
                pass
        self._save_after = self.window.after(_AUTOSAVE_MS, self.save)

    def save(self) -> None:
        self._save_after = None
        if self._text is not None:
            try:
                self.note["text"] = self._text.get("1.0", "end-1c")[:_MAX_TEXT]
            except tk.TclError:
                pass
        # Empty notes (no title, no text) are never persisted.
        if not (self.note.get("text") or "").strip() and not (
            self.note.get("title") or ""
        ).strip():
            delete_note_file(self.note["id"])
            refresh = getattr(self.app, "_refresh_sticky_notes_list", None)
            if callable(refresh):
                refresh()
            return
        if save_note(self.note):
            refresh = getattr(self.app, "_refresh_sticky_notes_list", None)
            if callable(refresh):
                refresh()

    # -- closing ----------------------------------------------------------

    def toggle_collapse(self) -> None:
        """Collapse the note to just its header strip, or expand it again."""
        if self.window is None:
            return
        self._collapsed = not self._collapsed
        self.note["collapsed"] = self._collapsed
        try:
            height = _COLLAPSED_H if self._collapsed else _WIN_H
            x, y = self.window.winfo_x(), self.window.winfo_y()
            self.window.geometry(f"{_WIN_W}x{height}+{x}+{y}")
        except tk.TclError:
            pass
        self._schedule_save()

    def hide_to_list(self) -> None:
        """Save and hide; the note stays reachable via My Notes."""
        self._teardown()
        self.app.speak_sticky_note_line(
            self.app._pick_sticky_note_line(
                sticky_notes_lines.STICKY_NOTE_HIDE_LINES, {}
            )
        )

    def hide(self) -> None:
        """Save and close the note window (same as hide_to_list)."""
        self.hide_to_list()

    def delete(self) -> None:
        if not messagebox.askyesno(
            "Delete note",
            "Delete this sticky note?",
            parent=self.window,
        ):
            return
        self._teardown(save=False)
        delete_note_file(self.note["id"])
        self.app.speak_sticky_note_line(
            self.app._pick_sticky_note_line(
                sticky_notes_lines.STICKY_NOTE_DELETE_LINES, {}
            )
        )

    def _teardown(self, save: bool = True) -> None:
        if save:
            self.save()
        self.app._unregister_sticky_note_window(self)
        try:
            self.window.destroy()
        except tk.TclError:
            pass
        self.window = None
        self._canvas = None
        self._text = None
        self._buttons = None
        self._title_entry = None
        self._title_placeholder = False


class StickyNotesMixin:
    """Actions menu entry points, note registry, list window, and recalls."""

    STICKY_NOTE_RECALL_CHANCE = 1 / 350
    STICKY_NOTE_RECALL_COOLDOWN_SECONDS = 900

    # -- registry ---------------------------------------------------------

    def _sticky_note_registry(self) -> dict[str, StickyNoteWindow]:
        registry = getattr(self, "_sticky_note_windows", None)
        if registry is None:
            registry = {}
            self._sticky_note_windows = registry
        return registry

    def _register_sticky_note_window(self, note_window: StickyNoteWindow) -> None:
        self._sticky_note_registry()[note_window.note["id"]] = note_window

    def _unregister_sticky_note_window(self, note_window: StickyNoteWindow) -> None:
        registry = self._sticky_note_registry()
        if registry.get(note_window.note["id"]) is note_window:
            del registry[note_window.note["id"]]

    def _close_all_sticky_notes(self) -> None:
        """Save and close all open notes quietly (used on shutdown)."""
        for note_window in list(self._sticky_note_registry().values()):
            note_window._teardown(save=True)
        existing = getattr(self, "_sticky_notes_list_window", None)
        if existing is not None:
            try:
                if existing.winfo_exists():
                    existing.destroy()
            except tk.TclError:
                pass
            self._sticky_notes_list_window = None

    # -- speech helpers ---------------------------------------------------

    def speak_sticky_note_line(self, line: str) -> None:
        """Speak a sticky-note commentary line."""
        self.speak(line, ai_hint=prompts.STICKY_NOTE_PROMPT)

    def _pick_sticky_note_line(self, pool, pool_by_mood) -> str:
        mood = self.get_mood() if hasattr(self, "get_mood") else None
        intensity = (
            self.get_mood_intensity() if hasattr(self, "get_mood_intensity") else 0.0
        )
        return sticky_notes_lines.pick_sticky_note_line(
            pool, pool_by_mood, mood, intensity
        )

    # -- menu entry points ------------------------------------------------

    def offer_sticky_notes_picker(self):
        """Speak the Sticky Notes submenu (New Note / My Notes)."""
        self.speak(dlg.STICKY_NOTES_PICKER_QUESTION, 45, True)

    def open_sticky_note(self, note_id: str | None = None) -> None:
        """Open a note window (new note when *note_id* is None)."""
        if note_id is not None:
            existing = self._sticky_note_registry().get(note_id)
            if existing is not None and existing.window is not None:
                try:
                    existing.window.deiconify()
                    existing.window.lift()
                    existing.window.focus_force()
                except tk.TclError:
                    pass
                return
        note = None
        if note_id is not None:
            for candidate in load_notes():
                if candidate["id"] == note_id:
                    note = candidate
                    break
            if note is None:
                self._show_sticky_notes_list()
                return
        else:
            note = new_note_data()
        self.root.after(
            0,
            lambda n=note: StickyNoteWindow(self, n).open(),
        )
        pool = (
            sticky_notes_lines.STICKY_NOTE_OPEN_LINES
            if note_id is not None
            else sticky_notes_lines.STICKY_NOTE_CREATE_LINES
        )
        mood_pool = (
            {}
            if note_id is not None
            else sticky_notes_lines.STICKY_NOTE_CREATE_BY_MOOD
        )
        self.speak_sticky_note_line(self._pick_sticky_note_line(pool, mood_pool))

    def open_sticky_notes_list(self) -> None:
        """Open the My Notes list, or speak an empty-list line."""
        notes = load_notes()
        if not notes:
            self.speak_sticky_note_line(
                self._pick_sticky_note_line(
                    sticky_notes_lines.STICKY_NOTE_LIST_EMPTY_LINES,
                    sticky_notes_lines.STICKY_NOTE_LIST_EMPTY_BY_MOOD,
                )
            )
            return
        self.speak_sticky_note_line(
            self._pick_sticky_note_line(
                sticky_notes_lines.STICKY_NOTE_LIST_OPEN_LINES,
                sticky_notes_lines.STICKY_NOTE_LIST_OPEN_BY_MOOD,
            )
        )
        self.root.after(0, lambda: self._show_sticky_notes_list(notes))

    # -- list window ------------------------------------------------------

    def _refresh_sticky_notes_list(self) -> None:
        """Rebuild the My Notes list if it is currently open."""
        if self._is_sticky_notes_list_open():
            self._show_sticky_notes_list()

    def _is_sticky_notes_list_open(self) -> bool:
        window = getattr(self, "_sticky_notes_list_window", None)
        if isinstance(window, Toplevel):
            try:
                if window.winfo_exists():
                    return True
            except tk.TclError:
                pass
            self._sticky_notes_list_window = None
        return False

    def _show_sticky_notes_list(self, notes: list[dict] | None = None) -> None:
        existing = getattr(self, "_sticky_notes_list_window", None)
        if existing is not None:
            try:
                if existing.winfo_exists():
                    self.root.unbind_all("<MouseWheel>")
                    existing.destroy()
            except tk.TclError:
                pass
            self._sticky_notes_list_window = None

        if notes is None:
            notes = load_notes()
        if not notes:
            self.speak_sticky_note_line(
                self._pick_sticky_note_line(
                    sticky_notes_lines.STICKY_NOTE_LIST_EMPTY_LINES,
                    sticky_notes_lines.STICKY_NOTE_LIST_EMPTY_BY_MOOD,
                )
            )
            return

        width, height = 460, 380
        window = Toplevel(self.root)
        self._sticky_notes_list_window = window
        window.title("My Notes")
        window.configure(bg=_UI_BG)
        center_toplevel(self, window, width, height)

        Label(window, text="Your sticky notes:", bg=_UI_BG, anchor="w").pack(
            fill=tk.X, padx=10, pady=(10, 4)
        )

        body = Frame(window, bg=_UI_BG)
        body.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        canvas = tk.Canvas(body, bg=_UI_BG, highlightthickness=0)
        scrollbar = Scrollbar(body, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        grid = Frame(canvas, bg=_UI_BG)
        inner_id = canvas.create_window((0, 0), window=grid, anchor="nw")
        grid.bind(
            "<Configure>",
            lambda _e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfigure(inner_id, width=e.width),
        )
        def _on_mousewheel(event):
            # Clamp so the list can't be scrolled above its top edge.
            if event.delta > 0 and canvas.yview()[0] <= 0:
                return
            canvas.yview_scroll(int(-event.delta / 120), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        open_ids = set(self._sticky_note_registry())

        def _trash_icon(parent, note_ref) -> tk.Canvas:
            """Small drawn trash-can icon; click deletes the note."""
            icon = tk.Canvas(
                parent, width=14, height=15, bg=paper, highlightthickness=0, bd=0
            )
            icon.create_rectangle(3, 4, 11, 14, fill="#3a3a3a", outline="")
            icon.create_rectangle(1, 2, 13, 4, fill="#3a3a3a", outline="")
            icon.create_rectangle(6, 0, 8, 2, fill="#3a3a3a", outline="")
            icon.create_line(5, 6, 5, 12, fill=paper)
            icon.create_line(9, 6, 9, 12, fill=paper)
            icon.bind(
                "<Button-1>",
                lambda _e, n=note_ref: self._delete_note_from_list(n, window),
            )
            return icon

        for index, note in enumerate(notes):
            row, col = divmod(index, _LIST_COLS)
            paper, dark = NOTE_COLORS[note["color"]]
            cell = Frame(
                grid,
                bg=paper,
                bd=1,
                relief=tk.RIDGE,
                padx=6,
                pady=6,
                cursor="hand2",
            )
            cell.grid(row=row, column=col, padx=6, pady=6, sticky="n")
            cell.bind(
                "<Button-1>",
                lambda _e, n=note["id"]: self.open_sticky_note(n),
            )

            def _open_on_click(_e, n=note["id"]):
                self.open_sticky_note(n)

            title = (note.get("title") or "").strip()
            if title:
                title_label = Label(
                    cell,
                    text=title,
                    bg=paper,
                    fg="#1a1a1a",
                    wraplength=110,
                    justify="left",
                    font=("Segoe UI", 8, "bold"),
                )
                title_label.pack(anchor="w")
                title_label.bind("<Button-1>", _open_on_click)
            snippet = (note.get("text") or "").strip().replace("\n", " ")
            if len(snippet) > 60:
                snippet = snippet[:57] + "..."
            if not snippet:
                snippet = "(empty note)"
            snippet_label = Label(
                cell,
                text=snippet,
                bg=paper,
                fg="#1a1a1a",
                wraplength=110,
                justify="left",
                font=("Segoe UI", 8),
            )
            snippet_label.pack()
            snippet_label.bind("<Button-1>", _open_on_click)

            meta = note.get("updated", "")[:10]
            suffix = " (open)" if note["id"] in open_ids else ""
            footer = Frame(cell, bg=paper)
            footer.pack(fill=tk.X, pady=(2, 0))
            trash = _trash_icon(footer, note)
            trash.pack(side=tk.LEFT)
            meta_label = Label(
                footer,
                text=meta + suffix,
                bg=paper,
                fg=dark,
                font=("TkDefaultFont", 6),
            )
            meta_label.pack(side=tk.LEFT, padx=(4, 0))
            meta_label.bind("<Button-1>", _open_on_click)
            footer.bind("<Button-1>", _open_on_click)

        Button(window, text="Close", command=window.destroy).pack(pady=(0, 10))

        def on_close():
            try:
                canvas.unbind_all("<MouseWheel>")
            except tk.TclError:
                pass
            self._sticky_notes_list_window = None
            try:
                window.destroy()
            except tk.TclError:
                pass

        window.protocol("WM_DELETE_WINDOW", on_close)

    def _delete_note_from_list(self, note: dict, list_window) -> None:
        snippet = (note.get("text") or "").strip().split("\n", 1)[0]
        if len(snippet) > 40:
            snippet = snippet[:37] + "..."
        label = f'"{snippet}"' if snippet else "this note"
        if not messagebox.askyesno(
            "Delete note", f"Delete {label}?", parent=list_window
        ):
            return
        open_window = self._sticky_note_registry().pop(note["id"], None)
        if open_window is not None:
            open_window._teardown(save=False)
        delete_note_file(note["id"])
        self.speak_sticky_note_line(
            self._pick_sticky_note_line(
                sticky_notes_lines.STICKY_NOTE_DELETE_LINES, {}
            )
        )
        self._show_sticky_notes_list()

    # -- spontaneous recalls ----------------------------------------------

    def maybe_trigger_sticky_notes_recall(self) -> bool:
        """Roll for a random saved-note popup with commentary."""
        if not getattr(self, "_sticky_notes_recall_enabled", True):
            return False
        if getattr(self, "_focus_mode", False):
            return False
        if getattr(self, "_is_game_active", lambda: False)():
            return False
        if (
            self.paused
            or getattr(self, "_is_position_locked_by_user", lambda: self.is_dragging)()
            or getattr(self, "_camera_active", False)
            or getattr(self, "_browser_active", False)
        ):
            return False
        if getattr(self, "_is_busy_with_speech", lambda: False)():
            return False
        if self._is_sticky_notes_list_open():
            return False
        notes = [n for n in load_notes() if n.get("text", "").strip()]
        if not notes:
            return False
        last_at = getattr(self, "_last_sticky_notes_recall_at", 0.0)
        if (
            last_at > 0
            and time.monotonic() - last_at < self.STICKY_NOTE_RECALL_COOLDOWN_SECONDS
        ):
            return False
        if random.random() >= self.STICKY_NOTE_RECALL_CHANCE:
            return False
        self._last_sticky_notes_recall_at = time.monotonic()
        note = random.choice(notes)
        self.root.after(
            0, lambda n=note: self._present_sticky_note_recall(n)
        )
        return True

    def _present_sticky_note_recall(self, note: dict) -> None:
        """Speak a comment and re-open the note on the desktop."""
        if getattr(self, "_is_busy_with_speech", lambda: False)():
            return
        existing = self._sticky_note_registry().get(note["id"])
        if existing is not None and existing.window is not None:
            try:
                if existing.window.winfo_exists():
                    existing.window.deiconify()
                    existing.window.lift()
                    return
            except tk.TclError:
                pass
        self.speak(
            self._pick_sticky_note_line(
                sticky_notes_lines.STICKY_NOTE_RECALL_LINES,
                sticky_notes_lines.STICKY_NOTE_RECALL_BY_MOOD,
            ),
            skip_ai=True,
        )
        StickyNoteWindow(self, note).open()

    def toggle_sticky_notes_recall(self):
        """Enable or disable spontaneous sticky-note popups."""
        self._sticky_notes_recall_enabled = not getattr(
            self, "_sticky_notes_recall_enabled", True
        )
        if hasattr(self, "_persist_settings"):
            self._persist_settings()
        lines = (
            dlg.STICKY_NOTES_RECALL_ON_LINES
            if self._sticky_notes_recall_enabled
            else dlg.STICKY_NOTES_RECALL_OFF_LINES
        )
        self.speak(dlg.pick_line(lines), skip_ai=True)
