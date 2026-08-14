"""Text-to-speech, speech bubbles, and interactive dialog UI."""

import os
import subprocess
import tempfile
import threading
import time
import tkinter as tk
import wave
from tkinter import Toplevel

import numpy as np
import pygame

try:
    import sounddevice as sd
except ImportError:  # optional at runtime; listed in requirements.txt
    sd = None

from content import dialogue as dlg
from content.dialog_registry import (
    apply_dialog_ui,
    find_dialog_spec,
    handle_dialog_response,
)
from kinito.assets import balconexe_directory, engine, starttalk_file_path, stoptalk_file_path
from kinito.bubble_ui import (
    ChamferedButton,
    draw_bubble_shell,
    measure_chamfered_button,
    outline_canvas_pad,
)
from kinito.tk_timers import schedule_after
from kinito.tts_text import normalize_text_for_tts


class SpeechMixin:
    """TTS playback, speech bubbles, and user response handling."""

    BUBBLE_MAX_WIDTH = 533
    BUBBLE_BG = "#FFF8E7"
    BUBBLE_BORDER = "#000000"
    BUBBLE_FG = "#111111"
    BUBBLE_TRANSPARENT_BG = "white"
    BUBBLE_BORDER_WIDTH = 1
    BUBBLE_CHAMFER = 8
    BUBBLE_BTN_CHAMFER = 5
    BUBBLE_TAIL_HEIGHT = 12
    BUBBLE_TAIL_HALF_WIDTH = 11
    BUBBLE_PAD_X = 12
    BUBBLE_PAD_Y = 10
    BUBBLE_BTN_BG = "#fff1ce"
    BUBBLE_BTN_ACTIVE = "#FFE9A8"
    BUBBLE_ENTRY_BG = "#FFFEF8"
    BUBBLE_BTN_PAD_X = 8
    BUBBLE_BTN_PAD_Y = 2
    DISMISS_RESPONSE_BUTTONS = frozenset(
        {
            dlg.BUTTON_NOT_NOW,
            dlg.BUTTON_NO,
            dlg.BUTTON_POEM_REJECT,
        }
    )
    VOICE_DEFAULT = "Eddie"
    # TruVoice-only: Microsoft SAPI5 voices sound like a generic Windows narrator.
    VOICE_NORMAL_CANDIDATES = [
        "Eddie",
        "Peter",
        "Douglas",
        "Sidney",
        "Melvin",
    ]
    VOICE_WHISPER_CANDIDATES = [
        "Female Whisper",
        "Eddie",
        "Peter",
        "Douglas",
        "Julia",
        "Wanda",
    ]
    # Last-resort system voices only when no TruVoice engine is installed.
    VOICE_SYSTEM_FALLBACK_CANDIDATES = [
        "Microsoft Zira Desktop",
        "Microsoft Hedda Desktop",
    ]

    BUBBLE_CLOSE_BUFFER_MS = 1500
    RESPONSE_TIMEOUT_MS = 120_000
    BUBBLE_REVEAL_DELAY_MS = 100
    BUBBLE_OFF_SCREEN_GEOMETRY = "-10000-10000"
    BRIEF_ACK_DISPLAY_MS = 2000
    POEM_READ_MS_MIN = 5000
    POEM_READ_MS_MAX = 45000
    POEM_READ_MS_PER_CHAR = 40

    def _has_protected_interactive_state(self) -> bool:
        """Return True while a memory question or other response dialog must stay open."""
        return (
            getattr(self, "_pending_memory_question", None) is not None
            or self._awaiting_response
            or getattr(self, "_planning_memory_question", False)
        )

    def _may_start_speech(self, text) -> bool:
        """Return False when *text* would replace a protected interactive bubble."""
        pending = getattr(self, "_pending_memory_question", None)
        if pending is not None and str(text) == pending.question:
            return True
        return not self._has_protected_interactive_state()

    def get_max_bubble_width(self):
        """Return the maximum width of a speech bubble in pixels."""
        return self.BUBBLE_MAX_WIDTH

    def _bubble_font(self):
        """Return the font used inside KinitoPET-style speech bubbles."""
        if os.name == "nt":
            return ("Tahoma", 10, "italic")
        return ("Helvetica", 11, "italic")

    def _bubble_button_font(self):
        """Return the font used on speech-bubble action buttons."""
        if os.name == "nt":
            return ("Tahoma", 10)
        return ("Helvetica", 11)

    def _bubble_button_options(self, **extra):
        """Return shared styling kwargs for speech-bubble action buttons."""
        del extra
        return {
            "font": self._bubble_button_font(),
            "bg": self.BUBBLE_BTN_BG,
            "active_bg": self.BUBBLE_BTN_ACTIVE,
            "fg": self.BUBBLE_FG,
            "border": self.BUBBLE_BORDER,
            "border_width": self.BUBBLE_BORDER_WIDTH,
            "chamfer": self.BUBBLE_BTN_CHAMFER,
            "padx": self.BUBBLE_BTN_PAD_X,
            "pady": self.BUBBLE_BTN_PAD_Y,
            "cursor": "hand2",
        }

    def _create_bubble_button(self, parent, text, command, **extra):
        """Create a speech-bubble button with chamfered corners."""
        options = self._bubble_button_options()
        options.update(extra)
        return ChamferedButton(parent, text=text, command=command, **options)

    def _create_bubble_shell(self, parent):
        """Build the cream speech panel with chamfered corners and bottom tail."""
        outer = tk.Frame(parent, bg=self.BUBBLE_TRANSPARENT_BG)
        outer.pack(anchor="w")

        shell = tk.Canvas(
            outer,
            bg=self.BUBBLE_TRANSPARENT_BG,
            highlightthickness=0,
            borderwidth=0,
            takefocus=0,
        )
        shell.pack(anchor="w")

        body = tk.Frame(shell, bg=self.BUBBLE_BG)
        body_window = shell.create_window(0, 0, window=body, anchor="nw")

        self._speech_bubble_outer = outer
        self._speech_bubble_canvas = shell
        self._speech_bubble_body = body
        self._speech_bubble_body_window = body_window
        return body

    def _kinito_screen_position(self):
        """Return Kinito's top-left corner in screen coordinates."""
        if (
            getattr(self, "is_dragging", False)
            or getattr(self, "_throwing", False)
            or getattr(self, "moving", False)
        ):
            tracked_x = getattr(self, "x", None)
            tracked_y = getattr(self, "y", None)
            if tracked_x is not None and tracked_y is not None:
                return int(tracked_x), int(tracked_y)

        kinito_x = self.root.winfo_rootx()
        kinito_y = self.root.winfo_rooty()
        if kinito_x > 0 and kinito_y > 0:
            return int(kinito_x), int(kinito_y)

        tracked_x = getattr(self, "x", None)
        tracked_y = getattr(self, "y", None)
        if tracked_x is not None and tracked_y is not None:
            return int(tracked_x), int(tracked_y)
        return int(kinito_x), int(kinito_y)

    def _kinito_screen_width(self):
        """Return Kinito's visible width in pixels."""
        return max(
            self.root.winfo_width(),
            getattr(getattr(self, "img_normal", None), "width", 0),
            1,
        )

    def _bubble_screen_size(self):
        """Return the speech bubble's width and height for layout calculations."""
        bubble = self.speech_bubble
        bubble.update_idletasks()
        # Prefer requested content size. Realized winfo_* can stay inflated after
        # off-screen reveal on Windows transparent windows and push the bubble up.
        req_w = max(int(bubble.winfo_reqwidth()), 1)
        req_h = max(int(bubble.winfo_reqheight()), 1)
        win_w = int(bubble.winfo_width())
        win_h = int(bubble.winfo_height())
        bubble_w = win_w if 1 < win_w <= req_w + 8 else req_w
        bubble_h = win_h if 1 < win_h <= req_h + 8 else req_h
        return bubble_w, bubble_h

    def _kinito_screen_center_x(self):
        """Return Kinito's horizontal center in screen coordinates."""
        kinito_x, _kinito_y = self._kinito_screen_position()
        return kinito_x + (self._kinito_screen_width() // 2)

    def _bubble_tail_center_x(self, tail_width):
        """Return where the bubble tail should sit to point at Kinito."""
        if tail_width <= 0:
            return 0
        if not self._has_active_speech_bubble():
            return tail_width // 2
        try:
            aim_x = self._kinito_screen_center_x() - self.speech_bubble.winfo_rootx()
        except (tk.TclError, AttributeError):
            return tail_width // 2
        margin = self.BUBBLE_TAIL_HALF_WIDTH + self.BUBBLE_BORDER_WIDTH
        if tail_width <= (2 * margin):
            return tail_width // 2
        return max(margin, min(int(aim_x), tail_width - margin))

    def _redraw_bubble_shell(self):
        """Resize the bubble chrome and redraw chamfered corners plus tail."""
        canvas = getattr(self, "_speech_bubble_canvas", None)
        body = getattr(self, "_speech_bubble_body", None)
        body_window = getattr(self, "_speech_bubble_body_window", None)
        if (
            canvas is None
            or body is None
            or body_window is None
            or not self._has_active_speech_bubble()
        ):
            return
        try:
            body.update_idletasks()
            # Prefer requested size so the bubble can shrink when content is removed
            # (e.g. closing the emoji dropdown). Using winfo_width/height would stick
            # at the previous larger allocation.
            content_w = max(body.winfo_reqwidth(), 1)
            content_h = max(body.winfo_reqheight(), 1)
            inset = self.BUBBLE_CHAMFER + self.BUBBLE_BORDER_WIDTH
            outline_pad = outline_canvas_pad(self.BUBBLE_BORDER_WIDTH)
            panel_w = content_w + (2 * inset)
            panel_h = content_h + (2 * inset) + self.BUBBLE_TAIL_HEIGHT
            canvas.configure(
                width=panel_w + (2 * outline_pad),
                height=panel_h + outline_pad,
            )
            canvas.coords(body_window, inset + outline_pad, inset + outline_pad)
            canvas.itemconfigure(body_window, width=content_w, height=content_h)
            tail_center_x = self._bubble_tail_center_x(panel_w)
            draw_bubble_shell(
                canvas,
                panel_width=panel_w,
                body_height=content_h,
                tail_center_x=tail_center_x,
                bg=self.BUBBLE_BG,
                border=self.BUBBLE_BORDER,
                border_width=self.BUBBLE_BORDER_WIDTH,
                chamfer=self.BUBBLE_CHAMFER,
                tail_height=self.BUBBLE_TAIL_HEIGHT,
                tail_half_width=self.BUBBLE_TAIL_HALF_WIDTH,
                offset_x=outline_pad,
                offset_y=outline_pad,
            )
            canvas.tag_lower("bubble")
            canvas.lift(body_window)
        except tk.TclError:
            pass

    def _update_bubble_tail(self):
        """Redraw bubble chrome so the tail keeps pointing at Kinito."""
        self._redraw_bubble_shell()

    def _bubble_body_parent(self):
        """Return the frame that holds interactive bubble content."""
        body = getattr(self, "_speech_bubble_body", None)
        if body is not None and body.winfo_exists():
            return body
        return None

    def _bind_entry_focus_on_click(self, entry):
        """Ensure clicking the entry always restores keyboard focus."""

        def _focus_entry(_event=None):
            try:
                if entry.winfo_exists() and entry.cget("state") == tk.NORMAL:
                    entry.focus_set()
            except tk.TclError:
                pass

        entry.bind("<Button-1>", _focus_entry, add="+")

    def _focus_bubble_entry(self, *, force=False):
        """Move keyboard focus to the active bubble text field when appropriate."""
        entry = getattr(self, "_speech_bubble_entry", None)
        if entry is None:
            return
        try:
            if not entry.winfo_exists():
                return
            if entry.cget("state") != tk.NORMAL:
                return
            if not force and entry.focus_get() == entry:
                return
            entry.focus_set()
        except tk.TclError:
            pass

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
        button_w, _button_h = measure_chamfered_button(
            parent,
            text=text,
            font=self._bubble_button_font(),
            padx=self.BUBBLE_BTN_PAD_X,
            pady=self.BUBBLE_BTN_PAD_Y,
            chamfer=self.BUBBLE_BTN_CHAMFER,
            border_width=self.BUBBLE_BORDER_WIDTH,
            width=width,
        )
        return button_w

    def create_wrapped_label(self, parent, text):
        """Create a word-wrapped label for bubble text."""
        label = tk.Label(
            parent,
            text=text,
            bg=self.BUBBLE_BG,
            fg=self.BUBBLE_FG,
            font=self._bubble_font(),
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
            # Redraw chrome first so req size includes chamfer + tail.
            self._redraw_bubble_shell()
            bubble.update_idletasks()
            width = max(bubble.winfo_reqwidth(), 1)
            height = max(bubble.winfo_reqheight(), 1)
            if width > 0 and height > 0:
                bubble_x = bubble.winfo_rootx()
                bubble_y = bubble.winfo_rooty()
                try:
                    withdrawn = bubble.state() == "withdrawn"
                except tk.TclError:
                    withdrawn = False
                if withdrawn or bubble_x <= 0 or bubble_y <= 0:
                    bubble.geometry(f"{width}x{height}")
                else:
                    bubble.geometry(f"{width}x{height}+{bubble_x}+{bubble_y}")
        except tk.TclError:
            pass

    def _capture_speech_bubble_drag_offset(self):
        """Remember how far the active bubble sits from Kinito for coupled dragging."""
        if not self._has_active_speech_bubble():
            self._bubble_kinito_offset_x = None
            self._bubble_kinito_offset_y = None
            return

        self.position_speech_bubble()
        kinito_x, kinito_y = self._kinito_screen_position()
        try:
            self._bubble_kinito_offset_x = self.speech_bubble.winfo_rootx() - kinito_x
            self._bubble_kinito_offset_y = self.speech_bubble.winfo_rooty() - kinito_y
        except tk.TclError:
            self._bubble_kinito_offset_x = None
            self._bubble_kinito_offset_y = None

    def _move_speech_bubble_with_kinito(self, kinito_x, kinito_y):
        """Move the speech bubble by the same delta as Kinito while dragging."""
        if not getattr(self, "_speech_bubble_ready", False):
            return
        offset_x = getattr(self, "_bubble_kinito_offset_x", None)
        offset_y = getattr(self, "_bubble_kinito_offset_y", None)
        if offset_x is None or offset_y is None:
            self.position_speech_bubble()
            return

        bubble_w, bubble_h = self._bubble_screen_size()
        bubble_x = int(kinito_x) + int(offset_x)
        bubble_y = int(kinito_y) + int(offset_y)

        min_x, min_y, max_x, max_y = self.get_screen_bounds(bubble_w, bubble_h)
        bubble_x = max(min_x, min(bubble_x, max_x))
        bubble_y = max(min_y, min(bubble_y, max_y))

        self._speech_bubble_last_pos = (bubble_x, bubble_y)
        self.speech_bubble.geometry(f"{bubble_w}x{bubble_h}+{bubble_x}+{bubble_y}")
        self.speech_bubble.lift()
        self.speech_bubble.wm_attributes("-topmost", True)
        self._update_bubble_tail()
        if hasattr(self, "_raise_screen_effect_overlays"):
            self._raise_screen_effect_overlays()

    def _cancel_bubble_close_timer(self):
        """Cancel any scheduled auto-close for the current speech bubble."""
        if getattr(self, "_bubble_close_timer", None) is not None:
            try:
                self.root.after_cancel(self._bubble_close_timer)
            except (tk.TclError, ValueError):
                pass
            self._bubble_close_timer = None

    def _cancel_response_timeout_timer(self):
        """Cancel any scheduled auto-dismiss for an unanswered dialog."""
        if getattr(self, "_response_timeout_timer", None) is not None:
            try:
                self.root.after_cancel(self._response_timeout_timer)
            except (tk.TclError, ValueError):
                pass
            self._response_timeout_timer = None

    def _schedule_response_timeout(self):
        """Close an unanswered button/textbox dialog after RESPONSE_TIMEOUT_MS."""
        self._cancel_response_timeout_timer()
        self._response_timeout_generation = getattr(self, "_response_timeout_generation", 0) + 1
        generation = self._response_timeout_generation
        self._response_timeout_timer = self.root.after(
            self.RESPONSE_TIMEOUT_MS,
            lambda: self._on_response_timeout(generation),
        )

    def _on_response_timeout(self, generation):
        """Dismiss an interactive bubble when the user does not answer in time."""
        self._response_timeout_timer = None
        if generation != getattr(self, "_response_timeout_generation", 0):
            return
        if not self._awaiting_response:
            return
        if not self._has_active_speech_bubble():
            return
        self.close_speech_bubble()

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
            or getattr(self, "_pending_memory_question", None) is not None
            or getattr(self, "_planning_memory_question", False)
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

    def _start_speech_accompaniment(self, file_path, volume=None):
        """Start poem-style background music after any prior speech was interrupted."""
        if not file_path or not hasattr(self, "play_mp3"):
            return
        play_volume = 0.6 if volume is None else volume
        self.play_mp3(file_path, volume=play_volume, speech_accompaniment=True)

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

        if getattr(self, "_tts_sd_active", False):
            if sd is not None:
                try:
                    sd.stop()
                except Exception:
                    pass
            self._tts_sd_active = False

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
        was_active = (
            getattr(self, "talking", False)
            or self._has_active_speech_bubble()
            or getattr(self, "_ai_generating", False)
        )
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
        if was_active and hasattr(self, "stop_speech_accompaniment_music"):
            self.stop_speech_accompaniment_music()

    def _run_pyttsx3_fallback(self, text):
        """Speak *text* via pyttsx3 when balcon is unavailable."""
        if engine is None:
            return False
        try:
            volume = max(0.0, min(1.0, self.get_tts_volume() / 100.0))
            engine.setProperty("volume", volume)
            engine.say(text)
            engine.runAndWait()
            return True
        except Exception:
            return False

    def get_tts_volume(self) -> int:
        """Return the current TTS volume in 0–100."""
        from kinito.settings_store import clamp_tts_volume

        return clamp_tts_volume(getattr(self, "_tts_volume", 100))

    def _play_bubble_sfx(self, file_path: str) -> None:
        """Play a bubble open/close sound scaled to the TTS volume setting."""
        if not hasattr(self, "play_sfx"):
            return
        volume = max(0.0, min(1.0, self.get_tts_volume() / 100.0))
        self.play_sfx(file_path, volume=volume)

    def offer_tts_volume_picker(self) -> None:
        """Ask the user to pick a TTS volume preset."""
        from content import dialogue as dlg

        volume = self.get_tts_volume()
        self.speak(
            dlg.TTS_VOLUME_QUESTION.format(volume=volume),
            45,
            True,
            skip_ai=True,
        )

    def set_tts_volume(self, volume: int) -> None:
        """Set and persist TTS volume, then confirm aloud."""
        from content import dialogue as dlg
        from kinito.settings_store import clamp_tts_volume

        self._tts_volume = clamp_tts_volume(volume)
        if hasattr(self, "_persist_settings"):
            self._persist_settings()
        self.speak(
            dlg.pick_line(dlg.TTS_VOLUME_SET_LINES).format(volume=self._tts_volume),
            skip_ai=True,
        )

    @staticmethod
    def _balcon_command(voice: str, pitch: int, wav_path: str | None = None) -> list[str]:
        """Build a balcon argv that reads speech text from stdin.

        When *wav_path* is set, synthesize to that file instead of speaking.
        balcon ``-v`` is ignored by SAPI4 (TruVoice), so volume is handled
        elsewhere.
        """
        command = [
            balconexe_directory,
            "-n",
            voice,
            "-i",
            "-enc",
            "utf8",
            "-p",
            str(pitch),
        ]
        if wav_path:
            command.extend(["-w", wav_path])
        return command

    @staticmethod
    def _scale_wav_pcm(data: np.ndarray, volume: float) -> np.ndarray:
        """Return PCM samples attenuated by *volume* (0.0–1.0)."""
        if volume >= 1.0:
            return data
        if data.dtype == np.uint8:
            centered = data.astype(np.float32) - 128.0
            scaled = centered * volume + 128.0
            return np.clip(scaled, 0, 255).astype(np.uint8)
        info = np.iinfo(data.dtype)
        scaled = data.astype(np.float32) * volume
        return np.clip(scaled, info.min, info.max).astype(data.dtype)

    @staticmethod
    def _load_wav_pcm(wav_path: str) -> tuple[np.ndarray, int]:
        """Load a WAV file as PCM samples and sample rate."""
        with wave.open(wav_path, "rb") as handle:
            channels = handle.getnchannels()
            sampwidth = handle.getsampwidth()
            rate = handle.getframerate()
            frames = handle.readframes(handle.getnframes())

        dtype_by_width = {1: np.uint8, 2: np.int16, 4: np.int32}
        dtype = dtype_by_width.get(sampwidth)
        if dtype is None:
            raise ValueError(f"Unsupported WAV sample width: {sampwidth}")

        data = np.frombuffer(frames, dtype=dtype)
        if channels > 1:
            data = data.reshape(-1, channels)
        return data, rate

    def _play_tts_wav(self, wav_path: str, speech_epoch=None) -> bool:
        """Play a synthesized WAV at TTS volume via sounddevice (native rate)."""
        if self._tts_interrupted(speech_epoch):
            return False
        if sd is None:
            return False
        if not os.path.isfile(wav_path) or os.path.getsize(wav_path) <= 0:
            return False

        volume = max(0.0, min(1.0, self.get_tts_volume() / 100.0))
        if volume <= 0.0:
            return True

        try:
            data, rate = self._load_wav_pcm(wav_path)
            data = self._scale_wav_pcm(data, volume)
            self._tts_sd_active = True
            sd.play(data, rate)
            while True:
                stream = sd.get_stream()
                if stream is None or not getattr(stream, "active", False):
                    break
                if self._tts_interrupted(speech_epoch):
                    sd.stop()
                    return False
                time.sleep(0.05)
        except Exception:
            return False
        finally:
            self._tts_sd_active = False

        return not self._tts_interrupted(speech_epoch)

    def _run_balcon_process(
        self,
        voice: str,
        text: str,
        pitch: int,
        *,
        wav_path: str | None = None,
        speech_epoch=None,
    ) -> tuple[bool, str]:
        """Run balcon once; return (ok_for_voice, stderr)."""
        try:
            process = subprocess.Popen(
                self._balcon_command(voice, pitch, wav_path=wav_path),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
        except (OSError, subprocess.SubprocessError, ValueError):
            return False, ""

        self._tts_process = process
        try:
            try:
                _stdout, stderr = process.communicate(input=text, timeout=120)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                return False, ""
        finally:
            self._tts_process = None

        if self._tts_interrupted(speech_epoch):
            return False, stderr or ""
        err = (stderr or "").lower()
        if "voice not selected" in err or "voice not found" in err:
            return False, stderr or ""
        return True, stderr or ""

    def _run_balcon_tts(self, voice: str, text: str, pitch: int, speech_epoch=None) -> bool:
        """Speak via balcon, applying software volume only when below 100%.

        Full volume uses balcon's direct output (original TruVoice character).
        Softer presets render to WAV and play at native sample rate so pygame
        does not resample the voice into a hollow/distant sound.
        """
        if self._tts_interrupted(speech_epoch):
            return False

        # Direct speak preserves the classic Kinito voice path.
        if self.get_tts_volume() >= 100:
            ok, _stderr = self._run_balcon_process(
                voice, text, pitch, speech_epoch=speech_epoch
            )
            return ok and not self._tts_interrupted(speech_epoch)

        wav_path = None
        try:
            fd, wav_path = tempfile.mkstemp(suffix=".wav", prefix="kinito_tts_")
            os.close(fd)
            ok, _stderr = self._run_balcon_process(
                voice,
                text,
                pitch,
                wav_path=wav_path,
                speech_epoch=speech_epoch,
            )
            if not ok or self._tts_interrupted(speech_epoch):
                return False
            return self._play_tts_wav(wav_path, speech_epoch=speech_epoch)
        finally:
            if wav_path:
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass

    def _voice_candidate_queue(self, voice_candidates):
        """Yield preferred voices first, then system fallbacks only if needed."""
        preferred = list(voice_candidates or self.VOICE_NORMAL_CANDIDATES)
        seen = set()
        for voice in preferred:
            if voice in seen:
                continue
            seen.add(voice)
            yield voice
        if any(voice in self._available_voices for voice in preferred):
            return
        for voice in self.VOICE_SYSTEM_FALLBACK_CANDIDATES:
            if voice in seen:
                continue
            seen.add(voice)
            yield voice

    def _run_tts(self, text, pitch=45, voice_candidates=None, speech_epoch=None):
        """Run TTS via balcon (preferred) or pyttsx3 fallback."""
        if not getattr(self, "_tts_enabled", True):
            return False
        text = normalize_text_for_tts(text)
        if voice_candidates is None:
            voice_candidates = self.VOICE_NORMAL_CANDIDATES

        self._tts_process = None

        if os.path.isfile(balconexe_directory):
            for voice in self._voice_candidate_queue(voice_candidates):
                if voice not in self._available_voices:
                    continue
                if self._run_balcon_tts(voice, text, pitch, speech_epoch=speech_epoch):
                    return True
                if self._tts_interrupted(speech_epoch):
                    return False

        if self._tts_interrupted(speech_epoch):
            return False
        return self._run_pyttsx3_fallback(text)

    def toggle_tts(self):
        """Enable or disable spoken TTS (speech bubbles still appear)."""
        from content import dialogue as dlg

        self._tts_enabled = not getattr(self, "_tts_enabled", True)
        if hasattr(self, "_persist_settings"):
            self._persist_settings()
        lines = dlg.TTS_ON_LINES if self._tts_enabled else dlg.TTS_OFF_LINES
        self.speak(dlg.pick_line(lines), skip_ai=True)

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
        speech_accompaniment_path=None,
        speech_accompaniment_volume=None,
    ):
        """Speak *text* in a background thread; optionally show and auto-close a bubble."""
        del ai_hint, skip_ai  # handled by LLMMixin when present in the MRO
        if getattr(self, "_focus_mode", False) and not allow_in_focus:
            return
        if show_bubble and not self._may_start_speech(text):
            return
        self.interrupt_speech()
        if hasattr(self, "_stop_roaming"):
            self._stop_roaming()
        epoch = self._speech_epoch
        self._tts_cancelled = False
        self.talking = True
        self._preserve_sprite = preserve_sprite
        self._talk_sprite_mode = self._infer_talk_sprite_mode(text, question=question)
        accompaniment_path = speech_accompaniment_path
        accompaniment_volume = speech_accompaniment_volume

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
                # Start poem music after TTS begins so SAPI4 keeps Eddie's voice.
                music_started = {"value": False}

                def start_music_soon():
                    if music_started["value"] or epoch != self._speech_epoch:
                        return
                    if accompaniment_path:
                        music_started["value"] = True
                        self._start_speech_accompaniment(
                            accompaniment_path, accompaniment_volume
                        )

                if accompaniment_path:
                    self.root.after(350, start_music_soon)
                spoke = self._run_tts(text, pitch, voice_candidates, speech_epoch=epoch)
                if not spoke and getattr(self, "_tts_enabled", True) is False:
                    # Give the user time to read the bubble when voice is muted.
                    time.sleep(min(2.5, 0.35 + 0.045 * max(len(text), 1)))
                if epoch != self._speech_epoch:
                    return
                if hasattr(self, "stop_speech_accompaniment_music"):
                    self.stop_speech_accompaniment_music()
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
        if not self._may_start_speech(text):
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

        self._play_bubble_sfx(starttalk_file_path)
        self.speech_bubble = self._new_speech_bubble_toplevel(text)
        self._speech_bubble_ready = False
        self._speech_bubble_label = None
        self._speech_bubble_text_frame = None
        self._speech_bubble_button_frame = None
        self._speech_bubble_buttons_content_width = 0
        self._speech_bubble_entry = None
        bubble_body = self._create_bubble_shell(self.speech_bubble)

        text_frame = tk.Frame(bubble_body, bg=self.BUBBLE_BG)
        text_frame.pack(fill=tk.X, anchor="w")
        self._speech_bubble_text_frame = text_frame

        label = self.create_wrapped_label(text_frame, text)
        label.pack(fill=tk.X, expand=False, ipadx=self.BUBBLE_PAD_X, ipady=self.BUBBLE_PAD_Y, anchor="w")
        self._speech_bubble_label = label

        spec = find_dialog_spec(text)
        pending = getattr(self, "_pending_memory_question", None)
        needs_response = spec is not None
        if pending is not None and pending.question == text:
            if pending.ui == "yes_no":
                self.show_response_buttons([dlg.BUTTON_YES, dlg.BUTTON_NO])
            else:
                self.show_response_textbox(pending.question)
            needs_response = True
        elif spec:
            apply_dialog_ui(self, spec)

        self._fit_speech_bubble_to_content()
        self._schedule_speech_bubble_position()

        if needs_response:
            self._awaiting_response = True
            self._schedule_response_timeout()

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

            buttons_width = getattr(self, "_speech_bubble_buttons_content_width", 0)
            if buttons_width <= 0 and button_frame is not None and button_frame.winfo_exists():
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
        bubble_body = getattr(self, "_speech_bubble_body", None)
        if bubble_body is None or not bubble_body.winfo_exists():
            return
        if hasattr(self, "speech_bubble") and self.speech_bubble.winfo_exists():
            button_frame = tk.Frame(bubble_body, bg=self.BUBBLE_BG)
            button_frame.pack(fill=tk.X, padx=self.BUBBLE_PAD_X, pady=(0, self.BUBBLE_PAD_Y))
            self._speech_bubble_button_frame = button_frame

            max_row_width = self.get_max_bubble_width() - 20
            show_close = self._response_buttons_need_close(options)
            close_width = (
                self._measure_button_width(button_frame, "×", width=2) + 8 if show_close else 0
            )
            row_wrapper = tk.Frame(button_frame, bg=self.BUBBLE_BG)
            row_wrapper.pack(fill=tk.X, pady=(0, 3))
            row_frame = tk.Frame(row_wrapper, bg=self.BUBBLE_BG)
            row_frame.pack()
            row_width = 0
            widest_row_width = 0

            for option in options:
                btn_width = self._measure_button_width(row_frame, option) + 8
                needs_new_row = (
                    row_width > 0 and row_width + btn_width + close_width > max_row_width
                )
                if needs_new_row:
                    widest_row_width = max(widest_row_width, row_width)
                    row_wrapper = tk.Frame(button_frame, bg=self.BUBBLE_BG)
                    row_wrapper.pack(fill=tk.X, pady=(0, 3))
                    row_frame = tk.Frame(row_wrapper, bg=self.BUBBLE_BG)
                    row_frame.pack()
                    row_width = 0
                option_button = self._create_bubble_button(
                    row_frame,
                    option,
                    lambda response=option: self.handle_response(response),
                )
                option_button.pack(side=tk.LEFT, padx=3)
                row_width += btn_width

            if show_close:
                close_button = self._create_bubble_button(
                    row_frame,
                    "×",
                    self.close_speech_bubble,
                    width=2,
                    padx=4,
                )
                close_button.pack(side=tk.LEFT, padx=3)
                row_width += close_width

            self._speech_bubble_buttons_content_width = max(widest_row_width, row_width)

            self._align_bubble_text_to_buttons()
            self._fit_speech_bubble_to_content()
            self._schedule_speech_bubble_position()

    def _add_textbox_row(self, parent, prompt):
        """Add an Entry + close button row for free-text dialog responses."""
        input_frame = tk.Frame(parent, bg=self.BUBBLE_BG)
        input_frame.pack(ipadx=10, ipady=5, anchor="w")

        entry_width = self.get_entry_char_width(prompt)
        entry = tk.Entry(
            input_frame,
            bg=self.BUBBLE_ENTRY_BG,
            fg=self.BUBBLE_FG,
            insertbackground=self.BUBBLE_FG,
            font=self._bubble_font(),
            width=entry_width,
            relief=tk.SOLID,
            borderwidth=1,
        )
        entry.pack(side=tk.LEFT, ipady=2)
        entry.bind("<Return>", lambda event: self.handle_response(entry.get()))
        self._speech_bubble_entry = entry
        self._bind_entry_focus_on_click(entry)

        close_button = self._create_bubble_button(
            input_frame,
            "×",
            self.close_speech_bubble,
            width=2,
            padx=4,
        )
        close_button.pack(side=tk.LEFT, padx=(5, 0))

        self._focus_bubble_entry(force=True)
        return entry

    def show_response_textbox(self, prompt):
        """Show or extend the bubble with a text entry for the user's answer."""
        body = self._bubble_body_parent()
        if body is not None:
            self._add_textbox_row(body, prompt)
            self._fit_speech_bubble_to_content()
            self._schedule_speech_bubble_position()
            delay = self._speech_bubble_reveal_delay_ms()
            self.root.after(
                delay + delay + 50,
                lambda: self._focus_bubble_entry(force=True),
            )
        else:
            self.speech_bubble = self._new_speech_bubble_toplevel(prompt)
            self._speech_bubble_ready = False
            bubble_body = self._create_bubble_shell(self.speech_bubble)

            label = self.create_wrapped_label(bubble_body, prompt)
            label.pack(ipadx=self.BUBBLE_PAD_X, ipady=self.BUBBLE_PAD_Y, anchor="w")

            self._add_textbox_row(bubble_body, prompt)
            self._fit_speech_bubble_to_content()
            self._schedule_speech_bubble_position()
            delay = self._speech_bubble_reveal_delay_ms()
            self.root.after(
                delay + delay + 50,
                lambda: self._focus_bubble_entry(force=True),
            )

    def handle_response(self, response):
        """Route a button or textbox answer to the matching dialog handler."""
        if getattr(self, "_pending_memory_question", None) is not None:
            self.interrupt_speech()
            self._close_speech_bubble_impl(stop_tts=False, clear_pending=False)
            self._handle_memory_question_response(response)
            return

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

    def _close_speech_bubble_impl(self, *, stop_tts: bool = True, clear_pending: bool = True):
        """Destroy the speech bubble without chat-mode teardown."""
        self._cancel_bubble_close_timer()
        self._response_timeout_generation = getattr(self, "_response_timeout_generation", 0) + 1
        self._cancel_response_timeout_timer()
        self._awaiting_response = False
        if clear_pending and hasattr(self, "_pending_memory_question"):
            self._pending_memory_question = None
        self._preserve_sprite = False
        self._talk_sprite_mode = "talking"
        self._speech_bubble_last_pos = None
        self._speech_bubble_ready = False
        self._speech_bubble_label = None
        self._speech_bubble_text_frame = None
        self._speech_bubble_button_frame = None
        self._speech_bubble_buttons_content_width = 0
        self._speech_bubble_entry = None
        self._speech_bubble_body = None
        self._speech_bubble_canvas = None
        self._speech_bubble_body_window = None
        self._speech_bubble_outer = None
        if stop_tts:
            self._stop_active_tts()
        if self._has_active_speech_bubble():
            self.speech_bubble.destroy()
            self._play_bubble_sfx(stoptalk_file_path)
            self.talking = False

    def _new_speech_bubble_toplevel(self, title):
        """Create a hidden speech-bubble window parked off-screen."""
        # Avoid transient() on an overrideredirect root — Windows relocates the parent.
        pin = getattr(self, "_pin_assistant_screen_position", None)
        pinned = pin() if callable(pin) else None
        bubble = Toplevel(self.root)
        try:
            bubble.withdraw()
        except tk.TclError:
            pass
        bubble.geometry(self.BUBBLE_OFF_SCREEN_GEOMETRY)
        bubble.configure(bg=self.BUBBLE_TRANSPARENT_BG)
        bubble.overrideredirect(True)
        bubble.attributes("-transparentcolor", "white")
        try:
            # Stay invisible until the first full paint finishes.
            bubble.attributes("-alpha", 0.0)
        except tk.TclError:
            pass
        bubble.wm_attributes("-topmost", True)
        bubble.wm_title(title)
        restore = getattr(self, "_restore_assistant_screen_position", None)
        if pinned is not None and callable(restore):
            restore(*pinned)
        return bubble

    def _speech_bubble_reveal_delay_ms(self):
        """Delay before showing a bubble so Kinito's window position is settled."""
        return getattr(self, "STARTUP_REVEAL_DELAY_MS", self.BUBBLE_REVEAL_DELAY_MS)

    def _reveal_speech_bubble(self):
        """Measure layout, pre-paint invisibly, then show beside Kinito."""
        if not self._has_active_speech_bubble():
            return
        # Second scheduled reveal: only re-anchor; never yank off-screen again.
        if getattr(self, "_speech_bubble_ready", False):
            self.position_speech_bubble(force=True)
            return
        if hasattr(self, "_sync_kinito_screen_position"):
            self._sync_kinito_screen_position()
        self._fit_speech_bubble_to_content()
        bubble = self.speech_bubble
        try:
            self.root.update_idletasks()
            bubble.update_idletasks()
            width, height = self._bubble_screen_size()
            try:
                bubble.attributes("-alpha", 0.0)
            except tk.TclError:
                pass
            # First full paint happens off-screen / invisible so Windows
            # transparentcolor windows do not flash black mid-throw.
            bubble.geometry(f"{width}x{height}{self.BUBBLE_OFF_SCREEN_GEOMETRY}")
            bubble.deiconify()
            bubble.update()
            # Re-measure after the first paint; realized sizes can settle then.
            self._fit_speech_bubble_to_content()
            width, height = self._bubble_screen_size()
            bubble.geometry(f"{width}x{height}{self.BUBBLE_OFF_SCREEN_GEOMETRY}")
            bubble.update_idletasks()
            self._speech_bubble_ready = True
            self._speech_bubble_last_pos = None
            self.position_speech_bubble(force=True)
            bubble.update_idletasks()
            try:
                bubble.attributes("-alpha", 1.0)
            except tk.TclError:
                pass
            bubble.lift()
        except tk.TclError:
            self._speech_bubble_ready = False
            return
        if hasattr(self, "_raise_screen_effect_overlays"):
            self._raise_screen_effect_overlays()
        self._focus_bubble_entry(force=True)

    def _schedule_speech_bubble_position(self):
        """Position and reveal the bubble after layout has settled."""
        delay = self._speech_bubble_reveal_delay_ms()
        self.root.after(delay, self._reveal_speech_bubble)
        self.root.after(delay + delay, self._reveal_speech_bubble)

    def position_speech_bubble(self, *, force: bool = False):
        """Place the bubble above Kinito, clamped to screen bounds."""
        if not hasattr(self, "speech_bubble") or not self.speech_bubble.winfo_exists():
            return
        if not force and not getattr(self, "_speech_bubble_ready", False):
            return

        self.root.update_idletasks()
        self.speech_bubble.update_idletasks()

        kinito_x, kinito_y = self._kinito_screen_position()
        kinito_w = self._kinito_screen_width()
        bubble_w, bubble_h = self._bubble_screen_size()

        gap = 12
        bubble_x = kinito_x + (kinito_w // 2) - (bubble_w // 2)
        bubble_y = kinito_y - bubble_h - gap

        min_x, min_y, max_x, max_y = self.get_screen_bounds(bubble_w, bubble_h)
        bubble_x = max(min_x, min(bubble_x, max_x))
        bubble_y = max(min_y, min(bubble_y, max_y))

        new_pos = (bubble_x, bubble_y)
        force_reposition = (
            force
            or getattr(self, "is_dragging", False)
            or getattr(self, "_throwing", False)
            or getattr(self, "moving", False)
        )
        if force_reposition or getattr(self, "_speech_bubble_last_pos", None) != new_pos:
            self._speech_bubble_last_pos = new_pos
            self.speech_bubble.geometry(f"{bubble_w}x{bubble_h}+{bubble_x}+{bubble_y}")
            self.speech_bubble.lift()
            self.speech_bubble.wm_attributes("-topmost", True)
        self._update_bubble_tail()

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
        if hasattr(self, "note_user_attention"):
            self.note_user_attention()
        if hasattr(self, "speech_bubble") and self.speech_bubble.winfo_exists():
            title = self.speech_bubble.wm_title() or ""
            menu_titles = (
                dlg.MENU_PROMPT,
                dlg.MODES_MENU_QUESTION,
                dlg.SETTINGS_MENU_QUESTION,
                dlg.ACTIONS_MENU_QUESTION,
            )
            if any(prompt in title for prompt in menu_titles):
                self.close_speech_bubble()
                return
        self.speak(dlg.MENU_PROMPT, 45, True, allow_in_focus=True)
