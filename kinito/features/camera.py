"""Webcam preview window with occasional commentary lines."""

import random
import threading
import tkinter as tk
from tkinter import Toplevel

from PIL import Image, ImageTk

from content import dialogue as dlg
from content.camera_lines import CAMERA_LINES
from kinito.tk_timers import cancel_after, schedule_after
from kinito.window_icon import apply_window_icon


class CameraMixin:
    """OpenCV-based camera feed in a small Tk window."""

    CAMERA_FRAME_INTERVAL_MS = 33
    CAMERA_SUCCESS_FRAMES_TO_RESTORE = 3
    CAMERA_FAILED_READS_TO_LOST = 30
    CAMERA_INITIAL_SIGNAL_CHECK_MS = 2000
    CAMERA_COMMENT_RETRY_MS = 400
    CAMERA_MIN_WIDTH = 320
    CAMERA_MIN_HEIGHT = 280

    def open_camera(self):
        """Open the default webcam and start the live preview loop."""
        if self._camera_active:
            self._speak_camera_comment(dlg.CAMERA_ALREADY_OPEN_LINES)
            return

        try:
            import cv2
        except ImportError:
            self.speak("I'd love to see you, but you need opencv-python installed first.")
            return

        cap = None
        try:
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap.release()
                cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                self.speak(dlg.pick_line(dlg.CAMERA_ERROR_LINES))
                return

            self._camera_cap = cap
            self._camera_active = True
            self._camera_feed_live = False
            self._camera_success_streak = 0
            self._camera_failed_reads = 0
            self._camera_open_line_spoken = False
            self._camera_last_frame = None
            self._camera_window_size = None
            cap = None

            self._camera_window = Toplevel(self.root)
            self._camera_window.title("Kinito's Camera")
            apply_window_icon(self._camera_window)
            self._camera_window.resizable(True, True)
            self._camera_window.minsize(self.CAMERA_MIN_WIDTH, self.CAMERA_MIN_HEIGHT)
            self._camera_window.protocol("WM_DELETE_WINDOW", self.close_camera)
            self._camera_window.bind("<Configure>", self._on_camera_window_configure, add="+")

            self._camera_label = tk.Label(
                self._camera_window,
                bg="black",
                fg="white",
                text="Waiting for camera...",
            )
            self._camera_label.pack(fill=tk.BOTH, expand=True)

            vroot_x = self.root.winfo_vrootx()
            vroot_y = self.root.winfo_vrooty()
            vroot_w = self.root.winfo_vrootwidth()
            vroot_h = self.root.winfo_vrootheight()
            x = vroot_x + (vroot_w - 660) // 2
            y = vroot_y + (vroot_h - 520) // 2
            self._camera_window.geometry(f"660x520+{x}+{y}")

            self._camera_line_timer = None
            self._camera_frame_timer = None
            self._cancel_camera_initial_check()
            self._camera_initial_check_id = self.root.after(
                self.CAMERA_INITIAL_SIGNAL_CHECK_MS,
                self._check_camera_initial_signal,
            )
            self._update_camera_frame()
        except (OSError, tk.TclError, cv2.error):
            self._camera_active = False
            self._camera_cap = None
            if self._camera_window is not None:
                try:
                    if self._camera_window.winfo_exists():
                        self._camera_window.destroy()
                except tk.TclError:
                    pass
                self._camera_window = None
            self._camera_label = None
            self.speak(dlg.pick_line(dlg.CAMERA_ERROR_LINES))
        finally:
            if cap is not None:
                cap.release()

    def _cancel_camera_frame_timer(self):
        """Cancel the pending camera preview frame update."""
        cancel_after(self.root, self, "_camera_frame_timer")

    def _cancel_camera_comment_retry(self):
        """Cancel a queued camera comment waiting for speech to finish."""
        cancel_after(self.root, self, "_camera_comment_timer")
        self._pending_camera_lines = None

    def _cancel_camera_initial_check(self):
        """Cancel the pending first-frame signal check."""
        timer_id = getattr(self, "_camera_initial_check_id", None)
        if timer_id is not None:
            try:
                self.root.after_cancel(timer_id)
            except (tk.TclError, ValueError):
                pass
            self._camera_initial_check_id = None

    def _speak_camera_comment(self, lines):
        """Speak a camera-related line once Kinito is not mid-dialog."""
        if not self._camera_active and lines is not dlg.CAMERA_CLOSE_LINES:
            return
        self._pending_camera_lines = lines
        self._try_speak_pending_camera_comment()

    def _try_speak_pending_camera_comment(self):
        """Retry camera comments until speech bubbles and TTS are idle."""
        cancel_after(self.root, self, "_camera_comment_timer")
        lines = getattr(self, "_pending_camera_lines", None)
        if lines is None:
            return

        camera_should_speak = self._camera_active or lines is dlg.CAMERA_CLOSE_LINES
        if not camera_should_speak:
            self._pending_camera_lines = None
            return

        if self._is_busy_with_speech():
            schedule_after(
                self.root,
                self,
                "_camera_comment_timer",
                self.CAMERA_COMMENT_RETRY_MS,
                self._try_speak_pending_camera_comment,
            )
            return

        self._pending_camera_lines = None
        threading.Thread(
            target=lambda: self.speak(dlg.pick_line(lines)),
            daemon=True,
        ).start()

    def _on_camera_window_configure(self, event=None):
        """Scale the preview when the camera window is resized."""
        if event is not None and event.widget is not self._camera_window:
            return
        if not self._camera_window or not self._camera_window.winfo_exists():
            return
        size = (self._camera_window.winfo_width(), self._camera_window.winfo_height())
        if size == getattr(self, "_camera_window_size", None):
            return
        self._camera_window_size = size
        self._render_camera_last_frame()

    def _render_camera_last_frame(self):
        """Draw the latest camera frame scaled to the current window size."""
        frame = getattr(self, "_camera_last_frame", None)
        if frame is None or self._camera_label is None:
            return
        if not self._camera_window or not self._camera_window.winfo_exists():
            return
        try:
            self._camera_window.update_idletasks()
            width = max(self._camera_window.winfo_width() - 12, 160)
            height = max(self._camera_window.winfo_height() - 12, 120)
            img = frame.copy()
            img.thumbnail((width, height), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._camera_label.config(image=photo, text="")
            self._camera_label.image = photo
        except (OSError, tk.TclError):
            pass

    def _check_camera_initial_signal(self):
        """Comment if the camera opened but never delivered a picture."""
        self._camera_initial_check_id = None
        if not self._camera_active:
            return
        if self._camera_feed_live or self._camera_open_line_spoken:
            return
        self._camera_open_line_spoken = True
        self._show_camera_no_signal_placeholder()
        self._speak_camera_comment(dlg.CAMERA_NO_SIGNAL_LINES)

    def _show_camera_no_signal_placeholder(self):
        """Show a helpful message when the camera feed is black."""
        if self._camera_label is None:
            return
        try:
            self._camera_label.config(
                image="",
                text="No camera signal\n(Is your camera turned off?)",
                fg="white",
                font=("Arial", 14),
            )
            self._camera_label.image = None
        except tk.TclError:
            pass

    def _on_camera_feed_restored(self):
        """Announce when a live picture appears or returns."""
        self._cancel_camera_initial_check()
        if self._camera_open_line_spoken:
            self._speak_camera_comment(dlg.CAMERA_SIGNAL_RESTORED_LINES)
        else:
            self._camera_open_line_spoken = True
            self._speak_camera_comment(dlg.CAMERA_OPEN_LINES)
            if self._camera_line_timer is None:
                delay_ms = random.randint(15000, 25000)
                self._camera_line_timer = self.root.after(
                    delay_ms,
                    self._schedule_camera_line,
                )

    def _on_camera_feed_lost(self):
        """Announce when the live picture disappears while the window stays open."""
        self._show_camera_no_signal_placeholder()
        self._speak_camera_comment(dlg.CAMERA_SIGNAL_LOST_LINES)

    def _update_camera_frame(self):
        """Read one frame from the camera and schedule the next update (~30 fps)."""
        self._camera_frame_timer = None
        if not self._camera_active or not self._camera_cap:
            return

        try:
            if not self.root.winfo_exists():
                self.close_camera()
                return
        except tk.TclError:
            self.close_camera()
            return

        try:
            import cv2
        except ImportError:
            self.close_camera()
            return

        try:
            ret, frame = self._camera_cap.read()
        except cv2.error:
            self.close_camera()
            return

        if ret and frame is not None and self._camera_label is not None:
            self._camera_failed_reads = 0
            self._camera_success_streak += 1
            was_live = self._camera_feed_live
            if self._camera_success_streak >= self.CAMERA_SUCCESS_FRAMES_TO_RESTORE:
                self._camera_feed_live = True
                if not was_live:
                    self._on_camera_feed_restored()
            try:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.flip(frame, 1)
                self._camera_last_frame = Image.fromarray(frame)
                self._render_camera_last_frame()
            except (OSError, tk.TclError):
                self.close_camera()
                return
        elif self._camera_active:
            self._camera_success_streak = 0
            self._camera_failed_reads += 1
            if (
                self._camera_feed_live
                and self._camera_failed_reads >= self.CAMERA_FAILED_READS_TO_LOST
            ):
                self._camera_feed_live = False
                self._on_camera_feed_lost()

        if self._camera_active:
            schedule_after(
                self.root,
                self,
                "_camera_frame_timer",
                self.CAMERA_FRAME_INTERVAL_MS,
                self._update_camera_frame,
            )

    def _schedule_camera_line(self):
        """Periodically speak a random camera line while the feed is open."""
        self._camera_line_timer = None
        if not self._camera_active:
            return
        if self._camera_feed_live and not self._is_busy_with_speech():
            threading.Thread(target=self.say_random_camera_line, daemon=True).start()
        delay_ms = random.randint(18000, 35000)
        schedule_after(
            self.root,
            self,
            "_camera_line_timer",
            delay_ms,
            self._schedule_camera_line,
        )

    def say_random_camera_line(self):
        """Speak a random line from CAMERA_LINES if the camera feed is live."""
        if self._camera_active and self._camera_feed_live and not self._is_busy_with_speech():
            self.speak(random.choice(CAMERA_LINES))

    def close_camera(self):
        """Release the camera, destroy the window, and speak a closing line."""
        self._cancel_camera_initial_check()
        self._cancel_camera_frame_timer()

        if self._camera_line_timer is not None:
            cancel_after(self.root, self, "_camera_line_timer")

        was_active = self._camera_active
        self._camera_active = False
        self._camera_feed_live = False
        self._camera_success_streak = 0
        self._camera_failed_reads = 0
        self._camera_open_line_spoken = False

        if self._camera_cap is not None:
            try:
                self._camera_cap.release()
            except Exception:
                pass
            self._camera_cap = None

        if self._camera_window is not None:
            try:
                if self._camera_window.winfo_exists():
                    self._camera_window.destroy()
            except tk.TclError:
                pass
            self._camera_window = None
        self._camera_label = None
        self._camera_last_frame = None
        self._camera_window_size = None

        if was_active:
            self._speak_camera_comment(dlg.CAMERA_CLOSE_LINES)
