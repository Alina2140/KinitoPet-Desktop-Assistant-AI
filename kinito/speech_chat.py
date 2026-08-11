"""Extended speech bubble for multi-turn Ollama chat."""

from __future__ import annotations

import threading
import tkinter as tk

from content import dialogue as dlg
from content import llm_prompts as prompts
from kinito.assets import starttalk_file_path
from kinito.features.emoji_picker import EmojiPickerMixin

CHAT_VOICE_CONTINUOUS = "continuous"
CHAT_VOICE_PUSH = "push"
MIC_LISTENING_BG = "#F4B84A"
MIC_ICON_SIZE = 18


def load_mic_button_icon(*, size: int = MIC_ICON_SIZE):
    """Return a small pixel-style microphone PhotoImage for the chat mic button."""
    try:
        from PIL import Image, ImageDraw, ImageTk
    except ImportError:
        return None

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Capsule mic body
    body = [size * 0.32, size * 0.12, size * 0.68, size * 0.58]
    draw.rounded_rectangle(body, radius=max(2, size // 5), fill=(17, 17, 17, 255))
    # Stand arc
    arc = [size * 0.22, size * 0.32, size * 0.78, size * 0.78]
    draw.arc(arc, start=0, end=180, fill=(17, 17, 17, 255), width=max(2, size // 9))
    # Stem + base
    cx = size // 2
    draw.line([(cx, size * 0.72), (cx, size * 0.88)], fill=(17, 17, 17, 255), width=max(2, size // 9))
    draw.line(
        [(size * 0.32, size * 0.88), (size * 0.68, size * 0.88)],
        fill=(17, 17, 17, 255),
        width=max(2, size // 9),
    )
    return ImageTk.PhotoImage(img)


class SpeechChatMixin(EmojiPickerMixin):
    """Chat-mode speech bubble with scrollable history and persistent input."""

    CHAT_TITLE = "Kinito Chat"
    CHAT_LOG_HEIGHT_PX = 120
    CHAT_LOG_WIDTH_PX = 360
    CHAT_KINITO_COLOR = "#cd77d1"
    CHAT_USER_COLOR = "#6A25EB"

    def _init_chat_state(self) -> None:
        """Initialize chat-related instance attributes (call from app __init__)."""
        self._chat_mode = False
        self._chat_generating = False
        self._chat_log_widget = None
        self._chat_entry_widget = None
        self._chat_voice_mode = None
        self._chat_voice_listening = False
        self._chat_voice_paused = False
        self._chat_mic_button = None
        self._voice_input = None
        self._init_emoji_picker_state()
        if not hasattr(self, "_chat_session_user_label"):
            self._chat_session_user_label = None

    def open_chat_mode_picker(self) -> None:
        """Show a short bubble asking continuous vs push-to-talk chat."""
        self.interrupt_speech()
        self._chat_mode = False
        self._chat_voice_mode = None
        self._stop_voice_input(discard=True)
        self._cancel_bubble_close_timer()

        if self._has_active_speech_bubble():
            self._close_speech_bubble_impl()

        self._play_bubble_sfx(starttalk_file_path)
        self.speech_bubble = self._new_speech_bubble_toplevel(dlg.CHAT_MODE_PROMPT)
        self._speech_bubble_ready = False
        self._speech_bubble_label = None
        self._speech_bubble_text_frame = None
        self._speech_bubble_button_frame = None
        self._speech_bubble_buttons_content_width = 0
        self._speech_bubble_entry = None
        self._chat_log_widget = None
        self._chat_entry_widget = None
        self._chat_mic_button = None
        self._close_emoji_picker()

        bubble_body = self._create_bubble_shell(self.speech_bubble)

        text_frame = tk.Frame(bubble_body, bg=self.BUBBLE_BG)
        text_frame.pack(fill=tk.X, anchor="w")
        self._speech_bubble_text_frame = text_frame

        label = self.create_wrapped_label(text_frame, dlg.CHAT_MODE_PROMPT)
        label.pack(
            fill=tk.X,
            expand=False,
            ipadx=self.BUBBLE_PAD_X,
            ipady=self.BUBBLE_PAD_Y,
            anchor="w",
        )
        self._speech_bubble_label = label

        button_frame = tk.Frame(bubble_body, bg=self.BUBBLE_BG)
        button_frame.pack(fill=tk.X, padx=self.BUBBLE_PAD_X, pady=(0, self.BUBBLE_PAD_Y))
        self._speech_bubble_button_frame = button_frame

        row = tk.Frame(button_frame, bg=self.BUBBLE_BG)
        row.pack()

        auto_btn = self._create_bubble_button(
            row,
            dlg.BUTTON_CHAT_AUTO_LISTEN,
            lambda: self._begin_chat_with_voice_mode(CHAT_VOICE_CONTINUOUS),
            padx=5,
            pady=1,
        )
        auto_btn.pack(side=tk.LEFT, padx=2)

        normal_btn = self._create_bubble_button(
            row,
            dlg.BUTTON_CHAT_NORMAL,
            lambda: self._begin_chat_with_voice_mode(CHAT_VOICE_PUSH),
            padx=5,
            pady=1,
        )
        normal_btn.pack(side=tk.LEFT, padx=2)

        close_button = self._create_bubble_button(
            row,
            "×",
            self.close_speech_bubble,
            width=2,
            padx=3,
            pady=1,
        )
        close_button.pack(side=tk.LEFT, padx=2)

        self._awaiting_response = True
        self._fit_speech_bubble_to_content()
        self._schedule_speech_bubble_position()
        self.speak(dlg.CHAT_MODE_PROMPT, show_bubble=False, skip_ai=True)

    def _begin_chat_with_voice_mode(self, mode: str) -> None:
        """Open the chat bubble after the user picks a voice input mode."""
        from kinito.stt.voice_input import check_voice_input_available

        fell_back = False
        if mode == CHAT_VOICE_CONTINUOUS:
            available, _err = check_voice_input_available()
            if not available:
                mode = CHAT_VOICE_PUSH
                fell_back = True
        self._chat_voice_mode = mode
        self._chat_voice_paused = False
        greeting = self._chat_greeting() if hasattr(self, "_chat_greeting") else dlg.CHAT_GREETING
        self.open_chat_bubble(greeting)
        if fell_back:
            self.append_chat_message(prompts.CHAT_ASSISTANT_LABEL, dlg.CHAT_VOICE_UNAVAILABLE)
        elif mode == CHAT_VOICE_CONTINUOUS:
            self.speak_chat_response(greeting)

    def open_chat_bubble(self, greeting: str) -> None:
        """Open a persistent chat bubble with an initial assistant greeting."""
        self.interrupt_speech()
        self._chat_mode = True
        self._chat_generating = False
        if hasattr(self, "_pin_chat_user_label") and not getattr(self, "_chat_session_user_label", None):
            self._pin_chat_user_label()
        self._cancel_bubble_close_timer()

        if self._has_active_speech_bubble():
            self._close_speech_bubble_impl()

        self._play_bubble_sfx(starttalk_file_path)
        self.speech_bubble = self._new_speech_bubble_toplevel(self.CHAT_TITLE)
        self._speech_bubble_ready = False
        self._speech_bubble_label = None
        self._speech_bubble_text_frame = None
        self._speech_bubble_button_frame = None
        self._chat_log_widget = None
        self._chat_entry_widget = None
        self._chat_mic_button = None
        self._close_emoji_picker()

        container = self._create_bubble_shell(self.speech_bubble)

        log_frame = tk.Frame(container, bg=self.BUBBLE_BG)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(5, 0), anchor="w")

        log = tk.Text(
            log_frame,
            height=6,
            width=48,
            wrap=tk.WORD,
            bg=self.BUBBLE_BG,
            fg=self.BUBBLE_FG,
            font=self._bubble_font(),
            relief=tk.FLAT,
            state=tk.DISABLED,
            cursor="arrow",
        )
        log.pack(fill=tk.BOTH, expand=True)
        self._configure_chat_log_tags(log)
        self._chat_log_widget = log

        self._show_chat_input_row(container)
        self.append_chat_message(prompts.CHAT_ASSISTANT_LABEL, greeting)

        self._awaiting_response = True
        self._fit_speech_bubble_to_content()
        self._schedule_speech_bubble_position()

    def _show_chat_input_row(self, parent) -> None:
        """Add the persistent chat entry row below the log."""
        self._emoji_dropdown_parent = parent
        input_frame = tk.Frame(parent, bg=self.BUBBLE_BG)
        input_frame.pack(fill=tk.X, padx=5, pady=5, anchor="w")
        self._speech_bubble_button_frame = input_frame

        voice_only = getattr(self, "_chat_voice_mode", None) == CHAT_VOICE_CONTINUOUS

        if voice_only:
            self._chat_entry_widget = None
            self._speech_bubble_entry = None
            self._emoji_button_photo = None
            self._emoji_picker_button = None
            spacer = tk.Frame(input_frame, bg=self.BUBBLE_BG)
            spacer.pack(side=tk.LEFT, fill=tk.X, expand=True)
        else:
            entry_font = self._bubble_font()
            if isinstance(entry_font, tuple) and len(entry_font) >= 2:
                entry_font = (entry_font[0], int(entry_font[1]) + 2)

            entry_width = self.get_entry_char_width("Type your message here...")
            entry = tk.Entry(
                input_frame,
                bg=self.BUBBLE_ENTRY_BG,
                fg=self.BUBBLE_FG,
                insertbackground=self.BUBBLE_FG,
                font=entry_font,
                width=entry_width,
                relief=tk.SOLID,
                borderwidth=1,
            )
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=2)
            entry.bind("<Return>", self._handle_chat_entry_submit)
            entry.bind("<BackSpace>", self._on_chat_entry_backspace)
            self._chat_entry_widget = entry
            self._speech_bubble_entry = entry
            self._bind_entry_focus_on_click(entry)

            if getattr(self, "_emoji_picker_enabled", True):
                from kinito.features.emoji_picker import load_emoji_button_icon

                self._emoji_button_photo = load_emoji_button_icon()
                if self._emoji_button_photo is not None:
                    emoji_button = self._create_bubble_button(
                        input_frame,
                        "",
                        self._toggle_emoji_picker,
                        image=self._emoji_button_photo,
                        padx=4,
                        pady=2,
                    )
                else:
                    emoji_button = self._create_bubble_button(
                        input_frame,
                        "☺",
                        self._toggle_emoji_picker,
                        width=2,
                        padx=4,
                    )
                emoji_button.pack(side=tk.LEFT, padx=(5, 0))
                self._emoji_picker_button = emoji_button
            else:
                self._emoji_button_photo = None
                self._emoji_picker_button = None

        self._mic_button_photo = load_mic_button_icon()
        if self._mic_button_photo is not None:
            mic_button = self._create_bubble_button(
                input_frame,
                "",
                self._toggle_chat_voice_listening,
                image=self._mic_button_photo,
                padx=4,
                pady=2,
            )
        else:
            mic_button = self._create_bubble_button(
                input_frame,
                "Mic",
                self._toggle_chat_voice_listening,
                width=3,
                padx=4,
                pady=2,
            )
        mic_button.pack(side=tk.LEFT, padx=(5, 0))
        self._chat_mic_button = mic_button
        self._update_mic_button_appearance()

        close_button = self._create_bubble_button(
            input_frame,
            "×",
            self.close_chat_mode,
            width=2,
            padx=4,
            pady=2,
        )
        close_button.pack(side=tk.LEFT, padx=(5, 0))
        if not voice_only:
            self._focus_bubble_entry(force=True)

    def _ensure_voice_input(self):
        """Create the shared voice controller if needed."""
        from kinito.stt.voice_input import VoiceInputController

        if self._voice_input is None:
            self._voice_input = VoiceInputController(
                schedule=lambda fn: self.root.after(0, fn),
                on_final_text=self._on_voice_transcript,
                on_error=self._on_voice_error,
            )
        return self._voice_input

    def _voice_capture_allowed(self) -> bool:
        """Return whether the mic may capture (echo / busy guards)."""
        if not getattr(self, "_chat_mode", False):
            return False
        if getattr(self, "_chat_generating", False):
            return False
        if getattr(self, "talking", False):
            return False
        return not getattr(self, "_chat_voice_paused", False)

    def _toggle_chat_voice_listening(self) -> None:
        """Start or stop mic listening from the chat mic button."""
        from kinito.stt.voice_input import check_voice_input_available

        if not getattr(self, "_chat_mode", False):
            return
        if getattr(self, "_chat_generating", False):
            return

        if self._chat_voice_listening:
            if self._chat_voice_mode == CHAT_VOICE_CONTINUOUS:
                self._chat_voice_paused = True
            self._stop_voice_input(discard=True)
            return

        available, _err = check_voice_input_available()
        if not available:
            self.speak(dlg.CHAT_VOICE_UNAVAILABLE, skip_ai=True)
            return

        if getattr(self, "talking", False):
            return

        self._chat_voice_paused = False
        self._start_voice_listening()

    def _start_voice_listening(self) -> None:
        """Begin capturing one utterance if capture is allowed."""
        from kinito.stt.voice_input import check_voice_input_available

        if not self._voice_capture_allowed():
            return
        available, _err = check_voice_input_available()
        if not available:
            return
        controller = self._ensure_voice_input()
        if controller.start():
            self._chat_voice_listening = True
            self._update_mic_button_appearance()

    def _stop_voice_input(self, *, discard: bool = False) -> None:
        """Stop the active voice capture session."""
        del discard  # stop always discards in-progress audio
        controller = getattr(self, "_voice_input", None)
        if controller is not None:
            controller.stop()
        self._chat_voice_listening = False
        self._update_mic_button_appearance()

    def _update_mic_button_appearance(self) -> None:
        """Highlight the mic button while listening."""
        button = getattr(self, "_chat_mic_button", None)
        if button is None:
            return
        try:
            if not button.winfo_exists():
                return
        except tk.TclError:
            return
        listening = bool(getattr(self, "_chat_voice_listening", False))
        fill = MIC_LISTENING_BG if listening else self.BUBBLE_BTN_BG
        active = self.BUBBLE_BTN_ACTIVE
        button._bg = fill
        button._active_bg = active
        if not getattr(button, "_hover", False):
            button._draw(fill)

    def _on_voice_transcript(self, text: str) -> None:
        """Handle a finished transcript on the UI thread."""
        self._chat_voice_listening = False
        self._update_mic_button_appearance()
        if not getattr(self, "_chat_mode", False):
            return
        cleaned = (text or "").strip()
        if not cleaned:
            if (
                self._chat_voice_mode == CHAT_VOICE_CONTINUOUS
                and not getattr(self, "_chat_voice_paused", False)
            ):
                self.root.after(200, self._maybe_resume_continuous_listening)
            return
        entry = getattr(self, "_chat_entry_widget", None)
        if entry is not None:
            try:
                if entry.winfo_exists():
                    entry.delete(0, tk.END)
            except tk.TclError:
                pass
        self.send_chat_message(cleaned)

    def _on_voice_error(self, message: str) -> None:
        """Handle mic/STT errors on the UI thread."""
        print(f"Kinito voice STT error: {message}", flush=True)
        self._chat_voice_listening = False
        self._update_mic_button_appearance()
        if not getattr(self, "_chat_mode", False):
            return
        self.append_chat_message(prompts.CHAT_ASSISTANT_LABEL, dlg.CHAT_VOICE_MIC_ERROR)
        if (
            self._chat_voice_mode == CHAT_VOICE_CONTINUOUS
            and not getattr(self, "_chat_voice_paused", False)
        ):
            self.root.after(800, self._maybe_resume_continuous_listening)

    def _maybe_resume_continuous_listening(self) -> None:
        """Restart listening in continuous mode when idle."""
        if self._chat_voice_mode != CHAT_VOICE_CONTINUOUS:
            return
        if getattr(self, "_chat_voice_paused", False):
            return
        if not self._voice_capture_allowed():
            return
        self._start_voice_listening()

    def _on_chat_tts_finished(self) -> None:
        """Resume continuous listening after Kinito finishes speaking."""
        if self._chat_voice_mode == CHAT_VOICE_CONTINUOUS:
            self._maybe_resume_continuous_listening()

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
        self._stop_voice_input(discard=True)
        entry.delete(0, tk.END)
        self.send_chat_message(text)
        return "break"

    def _configure_chat_log_tags(self, log: tk.Text) -> None:
        """Style speaker labels in the chat log."""
        log.tag_configure(
            "chat_kinito",
            foreground=self.CHAT_KINITO_COLOR,
            underline=True,
        )
        log.tag_configure(
            "chat_user",
            foreground=self.CHAT_USER_COLOR,
            underline=True,
        )

    def _resolve_chat_user_label(self) -> str:
        """Return one chat log label for the user (from memory when available)."""
        label = getattr(self, "chat_user_label", None)
        if callable(label):
            return label()
        return prompts.CHAT_USER_LABEL_FALLBACK

    def _resolve_chat_user_labels(self) -> set[str]:
        """Return all known user chat labels (lowercased) for speaker styling."""
        labels_fn = getattr(self, "chat_user_labels", None)
        if callable(labels_fn):
            names = [str(name).strip() for name in labels_fn() if str(name).strip()]
            if names:
                return {name.casefold() for name in names}
        single = self._resolve_chat_user_label().strip()
        if single:
            return {single.casefold()}
        return {prompts.CHAT_USER_LABEL_FALLBACK.casefold()}

    def _chat_role_tag(self, role: str) -> str | None:
        """Return the text tag for a chat speaker label, if any."""
        if role == prompts.CHAT_ASSISTANT_LABEL:
            return "chat_kinito"
        if role.casefold() in self._resolve_chat_user_labels():
            return "chat_user"
        return None

    def append_chat_message(self, role: str, text: str) -> None:
        """Append a line to the scrollable chat log."""
        log = getattr(self, "_chat_log_widget", None)
        if log is None or not log.winfo_exists():
            return
        message = text.strip()
        tag = self._chat_role_tag(role)
        log.configure(state=tk.NORMAL)
        if tag is not None:
            log.insert(tk.END, f"{role}:", tag)
            log.insert(tk.END, f" {message}\n")
        else:
            log.insert(tk.END, f"{role}: {message}\n")
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
                    self._focus_bubble_entry(force=True)
        except tk.TclError:
            pass

    def set_chat_generating(self, generating: bool) -> None:
        """Toggle the generating flag and input state."""
        if generating:
            self._stop_voice_input(discard=True)
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

        self._stop_voice_input(discard=True)
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
                    self._on_chat_tts_finished()

                self.root.after(0, finish)

        threading.Thread(target=run_speech, daemon=True).start()

    def close_chat_mode(self) -> None:
        """End chat mode, reset conversation history, and close the bubble."""
        self._stop_voice_input(discard=True)
        self._chat_voice_mode = None
        self._chat_voice_paused = False
        self._close_emoji_picker()
        if hasattr(self, "_conversation"):
            self._conversation.reset()
        self._chat_mode = False
        self._chat_generating = False
        self._chat_log_widget = None
        self._chat_entry_widget = None
        self._emoji_picker_button = None
        self._chat_mic_button = None
        if hasattr(self, "_clear_chat_session_user_label"):
            self._clear_chat_session_user_label()
        self._close_speech_bubble_impl()
