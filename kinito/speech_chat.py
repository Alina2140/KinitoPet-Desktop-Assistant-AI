"""Extended speech bubble for multi-turn Ollama chat."""

from __future__ import annotations

import threading
import tkinter as tk

from content import llm_prompts as prompts
from kinito.assets import starttalk_file_path


class SpeechChatMixin:
    """Chat-mode speech bubble with scrollable history and persistent input."""

    CHAT_TITLE = "Kinito Chat"
    CHAT_LOG_HEIGHT_PX = 120
    CHAT_LOG_WIDTH_PX = 360

    def _init_chat_state(self) -> None:
        """Initialize chat-related instance attributes (call from app __init__)."""
        self._chat_mode = False
        self._chat_generating = False
        self._chat_log_widget = None
        self._chat_entry_widget = None

    def open_chat_bubble(self, greeting: str) -> None:
        """Open a persistent chat bubble with an initial assistant greeting."""
        self.interrupt_speech()
        self._chat_mode = True
        self._chat_generating = False
        self._cancel_bubble_close_timer()

        if self._has_active_speech_bubble():
            self._close_speech_bubble_impl()

        self.play_sfx(starttalk_file_path)
        self.speech_bubble = self._new_speech_bubble_toplevel(self.CHAT_TITLE)
        self._speech_bubble_label = None
        self._speech_bubble_text_frame = None
        self._speech_bubble_button_frame = None
        self._chat_log_widget = None
        self._chat_entry_widget = None

        container = tk.Frame(self.speech_bubble, bg=self.BUBBLE_BG)
        container.pack(fill=tk.BOTH, expand=True, anchor="w")

        log_frame = tk.Frame(container, bg=self.BUBBLE_BG)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(5, 0), anchor="w")

        log = tk.Text(
            log_frame,
            height=6,
            width=48,
            wrap=tk.WORD,
            bg=self.BUBBLE_BG,
            fg="black",
            relief=tk.FLAT,
            state=tk.DISABLED,
            cursor="arrow",
        )
        log.pack(fill=tk.BOTH, expand=True)
        self._chat_log_widget = log

        self._show_chat_input_row(container)
        self.append_chat_message(prompts.CHAT_ASSISTANT_LABEL, greeting)

        self._awaiting_response = True
        self._fit_speech_bubble_to_content()
        self._schedule_speech_bubble_position()

    def _show_chat_input_row(self, parent) -> None:
        """Add the persistent chat entry row below the log."""
        input_frame = tk.Frame(parent, bg=self.BUBBLE_BG)
        input_frame.pack(fill=tk.X, padx=5, pady=5, anchor="w")
        self._speech_bubble_button_frame = input_frame

        entry_width = self.get_entry_char_width("Type your message here...")
        entry = tk.Entry(input_frame, bg=self.BUBBLE_BG, fg="black", width=entry_width)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=2)
        entry.bind("<Return>", self._handle_chat_entry_submit)
        self._chat_entry_widget = entry

        close_button = tk.Button(
            input_frame,
            text="×",
            width=2,
            command=self.close_chat_mode,
        )
        close_button.pack(side=tk.LEFT, padx=(5, 0))
        entry.focus_set()

    def _handle_chat_entry_submit(self, event=None):
        """Submit the chat entry to the LLM handler."""
        if not getattr(self, "_chat_mode", False):
            return
        if getattr(self, "_chat_generating", False):
            return "break"
        entry = self._chat_entry_widget
        if entry is None:
            return "break"
        text = entry.get().strip()
        if not text:
            return "break"
        entry.delete(0, tk.END)
        self.send_chat_message(text)
        return "break"

    def append_chat_message(self, role: str, text: str) -> None:
        """Append a line to the scrollable chat log."""
        log = getattr(self, "_chat_log_widget", None)
        if log is None or not log.winfo_exists():
            return
        line = f"{role}: {text.strip()}\n"
        log.configure(state=tk.NORMAL)
        log.insert(tk.END, line)
        log.configure(state=tk.DISABLED)
        log.see(tk.END)
        self._fit_speech_bubble_to_content()
        self._schedule_speech_bubble_position()

    def set_chat_input_enabled(self, enabled: bool) -> None:
        """Enable or disable the chat entry while waiting for Ollama."""
        entry = getattr(self, "_chat_entry_widget", None)
        if entry is None:
            return
        try:
            if entry.winfo_exists():
                entry.configure(state=tk.NORMAL if enabled else tk.DISABLED)
                if enabled:
                    entry.focus_set()
        except tk.TclError:
            pass

    def set_chat_generating(self, generating: bool) -> None:
        """Toggle the generating flag and input state."""
        self._chat_generating = generating
        self.set_chat_input_enabled(not generating)
        if generating and hasattr(self, "change_sprite") and hasattr(self, "tk_img_thinking"):
            self.change_sprite(self.tk_img_thinking)
            self._talk_sprite_mode = "thinking"

    def speak_chat_response(self, text: str, pitch: int = 45) -> None:
        """Speak an AI reply without replacing the chat bubble."""
        if not getattr(self, "_chat_mode", False):
            self.speak(text, pitch)
            return

        self.interrupt_speech()
        epoch = self._speech_epoch
        self._tts_cancelled = False
        self.talking = True
        self._talk_sprite_mode = "talking"
        if hasattr(self, "change_sprite") and hasattr(self, "tk_img_talking"):
            self.change_sprite(self.tk_img_talking)

        def run_speech():
            with self._speech_lock:
                self._run_tts(text, pitch, voice_candidates=None, speech_epoch=epoch)
                if epoch != self._speech_epoch:
                    return

                def finish():
                    if epoch != self._speech_epoch:
                        return
                    self.talking = False
                    if getattr(self, "_chat_mode", False) and hasattr(self, "tk_img_normal"):
                        self.change_sprite(self.tk_img_normal)

                self.root.after(0, finish)

        threading.Thread(target=run_speech, daemon=True).start()

    def close_chat_mode(self) -> None:
        """End chat mode, reset conversation history, and close the bubble."""
        if hasattr(self, "_conversation"):
            self._conversation.reset()
        self._chat_mode = False
        self._chat_generating = False
        self._chat_log_widget = None
        self._chat_entry_widget = None
        self._close_speech_bubble_impl()
