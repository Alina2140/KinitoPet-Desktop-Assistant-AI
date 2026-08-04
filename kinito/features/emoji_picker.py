"""Pixel-art emoji picker for the chat input row (Kuteken spritesheet)."""

from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path

from PIL import Image, ImageTk

from kinito.assets import emoji_catalog_path, emoji_sheet_path

DISPLAY_SIZE = 28
BUTTON_ICON_SIZE = 18
PICKER_COLS = 11
PICKER_BG = "#FFF8E7"
PICKER_BORDER = "#000000"
PICKER_HEIGHT = 132
TILE_PAD = 1
MIN_TILE_CONTENT = 20
_VARIATION_SELECTOR = "\ufe0f"


def normalize_emoji_char(char: str) -> str:
    """Return *char* unchanged (kept for API stability / catalog loading)."""
    if not char:
        return char
    return char


def _utf16_len(text: str) -> int:
    """Return the number of UTF-16 code units in *text* (Tk Entry index units)."""
    return len(text.encode("utf-16-le")) // 2


def _tk_index_to_py(text: str, tk_index: int) -> int:
    """Convert a Tk Entry UTF-16 index into a Python code-point index."""
    if tk_index <= 0:
        return 0
    units = 0
    for i, ch in enumerate(text):
        if units >= tk_index:
            return i
        units += 1 if ord(ch) < 0x10000 else 2
    return len(text)


def _py_index_to_tk(text: str, py_index: int) -> int:
    """Convert a Python code-point index into a Tk Entry UTF-16 index."""
    py_index = max(0, min(py_index, len(text)))
    return _utf16_len(text[:py_index])


def load_emoji_catalog(
    catalog_path: str | Path | None = None,
) -> list[dict]:
    """Load catalog entries ``{x, y, w, h, char}`` from JSON."""
    path = Path(catalog_path or emoji_catalog_path)
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(data, list):
        return []
    entries: list[dict] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        try:
            x, y, w, h = int(item["x"]), int(item["y"]), int(item["w"]), int(item["h"])
            char = str(item["char"])
        except (KeyError, TypeError, ValueError):
            continue
        if not char or w <= 0 or h <= 0:
            continue
        entries.append({"x": x, "y": y, "w": w, "h": h, "char": char})
    return entries


def _content_bbox(tile: Image.Image) -> tuple[int, int, int, int] | None:
    """Return tight non-transparent / non-black bbox inside *tile*, or None."""
    pixels = tile.load()
    width, height = tile.size
    xs: list[int] = []
    ys: list[int] = []
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue
            if r < 8 and g < 8 and b < 8:
                continue
            xs.append(x)
            ys.append(y)
    if not xs:
        return None
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def crop_emoji_tile(
    sheet: Image.Image,
    entry: dict,
    *,
    display_size: int = DISPLAY_SIZE,
) -> Image.Image | None:
    """Crop, trim neighbor pixels, square-pad, and nearest-scale one tile."""
    try:
        x, y, w, h = entry["x"], entry["y"], entry["w"], entry["h"]
        box = (x, y, x + w, y + h)
        if box[2] > sheet.width or box[3] > sheet.height or box[0] < 0 or box[1] < 0:
            return None
        region = sheet.crop(box)
        bbox = _content_bbox(region)
        if bbox is None:
            return None
        trimmed = region.crop(bbox)
        tw, th = trimmed.size
        if tw * th < MIN_TILE_CONTENT:
            return None
        side = max(tw, th, 16)
        canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        canvas.paste(trimmed, ((side - tw) // 2, (side - th) // 2), trimmed)
        if display_size != side:
            canvas = canvas.resize((display_size, display_size), Image.Resampling.NEAREST)
        return canvas
    except (KeyError, TypeError, ValueError, OSError):
        return None


def load_emoji_button_icon(
    *,
    display_size: int = BUTTON_ICON_SIZE,
) -> ImageTk.PhotoImage | None:
    """Return a PhotoImage of the first catalog smile for the trigger button."""
    catalog = load_emoji_catalog()
    sheet_path = Path(emoji_sheet_path)
    if not catalog or not sheet_path.is_file():
        return None
    try:
        sheet = Image.open(sheet_path).convert("RGBA")
    except OSError:
        return None
    tile = crop_emoji_tile(sheet, catalog[0], display_size=display_size)
    if tile is None:
        return None
    return ImageTk.PhotoImage(tile)


def insert_emoji_into_entry(entry: tk.Entry, char: str) -> None:
    """Insert *char* at the Entry cursor."""
    if entry is None or not char:
        return
    try:
        if not entry.winfo_exists():
            return
    except tk.TclError:
        return
    try:
        entry.insert(tk.INSERT, char)
    except tk.TclError:
        return


def delete_char_before_cursor(entry: tk.Entry) -> str | None:
    """Delete one Unicode code point before the cursor (Tk uses UTF-16 indices)."""
    if entry is None:
        return None
    try:
        if not entry.winfo_exists():
            return None
        if entry.selection_present():
            return None
        text = entry.get()
        tk_pos = int(entry.index(tk.INSERT))
        py_pos = _tk_index_to_py(text, tk_pos)
        if py_pos <= 0:
            return "break"
        end_py = py_pos
        start_py = py_pos - 1
        # ❤︎ + VS16 must go together, otherwise a tofu square remains.
        if text[start_py] == _VARIATION_SELECTOR and start_py > 0:
            start_py -= 1
        entry.delete(_py_index_to_tk(text, start_py), _py_index_to_tk(text, end_py))
        return "break"
    except (tk.TclError, ValueError, IndexError):
        return None


class EmojiPickerMixin:
    """Toggle an in-bubble scrollable emoji dropdown under the chat input."""

    def _init_emoji_picker_state(self) -> None:
        self._emoji_picker_frame: tk.Frame | None = None
        self._emoji_picker_photos: list[ImageTk.PhotoImage] = []
        self._emoji_picker_button = None
        self._emoji_button_photo: ImageTk.PhotoImage | None = None
        self._emoji_dropdown_parent = None
        self._emoji_sheet_cache: Image.Image | None = None

    def _toggle_emoji_picker(self) -> None:
        """Open or close the emoji dropdown."""
        if not getattr(self, "_emoji_picker_enabled", True):
            return
        if self._emoji_picker_is_open():
            self._close_emoji_picker()
            return
        self._open_emoji_picker()

    def toggle_emoji_picker_setting(self) -> None:
        """Enable or disable the chat emoji button (persisted in settings)."""
        from content import dialogue as dlg

        self._emoji_picker_enabled = not getattr(self, "_emoji_picker_enabled", True)
        if not self._emoji_picker_enabled:
            self._close_emoji_picker()
        if hasattr(self, "_persist_settings"):
            self._persist_settings()
        lines = (
            dlg.EMOJI_PICKER_ON_LINES
            if self._emoji_picker_enabled
            else dlg.EMOJI_PICKER_OFF_LINES
        )
        self.speak(dlg.pick_line(lines), skip_ai=True)

    def _emoji_picker_is_open(self) -> bool:
        frame = getattr(self, "_emoji_picker_frame", None)
        if frame is None:
            return False
        try:
            return bool(frame.winfo_exists()) and bool(frame.winfo_ismapped())
        except tk.TclError:
            return False

    def _refit_bubble_after_picker(self) -> None:
        """Recompute bubble chrome after the dropdown opens or closes."""
        parent = getattr(self, "_emoji_dropdown_parent", None)
        if parent is not None:
            try:
                parent.update_idletasks()
            except tk.TclError:
                pass
        if hasattr(self, "_fit_speech_bubble_to_content"):
            try:
                self._fit_speech_bubble_to_content()
                self._schedule_speech_bubble_position()
            except Exception:
                pass

    def _close_emoji_picker(self) -> None:
        frame = getattr(self, "_emoji_picker_frame", None)
        self._emoji_picker_frame = None
        self._emoji_picker_photos = []
        if frame is not None:
            try:
                if frame.winfo_exists():
                    frame.destroy()
            except tk.TclError:
                pass
        self._refit_bubble_after_picker()

    def _open_emoji_picker(self) -> None:
        entry = getattr(self, "_chat_entry_widget", None)
        parent = getattr(self, "_emoji_dropdown_parent", None)
        if entry is None or parent is None:
            return
        try:
            if not entry.winfo_exists() or not parent.winfo_exists():
                return
        except tk.TclError:
            return

        catalog = load_emoji_catalog()
        sheet_path = Path(emoji_sheet_path)
        if not catalog or not sheet_path.is_file():
            return

        try:
            sheet = Image.open(sheet_path).convert("RGBA")
        except OSError:
            return
        self._emoji_sheet_cache = sheet

        self._close_emoji_picker()

        frame = tk.Frame(
            parent,
            bg=PICKER_BG,
            highlightbackground=PICKER_BORDER,
            highlightthickness=1,
        )
        frame.pack(fill=tk.X, padx=5, pady=(0, 5), after=getattr(self, "_speech_bubble_button_frame", None))

        canvas = tk.Canvas(
            frame,
            bg=PICKER_BG,
            highlightthickness=0,
            borderwidth=0,
            height=PICKER_HEIGHT,
        )
        scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        grid = tk.Frame(canvas, bg=PICKER_BG)
        window_id = canvas.create_window((0, 0), window=grid, anchor="nw")

        photos: list[ImageTk.PhotoImage] = []

        def _on_mousewheel(event) -> None:
            delta = 0
            if getattr(event, "delta", 0):
                delta = -1 if event.delta > 0 else 1
            elif getattr(event, "num", None) == 4:
                delta = -1
            elif getattr(event, "num", None) == 5:
                delta = 1
            if delta:
                canvas.yview_scroll(delta, "units")

        for item in catalog:
            tile = crop_emoji_tile(sheet, item)
            if tile is None:
                continue
            photo = ImageTk.PhotoImage(tile)
            photos.append(photo)
            row, col = divmod(len(photos) - 1, PICKER_COLS)
            btn = tk.Label(
                grid,
                image=photo,
                bg=PICKER_BG,
                cursor="hand2",
                borderwidth=0,
                padx=TILE_PAD,
                pady=TILE_PAD,
            )
            btn.image = photo  # type: ignore[attr-defined]
            btn.grid(row=row, column=col, padx=1, pady=1)
            btn.bind("<Button-1>", lambda _e, ch=item["char"]: self._on_emoji_picked(ch))
            btn.bind("<Enter>", lambda _e, b=btn: b.configure(bg="#FFE9A8"))
            btn.bind("<Leave>", lambda _e, b=btn: b.configure(bg=PICKER_BG))
            btn.bind("<MouseWheel>", _on_mousewheel)
            btn.bind("<Button-4>", _on_mousewheel)
            btn.bind("<Button-5>", _on_mousewheel)

        self._emoji_picker_photos = photos
        self._emoji_picker_frame = frame

        def _sync_scroll(_event=None) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas_width = canvas.winfo_width()
            if canvas_width > 1:
                canvas.itemconfigure(window_id, width=canvas_width)

        grid.bind("<Configure>", _sync_scroll)
        canvas.bind("<Configure>", _sync_scroll)

        for widget in (canvas, grid, frame):
            widget.bind("<MouseWheel>", _on_mousewheel)
            widget.bind("<Button-4>", _on_mousewheel)
            widget.bind("<Button-5>", _on_mousewheel)

        frame.bind("<Escape>", lambda _e: self._close_emoji_picker())

        self._refit_bubble_after_picker()

    def _on_emoji_picked(self, char: str) -> None:
        entry = getattr(self, "_chat_entry_widget", None)
        insert_emoji_into_entry(entry, char)
        self._close_emoji_picker()
        if entry is not None:
            try:
                if entry.winfo_exists():
                    entry.focus_set()
            except tk.TclError:
                pass

    def _on_chat_entry_backspace(self, event=None):
        """Delete a full emoji code point (and FE0F) with one Backspace."""
        entry = getattr(self, "_chat_entry_widget", None) or (event.widget if event else None)
        result = delete_char_before_cursor(entry)
        return result
