"""User memory initialization and menu actions."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from content import dialogue as dlg
from content.memory_followups import FACT_UPDATE_PROMPTS
from content.memory_keys import ALLOWED_FACT_KEYS, MULTI_VALUE_FACT_KEYS, PROTECTED_FACT_KEYS
from kinito.memory.fact_values import is_placeholder_fact_answer, split_fact_values
from kinito.memory.questions import SAVE_AS_NOTE, MemoryQuestion, verify_fact_key
from kinito.memory.store import MemoryStore
from kinito.window_icon import apply_window_icon


class MemoryMixin:
    """Load persistent memory and expose remember/forget actions."""

    _MEMORY_EDITOR_WIDTH = 520
    _MEMORY_EDITOR_HEIGHT = 420
    _MEMORY_UI_BG = "#e6ded5"
    _MEMORY_TITLEBAR_BG = "#d4ccc2"
    _MEMORY_BTN_BG = "#d9d9d9"

    def _init_memory(self) -> None:
        """Create the on-disk memory store (call from app __init__)."""
        from content.friendship import ensure_first_met

        self._memory = MemoryStore()
        self._pending_memory_question: MemoryQuestion | None = None
        self._planning_memory_question = False
        self._chat_session_user_label: str | None = None
        self._memory_editor_window = None
        self._memory_editor_widgets: dict = {}
        ensure_first_met(self._memory)

    def show_memory_summary(self) -> None:
        """Open the memory editor (Settings → Memories compatibility alias)."""
        self.open_memory_editor()

    def open_memory_editor(self) -> None:
        """Show an editable window for facts and notes from memory.json."""
        existing = getattr(self, "_memory_editor_window", None)
        if existing is not None:
            try:
                if existing.winfo_exists():
                    self._reload_memory_editor_rows()
                    existing.lift()
                    existing.focus_force()
                    return
            except tk.TclError:
                self._memory_editor_window = None

        window = tk.Toplevel(self.root)
        self._memory_editor_window = window
        window.title("Kinito's Memories")
        apply_window_icon(window)
        window.wm_attributes("-topmost", True)
        window.configure(bg=self._MEMORY_UI_BG)
        window.geometry(f"{self._MEMORY_EDITOR_WIDTH}x{self._MEMORY_EDITOR_HEIGHT}")
        self._center_memory_editor(window)

        title = tk.Label(
            window,
            text="Memories",
            bg=self._MEMORY_UI_BG,
            fg="#111111",
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        )
        title.pack(fill="x", padx=12, pady=(10, 4))

        hint = tk.Label(
            window,
            text="Edit values, delete rows, then Save.",
            bg=self._MEMORY_UI_BG,
            fg="#444444",
            font=("Segoe UI", 9),
            anchor="w",
        )
        hint.pack(fill="x", padx=12, pady=(0, 6))

        canvas_frame = tk.Frame(window, bg=self._MEMORY_UI_BG)
        canvas_frame.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        canvas = tk.Canvas(canvas_frame, bg=self._MEMORY_UI_BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        rows_host = tk.Frame(canvas, bg=self._MEMORY_UI_BG)
        rows_host.bind(
            "<Configure>",
            lambda _event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas_window = canvas.create_window((0, 0), window=rows_host, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def _sync_scroll_width(event):
            canvas.itemconfigure(canvas_window, width=event.width)

        canvas.bind("<Configure>", _sync_scroll_width)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        buttons = tk.Frame(window, bg=self._MEMORY_UI_BG)
        buttons.pack(fill="x", padx=12, pady=(0, 12))
        save_btn = tk.Button(
            buttons,
            text="Save",
            command=self._save_memory_editor,
            relief=tk.RIDGE,
            bd=1,
            padx=12,
            pady=4,
            bg=self._MEMORY_BTN_BG,
            activebackground=self._MEMORY_BTN_BG,
        )
        close_btn = tk.Button(
            buttons,
            text="Close",
            command=self._close_memory_editor,
            relief=tk.RIDGE,
            bd=1,
            padx=12,
            pady=4,
            bg=self._MEMORY_BTN_BG,
            activebackground=self._MEMORY_BTN_BG,
        )
        save_btn.pack(side="right", padx=(6, 0))
        close_btn.pack(side="right")

        self._memory_editor_widgets = {
            "canvas": canvas,
            "rows_host": rows_host,
            "fact_rows": [],
            "note_rows": [],
        }
        window.protocol("WM_DELETE_WINDOW", self._close_memory_editor)
        self._reload_memory_editor_rows()

    def _center_memory_editor(self, window: tk.Toplevel) -> None:
        """Place the editor in the center of the primary monitor."""
        try:
            self.root.update_idletasks()
            x, y = self._centered_origin_on_primary(
                self._MEMORY_EDITOR_WIDTH,
                self._MEMORY_EDITOR_HEIGHT,
            )
        except (tk.TclError, AttributeError):
            return
        window.geometry(
            f"{self._MEMORY_EDITOR_WIDTH}x{self._MEMORY_EDITOR_HEIGHT}+{int(x)}+{int(y)}"
        )

    def _reload_memory_editor_rows(self) -> None:
        """Rebuild fact/note rows from the current memory store."""
        widgets = getattr(self, "_memory_editor_widgets", {})
        host = widgets.get("rows_host")
        if host is None:
            return
        for child in host.winfo_children():
            child.destroy()

        facts = self._memory.facts_dict()
        notes = self._memory.notes_list()
        fact_rows: list[dict] = []
        note_rows: list[dict] = []

        if not facts and not notes:
            tk.Label(
                host,
                text=dlg.MEMORY_EMPTY_LINE,
                bg=self._MEMORY_UI_BG,
                fg="#333333",
                font=("Segoe UI", 9),
                wraplength=self._MEMORY_EDITOR_WIDTH - 60,
                justify="left",
                anchor="w",
            ).pack(fill="x", pady=8)
            widgets["fact_rows"] = []
            widgets["note_rows"] = []
            return

        if facts:
            tk.Label(
                host,
                text="Facts",
                bg=self._MEMORY_UI_BG,
                fg="#111111",
                font=("Segoe UI", 10, "bold"),
                anchor="w",
            ).pack(fill="x", pady=(4, 4))
            for key, value in facts.items():
                row = self._build_memory_fact_row(host, key, value)
                fact_rows.append(row)

        if notes:
            tk.Label(
                host,
                text="Notes",
                bg=self._MEMORY_UI_BG,
                fg="#111111",
                font=("Segoe UI", 10, "bold"),
                anchor="w",
            ).pack(fill="x", pady=(12, 4))
            for note in notes:
                text = note.get("text") or ""
                row = self._build_memory_note_row(host, text)
                note_rows.append(row)

        widgets["fact_rows"] = fact_rows
        widgets["note_rows"] = note_rows

    def _build_memory_fact_row(self, parent: tk.Misc, key: str, value: str) -> dict:
        """Create one editable fact row and return widget handles."""
        frame = tk.Frame(parent, bg=self._MEMORY_UI_BG)
        frame.pack(fill="x", pady=2)
        label = tk.Label(
            frame,
            text=key.replace("_", " "),
            width=18,
            anchor="w",
            bg=self._MEMORY_UI_BG,
            font=("Segoe UI", 9),
        )
        label.pack(side="left", padx=(0, 6))
        entry = tk.Entry(frame, font=("Segoe UI", 9))
        entry.insert(0, value)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        row = {"key": key, "frame": frame, "entry": entry}

        def _delete():
            rows = self._memory_editor_widgets.get("fact_rows", [])
            if row in rows:
                rows.remove(row)
            try:
                frame.destroy()
            except tk.TclError:
                pass

        tk.Button(
            frame,
            text="Delete",
            command=_delete,
            relief=tk.RIDGE,
            bd=1,
            padx=6,
            bg=self._MEMORY_BTN_BG,
            activebackground=self._MEMORY_BTN_BG,
        ).pack(side="right")
        return row

    def _build_memory_note_row(self, parent: tk.Misc, text: str) -> dict:
        """Create one editable note row and return widget handles."""
        frame = tk.Frame(parent, bg=self._MEMORY_UI_BG)
        frame.pack(fill="x", pady=2)
        entry = tk.Entry(frame, font=("Segoe UI", 9))
        entry.insert(0, text)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        row = {"frame": frame, "entry": entry}

        def _delete():
            rows = self._memory_editor_widgets.get("note_rows", [])
            if row in rows:
                rows.remove(row)
            try:
                frame.destroy()
            except tk.TclError:
                pass

        tk.Button(
            frame,
            text="Delete",
            command=_delete,
            relief=tk.RIDGE,
            bd=1,
            padx=6,
            bg=self._MEMORY_BTN_BG,
            activebackground=self._MEMORY_BTN_BG,
        ).pack(side="right")
        return row

    def _save_memory_editor(self) -> None:
        """Persist edited facts/notes from the open editor window."""
        widgets = getattr(self, "_memory_editor_widgets", {})
        fact_rows = list(widgets.get("fact_rows") or [])
        note_rows = list(widgets.get("note_rows") or [])

        kept_keys: set[str] = set()
        for row in fact_rows:
            key = row.get("key")
            entry = row.get("entry")
            if not isinstance(key, str) or entry is None:
                continue
            try:
                value = entry.get().strip()
            except tk.TclError:
                continue
            if not value:
                self._memory.delete_fact(key)
                continue
            self._memory.set_fact(key, value)
            kept_keys.add(key)

        for key in list(self._memory.facts_dict()):
            if key not in kept_keys:
                self._memory.delete_fact(key)

        note_texts: list[str] = []
        for row in note_rows:
            entry = row.get("entry")
            if entry is None:
                continue
            try:
                text = entry.get().strip()
            except tk.TclError:
                continue
            if text:
                note_texts.append(text)
        self._memory.replace_notes(note_texts)

        self._reload_memory_editor_rows()
        self.speak(dlg.MEMORY_SAVED_LINE, skip_ai=True)

    def _close_memory_editor(self) -> None:
        """Destroy the memory editor window if open."""
        window = getattr(self, "_memory_editor_window", None)
        self._memory_editor_window = None
        self._memory_editor_widgets = {}
        if window is None:
            return
        try:
            window.destroy()
        except tk.TclError:
            pass

    def forget_memory(self) -> None:
        """Ask for confirmation, then clear all saved memory."""
        from content.friendship import ensure_first_met

        parent = getattr(self, "root", None)
        confirmed = messagebox.askyesno(
            dlg.MEMORY_FORGET_CONFIRM_TITLE,
            dlg.MEMORY_FORGET_CONFIRM_MESSAGE,
            parent=parent,
        )
        if not confirmed:
            return

        self._memory.reset()
        ensure_first_met(self._memory)
        self._pending_memory_question = None
        self._chat_session_user_label = None
        if getattr(self, "_memory_editor_window", None) is not None:
            self._close_memory_editor()
        self.speak(dlg.MEMORY_FORGOTTEN_LINE, skip_ai=True)

    def memory_prompt_block(self) -> str:
        """Return memory text for LLM chat prompts, or empty string."""
        return self._memory.as_prompt_block()

    def facts_prompt_block(self) -> str:
        """Return structured facts only (for idle / line replacement)."""
        return self._memory.as_facts_prompt_block()

    def chat_user_label(self) -> str:
        """Return the user chat label (stable for the open chat session)."""
        pinned = getattr(self, "_chat_session_user_label", None)
        if pinned:
            return pinned
        return self._memory.user_display_name()

    def chat_user_labels(self) -> list[str]:
        """Return all known user names for chat speaker styling."""
        names = self._memory.get_fact_values("user_names")
        if names:
            return names
        return [self.chat_user_label()]

    def _pin_chat_user_label(self) -> str:
        """Pick a user name for this chat session and keep it until chat closes."""
        label = self._memory.user_display_name()
        self._chat_session_user_label = label
        return label

    def _clear_chat_session_user_label(self) -> None:
        """Forget the pinned chat label so the next session can pick again."""
        self._chat_session_user_label = None

    def ask_memory_question(self, spec: MemoryQuestion) -> None:
        """Speak an interactive memory question with textbox or yes/no UI."""
        self._pending_memory_question = spec
        self.speak(spec.question, 45, True, skip_ai=True)

    def _handle_memory_question_response(self, response: str) -> None:
        """Persist the user's answer to a pending memory question."""
        spec = self._pending_memory_question
        self._pending_memory_question = None
        if spec is None:
            return

        answer = self._normalize_memory_answer(response, spec.ui)
        if not answer:
            return

        followup = self._persist_memory_answer(spec, answer)
        self._memory.mark_topic_asked(spec.topic)
        if followup is not None:
            self.ask_memory_question(followup)
            return
        self.speak(dlg.pick_line(dlg.MEMORY_ANSWER_ACK_LINES), skip_ai=True)

    @staticmethod
    def _normalize_memory_answer(response: str, ui: str) -> str:
        """Normalize a textbox or yes/no answer for storage."""
        if ui == "yes_no":
            if response == dlg.BUTTON_YES:
                return "yes"
            if response == dlg.BUTTON_NO:
                return "no"
            return ""
        return response.strip()

    def _persist_memory_answer(self, spec: MemoryQuestion, answer: str) -> MemoryQuestion | None:
        """Store a memory-question answer; may return a follow-up question."""
        fact_key = verify_fact_key(spec.save_as)
        if fact_key is not None:
            return self._persist_verification_answer(fact_key, answer, spec.context_value)

        if (
            spec.save_as != SAVE_AS_NOTE
            and spec.save_as in ALLOWED_FACT_KEYS
            and spec.save_as not in PROTECTED_FACT_KEYS
        ):
            self._apply_fact_update(spec.save_as, answer, topic=spec.topic)
            return None

        note = self._compact_memory_note(spec, answer)
        self._memory.add_note(note, source="question")
        return None

    def _apply_fact_update(self, fact_key: str, answer: str, *, topic: str) -> None:
        """Write an updated fact without wiping multi-value lists on partial answers."""
        if is_placeholder_fact_answer(answer) and not fact_key.startswith("likes_"):
            # Decline / "none" after verify: keep remaining values as-is.
            return

        if fact_key in MULTI_VALUE_FACT_KEYS:
            values = split_fact_values(answer)
            if not values:
                return
            # Updates after verify append instead of replace, so answering
            # "Crochet" does not erase Drawing/Reading.
            if topic.startswith("update_"):
                self._memory.merge_fact_values(fact_key, values)
            else:
                self._memory.set_fact(fact_key, answer)
            return

        self._memory.set_fact(fact_key, answer)

    def _persist_verification_answer(
        self,
        fact_key: str,
        answer: str,
        context_value: str | None = None,
    ) -> MemoryQuestion | None:
        """Handle yes/no confirmation of an existing fact; update instead of delete."""
        if answer == "yes":
            # Re-set the same value so the fact stays current without changing it.
            values = self._memory.get_fact_values(fact_key)
            if values:
                if fact_key in MULTI_VALUE_FACT_KEYS:
                    self._memory.replace_fact_values(fact_key, values)
                else:
                    self._memory.set_fact(fact_key, values[0])
            return None

        if answer != "no":
            return None

        # Boolean preference facts: flip to "no" in place (never delete the key).
        if fact_key.startswith("likes_"):
            self._memory.set_fact(fact_key, "no")
            return None

        if fact_key not in ALLOWED_FACT_KEYS or fact_key in PROTECTED_FACT_KEYS:
            return None

        # Multi-value verify asks about one item — drop only that item.
        if fact_key in MULTI_VALUE_FACT_KEYS and context_value:
            self._memory.remove_fact_value(fact_key, context_value)

        prompt = FACT_UPDATE_PROMPTS.get(
            fact_key,
            f"Got it! What should I remember instead for {fact_key.replace('_', ' ')}?",
        )
        return MemoryQuestion(
            question=prompt,
            ui="textbox",
            topic=f"update_{fact_key}",
            save_as=fact_key,
            context_value=context_value,
        )

    @staticmethod
    def _compact_memory_note(spec: MemoryQuestion, answer: str) -> str:
        """Build a short note summarizing the Q&A pair."""
        question = spec.question.strip()
        if len(question) > 60:
            question = f"{question[:57]}..."
        return f"{spec.topic}: {answer} ({question})"
