"""Text-to-speech, speech bubbles, and interactive dialog UI."""

import os
import subprocess
import threading
import tkinter as tk
from tkinter import Toplevel

import pygame

from content import dialogue as dlg
from content.dialog_registry import (
    apply_dialog_ui,
    find_dialog_spec,
    handle_dialog_response,
)
from kinito.assets import balconexe_directory, engine, starttalk_file_path, stoptalk_file_path
from kinito.tk_timers import schedule_after


class SpeechMixin:
    """TTS playback, speech bubbles, and user response handling."""

    BUBBLE_MAX_WIDTH = 800
    BUBBLE_BG = "light gray"
    BUBBLE_TRANSPARENT_BG = "white"
    DISMISS_RESPONSE_BUTTONS = frozenset(
        {
            dlg.BUTTON_NOT_NOW,
            dlg.BUTTON_NO,
            dlg.BUTTON_POEM_REJECT,
        }
    )
    VOICE_DEFAULT = "Eddie"
    VOICE_NORMAL_CANDIDATES = [
        "Eddie",
        "Peter",
        "Douglas",
        "Microsoft Zira Desktop",
        "Microsoft Hedda Desktop",
    ]
    VOICE_WHISPER_CANDIDATES = [
        "Female Whisper",
        "Julia",
        "Wanda",
        "Microsoft Hedda Desktop",
        "Eddie",
    ]

    BUBBLE_CLOSE_BUFFER_MS = 1500
    BUBBLE_REVEAL_DELAY_MS = 100
    BUBBLE_OFF_SCREEN_GEOMETRY = "-10000-10000"
    BRIEF_ACK_DISPLAY_MS = 2000
    POEM_READ_MS_MIN = 5000
    POEM_READ_MS_MAX = 45000
    POEM_READ_MS_PER_CHAR = 40

    def get_max_bubble_width(self):
        """Return the maximum width of a speech bubble in pixels."""
        return self.BUBBLE_MAX_WIDTH

    def get_entry_char_width(self, prompt=""):
        """Compute a sensible Entry widget width from the prompt length."""
        return min(40, max(15, len(prompt) // 3 + 8))

    def _bubble_wraplength(self, text):
        """Pick a wrap width that fits short prompts without a wide empty bubble."""
        return min(self.BUBBLE_MAX_WIDTH - 20, max(140, len(text) * 8))

    def _measure_text_width(self, parent, text):
        """Return the pixel width *text* needs on a single line."""
        temp = tk.Label(parent, text=text)
        temp.update_idletasks()
        measured = temp.winfo_reqwidth()
        temp.destroy()
        return measured

    def _measure_button_width(self, parent, text, *, width=None):
        """Return the pixel width a button with *text* needs."""
        kwargs = {"text": text}
        if width is not None:
            kwargs["width"] = width
        temp = tk.Button(parent, **kwargs)
        temp.update_idletasks()
        measured = temp.winfo_reqwidth()
        temp.destroy()
        return measured

    def create_wrapped_label(self, parent, text):
        """Create a word-wrapped label for bubble text."""
        label = tk.Label(
            parent,
            text=text,
            bg=self.BUBBLE_BG,
            fg="black",
            wraplength=self._bubble_wraplength(text),
            justify="left",
        )
        return label

    def _fit_speech_bubble_to_content(self):
        """Shrink the bubble window to its content so no empty side bars remain."""
        if not self._has_active_speech_bubble():
            return
        bubble = self.speech_bubble
        try:
            bubble.update_idletasks()
            width = bubble.winfo_reqwidth()
            height = bubble.winfo_reqheight()
            if width > 0 and height > 0:
                bubble.geometry(f"{width}x{height}")
        except tk.TclError:
            pass

    def _cancel_bubble_close_timer(self):
        """Cancel any scheduled auto-close for the current speech bubble."""
        if getattr(self, "_bubble_close_timer", None) is not None:
            try:
                self.root.after_cancel(self._bubble_close_timer)
            except (tk.TclError, ValueError):
                pass
            self._bubble_close_timer = None

    def _schedule_bubble_close(self, delay_ms):
        """Close the speech bubble after *delay_ms* milliseconds."""
        self._cancel_bubble_close_timer()
        self._bubble_close_timer = self.root.after(delay_ms, self._auto_close_speech_bubble)

    def _auto_close_speech_bubble(self):
        """Timer callback that destroys the speech bubble."""
        self._bubble_close_timer = None
        self.close_speech_bubble()

    def _next_speech_epoch(self):
        """Increment and return the speech epoch (invalidates stale bubble timers)."""
        self._speech_epoch += 1
        return self._speech_epoch

    def _schedule_bubble_close_if_current(self, epoch, delay_ms):
        """Schedule bubble close only if *epoch* is still the active speech."""
        if epoch != self._speech_epoch:
            return
        if self._awaiting_response:
            return
        if not self._has_active_speech_bubble():
            return
        self._schedule_bubble_close(delay_ms)

    def _bubble_reading_tail(self, text, *, long_read=False):
        """Extra display time for long texts (poems) based on character count."""
        if not long_read:
            return 0
        return min(
            self.POEM_READ_MS_MAX,
            max(self.POEM_READ_MS_MIN, len(text) * self.POEM_READ_MS_PER_CHAR),
        )

    def _bubble_close_delay_after_tts(self, text, *, long_read=False):
        """Milliseconds to keep the bubble open after TTS finishes."""
        return self.BUBBLE_CLOSE_BUFFER_MS + self._bubble_reading_tail(text, long_read=long_read)

    def _bubble_display_duration(self, text, *, long_read=False):
        """Alias for total bubble visibility duration after speech."""
        return self._bubble_close_delay_after_tts(text, long_read=long_read)

    def _has_active_speech_bubble(self):
        """Return True if a speech bubble Toplevel exists."""
        try:
            return hasattr(self, "speech_bubble") and self.speech_bubble.winfo_exists()
        except tk.TclError:
            return False

    def _is_busy_with_speech(self):
        """Return True while TTS, a bubble, a user response, or AI generation is in progress."""
        return (
            self.talking
            or self._awaiting_response
            or self._has_active_speech_bubble()
            or getattr(self, "_ai_generating", False)
        )

    def _is_background_music_playing(self):
        """Return True if pygame is playing background music."""
        try:
            return pygame.mixer.get_init() and pygame.mixer.music.get_busy()
        except pygame.error:
            return False

    def _should_skip_drag_sounds(self):
        """Suppress drag sounds when speech or music would clash."""
        return self._is_busy_with_speech() or self._is_background_music_playing()

    def _load_available_voices(self):
        """Query balcon.exe for installed TTS voices."""
        if not os.path.isfile(balconexe_directory):
            return set()
        try:
            result = subprocess.run(
                [balconexe_directory, "-l"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            voices = set()
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line or line.endswith(":"):
                    continue
                if "::" in line:
                    voices.add(line.split("::", 1)[0].strip())
                else:
                    voices.add(line)
            if voices:
                return voices
        except (OSError, subprocess.SubprocessError, ValueError):
            pass
        return {self.VOICE_DEFAULT}

    def _tts_interrupted(self, speech_epoch=None) -> bool:
        """Return True if this utterance was cancelled or superseded."""
        if getattr(self, "_tts_cancelled", False):
            return True
        return speech_epoch is not None and self._speech_epoch != speech_epoch

    def _stop_active_tts(self):
        """Terminate an in-progress balcon or pyttsx3 utterance."""
        self._tts_cancelled = True
        process = getattr(self, "_tts_process", None)
        if process is not None and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=1)
            except (OSError, subprocess.SubprocessError, ValueError):
                try:
                    process.kill()
                except (OSError, subprocess.SubprocessError, ValueError):
                    pass
        self._tts_process = None

        if engine is not None:
            try:
                engine.stop()
            except Exception:
                pass

    def _speech_bubble_title(self) -> str:
        """Return the active bubble title, or empty string if none exists."""
        if not self._has_active_speech_bubble():
            return ""
        try:
            return self.speech_bubble.wm_title()
        except tk.TclError:
            return ""

    def interrupt_speech(self):
        """Stop current TTS and invalidate pending bubble callbacks."""
        self._next_speech_epoch()
        self._stop_active_tts()
        self._cancel_bubble_close_timer()
        if getattr(self, "_ai_generating", False):
            self._ai_generating = False
        if (
            not getattr(self, "_chat_mode", False)
            and not getattr(self, "_awaiting_response", False)
            and self._has_active_speech_bubble()
            and hasattr(self, "_close_speech_bubble_impl")
        ):
            self._close_speech_bubble_impl()
        self._preserve_sprite = False
        self._talk_sprite_mode = "talking"
        self.talking = False

    def _run_pyttsx3_fallback(self, text):
        """Speak *text* via pyttsx3 when balcon is unavailable."""
        if engine is None:
            return False
        try:
            engine.say(text)
            engine.runAndWait()
            return True
        except Exception:
            return False

    @staticmethod
    def _balcon_command(voice: str, pitch: int) -> list[str]:
        """Build a balcon argv that reads speech text from stdin."""
        return [
            balconexe_directory,
            "-n",
            voice,
            "-i",
            "-enc",
            "utf8",
            "-p",
            str(pitch),
        ]

    def _run_balcon_tts(self, voice: str, text: str, pitch: int, speech_epoch=None) -> bool:
        """Run balcon for *text*, feeding the line via stdin to survive quotes."""
        if self._tts_interrupted(speech_epoch):
            return False
        try:
            process = subprocess.Popen(
                self._balcon_command(voice, pitch),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
        except (OSError, subprocess.SubprocessError, ValueError):
            return False

        self._tts_process = process
        try:
            try:
                process.communicate(input=text, timeout=120)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                return False
        finally:
            self._tts_process = None

        if self._tts_interrupted(speech_epoch):
            return False
        return process.returncode == 0

    def _run_tts(self, text, pitch=45, voice_candidates=None, speech_epoch=None):
        """Run TTS via balcon (preferred) or pyttsx3 fallback."""
        if voice_candidates is None:
            voice_candidates = self.VOICE_NORMAL_CANDIDATES

        self._tts_process = None

        if os.path.isfile(balconexe_directory):
            for voice in voice_candidates:
                if voice not in self._available_voices:
                    continue
                if self._run_balcon_tts(voice, text, pitch, speech_epoch=speech_epoch):
                    return True
                if self._tts_interrupted(speech_epoch):
                    return False

        if self._tts_interrupted(speech_epoch):
            return False
        return self._run_pyttsx3_fallback(text)

    def _infer_talk_sprite_mode(self, text, question=None):
        """Return 'thinking' for questions and 'talking' for statements."""
        if question is not None:
            return "thinking" if question else "talking"
        if find_dialog_spec(text) is not None:
            return "thinking"
        if text.strip().endswith("?"):
            return "thinking"
        return "talking"

    def speak(
        self,
        text,
        pitch=45,
        slow=False,
        show_bubble=True,
        voice_candidates=None,
        long_bubble=False,
        wait_for_tts=False,
        allow_in_focus=False,
        preserve_sprite=False,
        question=None,
        *,
        ai_hint=None,
        skip_ai=False,
    ):
        """Speak *text* in a background thread; optionally show and auto-close a bubble."""
        del ai_hint, skip_ai  # handled by LLMMixin when present in the MRO
        if getattr(self, "_focus_mode", False) and not allow_in_focus:
            return
        self.interrupt_speech()
        epoch = self._speech_epoch
        self._tts_cancelled = False
        self.talking = True
        self._preserve_sprite = preserve_sprite
        self._talk_sprite_mode = self._infer_talk_sprite_mode(text, question=question)

        def run_speech():
            with self._speech_lock:
                if show_bubble:
                    self.root.after(
                        0,
                        lambda: self.show_speech_bubble(
                            text,
                            evergoaway=False,
                            speech_epoch=epoch,
                        ),
                    )
                self._run_tts(text, pitch, voice_candidates, speech_epoch=epoch)
                if epoch != self._speech_epoch:
                    return
                if show_bubble and find_dialog_spec(text) is None:
                    delay = self._bubble_close_delay_after_tts(text, long_read=long_bubble)
                    self.root.after(
                        0,
                        lambda: self._schedule_bubble_close_if_current(epoch, delay),
                    )
                elif not show_bubble:
                    self.talking = False

        thread = threading.Thread(target=run_speech, daemon=True)
        thread.start()
        if wait_for_tts:
            thread.join()

    def speak_brief(self, text, display_ms=None, *, allow_in_focus=False):
        """Show a short on-screen acknowledgment without TTS after the user interrupted speech.

        Do not use for normal dialog lines — use ``speak()`` so Kinito actually says them.
        """
        if getattr(self, "_focus_mode", False) and not allow_in_focus:
            return
        if display_ms is None:
            display_ms = self.BRIEF_ACK_DISPLAY_MS

        self.interrupt_speech()
        epoch = self._speech_epoch
        self.talking = True
        self._talk_sprite_mode = self._infer_talk_sprite_mode(text)
        self.show_speech_bubble(text, evergoaway=False, speech_epoch=epoch, force=True)
        self._schedule_bubble_close_if_current(epoch, display_ms)

    def speak_whisper(self, text, pitch=25, slow=False, long_bubble=False, *, ai_hint=None, skip_ai=False):
        """Speak *text* with whisper voice candidates and optional long bubble display."""
        del ai_hint, skip_ai
        self.speak(
            text,
            pitch=pitch,
            slow=slow,
            voice_candidates=self.VOICE_WHISPER_CANDIDATES,
            long_bubble=long_bubble,
        )

    def show_speech_bubble(self, text, evergoaway=True, force=False, speech_epoch=None):
        """Open a borderless speech bubble; attach dialog UI if *text* matches a spec."""
        if speech_epoch is not None and speech_epoch != self._speech_epoch:
            return
        if not force and self._awaiting_response and self._has_active_speech_bubble():
            return

        self._cancel_bubble_close_timer()
        if self._has_active_speech_bubble():
            self.close_speech_bubble()

        if speech_epoch is not None:
            self._active_bubble_epoch = speech_epoch

        self.play_sfx(starttalk_file_path)
        self.speech_bubble = self._new_speech_bubble_toplevel(text)
        self._speech_bubble_label = None
        self._speech_bubble_text_frame = None
        self._speech_bubble_button_frame = None

        text_frame = tk.Frame(self.speech_bubble, bg=self.BUBBLE_BG)
        text_frame.pack(fill=tk.X, anchor="w")
        self._speech_bubble_text_frame = text_frame

        label = self.create_wrapped_label(text_frame, text)
        label.pack(fill=tk.BOTH, expand=True, ipadx=5, ipady=5, anchor="w")
        self._speech_bubble_label = label

        spec = find_dialog_spec(text)
        needs_response = spec is not None
        if spec:
            apply_dialog_ui(self, spec)

        self._fit_speech_bubble_to_content()
        self._schedule_speech_bubble_position()

        if needs_response:
            self._awaiting_response = True

    def _response_buttons_need_close(self, options):
        """Return True when no explicit decline button makes a separate × redundant."""
        return not any(option in self.DISMISS_RESPONSE_BUTTONS for option in options)

    def _align_bubble_text_to_buttons(self):
        """Match the text bar width to the button row; never wrap wider text."""
        label = getattr(self, "_speech_bubble_label", None)
        text_frame = getattr(self, "_speech_bubble_text_frame", None)
        button_frame = getattr(self, "_speech_bubble_button_frame", None)
        if (
            not self._has_active_speech_bubble()
            or label is None
            or text_frame is None
            or not label.winfo_exists()
            or not text_frame.winfo_exists()
        ):
            return

        try:
            self.speech_bubble.update_idletasks()
            text_frame.update_idletasks()
            label.update_idletasks()

            pad_x = 10
            pad_y = 10
            text = label.cget("text")
            text_width = self._measure_text_width(text_frame, text)

            buttons_width = 0
            if button_frame is not None and button_frame.winfo_exists():
                button_frame.update_idletasks()
                buttons_width = button_frame.winfo_reqwidth()

            if buttons_width > 0:
                if text_width + pad_x > buttons_width:
                    label.config(wraplength=0)
                else:
                    label.config(wraplength=max(buttons_width - pad_x, 1))
            else:
                label.config(wraplength=self._bubble_wraplength(text))

            text_frame.update_idletasks()
            label.update_idletasks()

            content_width = max(
                buttons_width,
                text_width + pad_x,
                label.winfo_reqwidth() + pad_x,
            )
            content_height = max(label.winfo_reqheight() + pad_y, 1)
            text_frame.configure(width=content_width, height=content_height)
            text_frame.pack_propagate(False)
        except tk.TclError:
            pass

    def show_response_buttons(self, options):
        """Add wrapped rows of response buttons below the bubble text."""
        if hasattr(self, "speech_bubble") and self.speech_bubble.winfo_exists():
            button_frame = tk.Frame(self.speech_bubble, bg=self.BUBBLE_TRANSPARENT_BG)
            button_frame.pack(anchor="w")
            self._speech_bubble_button_frame = button_frame

            max_row_width = self.get_max_bubble_width() - 20
            show_close = self._response_buttons_need_close(options)
            close_width = (
                self._measure_button_width(button_frame, "×", width=2) + 10 if show_close else 0
            )
            row_frame = tk.Frame(button_frame, bg=self.BUBBLE_TRANSPARENT_BG)
            row_frame.pack(anchor="w")
            row_width = 0

            for option in options:
                btn_width = self._measure_button_width(row_frame, option) + 10
                needs_new_row = (
                    row_width > 0 and row_width + btn_width + close_width > max_row_width
                )
                if needs_new_row:
                    row_frame = tk.Frame(button_frame, bg=self.BUBBLE_TRANSPARENT_BG)
                    row_frame.pack(anchor="w")
                    row_width = 0
                option_button = tk.Button(
                    row_frame,
                    text=option,
                    command=lambda response=option: self.handle_response(response),
                )
                option_button.pack(side=tk.LEFT, padx=5)
                row_width += btn_width

            if show_close:
                close_button = tk.Button(
                    row_frame,
                    text="×",
                    width=2,
                    command=self.close_speech_bubble,
                )
                close_button.pack(side=tk.LEFT, padx=5)

            self._align_bubble_text_to_buttons()
            self._fit_speech_bubble_to_content()
            self._schedule_speech_bubble_position()

    def _add_textbox_row(self, parent, prompt):
        """Add an Entry + close button row for free-text dialog responses."""
        input_frame = tk.Frame(parent, bg=self.BUBBLE_BG)
        input_frame.pack(ipadx=10, ipady=5, anchor="w")

        entry_width = self.get_entry_char_width(prompt)
        entry = tk.Entry(input_frame, bg=self.BUBBLE_BG, fg="black", width=entry_width)
        entry.pack(side=tk.LEFT, ipady=2)
        entry.bind("<Return>", lambda event: self.handle_response(entry.get()))

        close_button = tk.Button(
            input_frame,
            text="×",
            width=2,
            command=self.close_speech_bubble,
        )
        close_button.pack(side=tk.LEFT, padx=(5, 0))

        entry.focus_set()
        return entry

    def show_response_textbox(self, prompt):
        """Show or extend the bubble with a text entry for the user's answer."""
        if self._has_active_speech_bubble():
            self._add_textbox_row(self.speech_bubble, prompt)
            self._fit_speech_bubble_to_content()
            self._schedule_speech_bubble_position()
        else:
            self.speech_bubble = self._new_speech_bubble_toplevel(prompt)

            label = self.create_wrapped_label(self.speech_bubble, prompt)
            label.pack(ipadx=10, ipady=5, anchor="w")

            self._add_textbox_row(self.speech_bubble, prompt)
            self._fit_speech_bubble_to_content()
            self._schedule_speech_bubble_position()

    def handle_response(self, response):
        """Route a button or textbox answer to the matching dialog handler."""
        current_question = self._speech_bubble_title()
        self.interrupt_speech()
        self.close_speech_bubble()

        spec = find_dialog_spec(current_question)
        if spec:
            handle_dialog_response(self, spec, response)

    def close_speech_bubble(self):
        """Destroy the speech bubble and reset speech/hug state."""
        if getattr(self, "_chat_mode", False) and hasattr(self, "close_chat_mode"):
            self.close_chat_mode()
            return
        self._close_speech_bubble_impl()

    def _close_speech_bubble_impl(self):
        """Destroy the speech bubble without chat-mode teardown."""
        self._cancel_bubble_close_timer()
        self._awaiting_response = False
        self._preserve_sprite = False
        self._talk_sprite_mode = "talking"
        self._speech_bubble_last_pos = None
        self._speech_bubble_label = None
        self._speech_bubble_text_frame = None
        self._speech_bubble_button_frame = None
        self._stop_active_tts()
        if self._has_active_speech_bubble():
            self.speech_bubble.destroy()
            self.play_sfx(stoptalk_file_path)
            self.talking = False

    def _new_speech_bubble_toplevel(self, title):
        """Create a hidden speech-bubble window parked off-screen."""
        bubble = Toplevel(self.root)
        bubble.withdraw()
        bubble.geometry(self.BUBBLE_OFF_SCREEN_GEOMETRY)
        bubble.configure(bg=self.BUBBLE_TRANSPARENT_BG)
        bubble.overrideredirect(True)
        bubble.attributes("-transparentcolor", "white")
        bubble.wm_attributes("-topmost", True)
        bubble.wm_title(title)
        return bubble

    def _speech_bubble_reveal_delay_ms(self):
        """Delay before showing a bubble so Kinito's window position is settled."""
        return getattr(self, "STARTUP_REVEAL_DELAY_MS", self.BUBBLE_REVEAL_DELAY_MS)

    def _reveal_speech_bubble(self):
        """Measure layout, position beside Kinito, then show the bubble."""
        if not self._has_active_speech_bubble():
            return
        self._fit_speech_bubble_to_content()
        self.root.update_idletasks()
        self.speech_bubble.update_idletasks()
        self.position_speech_bubble()
        try:
            self.speech_bubble.deiconify()
            self.speech_bubble.lift()
        except tk.TclError:
            pass

    def _schedule_speech_bubble_position(self):
        """Position and reveal the bubble after layout has settled."""
        delay = self._speech_bubble_reveal_delay_ms()
        self.root.after(delay, self._reveal_speech_bubble)
        self.root.after(delay + delay, self._reveal_speech_bubble)

    def position_speech_bubble(self):
        """Place the bubble above Kinito, clamped to screen bounds."""
        if not hasattr(self, "speech_bubble") or not self.speech_bubble.winfo_exists():
            return

        self.root.update_idletasks()
        self.speech_bubble.update_idletasks()

        kinito_x = self.root.winfo_rootx()
        kinito_y = self.root.winfo_rooty()
        if kinito_x <= 0 or kinito_y <= 0:
            kinito_x = getattr(self, "x", kinito_x)
            kinito_y = getattr(self, "y", kinito_y)
        kinito_w = max(
            self.root.winfo_width(),
            getattr(getattr(self, "img_normal", None), "width", 0),
            1,
        )
        bubble_w = self.speech_bubble.winfo_width()
        bubble_h = self.speech_bubble.winfo_height()

        gap = 30
        bubble_x = kinito_x + (kinito_w // 2) - (bubble_w // 2)
        bubble_y = kinito_y - bubble_h - gap

        min_x, min_y, max_x, max_y = self.get_screen_bounds(bubble_w, bubble_h)
        bubble_x = max(min_x, min(bubble_x, max_x))
        bubble_y = max(min_y, min(bubble_y, max_y))

        new_pos = (bubble_x, bubble_y)
        if getattr(self, "_speech_bubble_last_pos", None) == new_pos:
            return
        self._speech_bubble_last_pos = new_pos

        self.speech_bubble.geometry(f"+{bubble_x}+{bubble_y}")
        self.speech_bubble.lift()
        self.speech_bubble.wm_attributes("-topmost", True)

    def _update_speech_bubble_position(self):
        """Periodic callback to keep bubbles on-screen and follow Kinito."""
        self._bubble_position_timer = None
        if not getattr(self, "_running", True):
            return
        try:
            if not self.root.winfo_exists():
                return
        except tk.TclError:
            return
        if hasattr(self, "ensure_on_screen"):
            self.ensure_on_screen()
        if hasattr(self, "speech_bubble"):
            try:
                if self.speech_bubble.winfo_exists():
                    self.position_speech_bubble()
                else:
                    delattr(self, "speech_bubble")
            except tk.TclError:
                pass
        schedule_after(
            self.root,
            self,
            "_bubble_position_timer",
            100,
            self._update_speech_bubble_position,
        )

    def ask_what_todo(self, event):
        """Right-click handler: open or close the action menu speech bubble."""
        if (
            hasattr(self, "speech_bubble")
            and self.speech_bubble.winfo_exists()
            and dlg.MENU_PROMPT in self.speech_bubble.wm_title()
        ):
            self.close_speech_bubble()
            return
        self.speak(dlg.MENU_PROMPT, 45, True, allow_in_focus=True)
