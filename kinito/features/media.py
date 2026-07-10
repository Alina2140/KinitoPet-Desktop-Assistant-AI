"""Show allow-listed images and videos in a window beside Kinito."""

import importlib.util
import random
import subprocess
import sys
import threading
import time
import tkinter as tk
import webbrowser
from tkinter import Label, Toplevel

from PIL import Image, ImageTk

from content import dialogue as dlg
from content.media_lines import MEDIA_IMAGE_OPEN_LINES, MEDIA_VIDEO_OPEN_LINES
from content.media_validator import (
    is_allowed_image_path,
    is_allowed_video_path,
    is_allowed_video_url,
    list_allowed_images,
    pick_random_image,
    pick_random_video,
)
from kinito.tk_timers import cancel_after, schedule_after
from kinito.window_icon import apply_window_icon


class MediaMixin:
    """Open user images and allow-listed videos in a side window next to Kinito."""

    MEDIA_WIDTH = 720
    MEDIA_HEIGHT = 540
    MEDIA_MIN_WIDTH = 320
    MEDIA_MIN_HEIGHT = 240
    MEDIA_FRAME_INTERVAL_MS = 33

    def show_random_media(self):
        """Spontaneously show a random allow-listed image or video without asking."""
        if self._media_active or self._is_busy_with_speech():
            return

        options = []
        if list_allowed_images():
            options.append("image")
        if pick_random_video() is not None:
            options.append("video")
        if not options:
            return

        if random.choice(options) == "image":
            self.show_allowed_image(quiet=True)
        else:
            self.show_allowed_video(quiet=True)

    def ask_media_type(self):
        """Prompt the user to choose between a picture and a video."""
        if self._is_busy_with_speech():
            return
        self.speak(dlg.MEDIA_TYPE_QUESTION, 45, True)

    def _get_media_position(self):
        """Compute window coordinates beside Kinito for the media popup."""
        self.root.update_idletasks()
        kinito_x = self.root.winfo_rootx()
        kinito_y = self.root.winfo_rooty()
        kinito_w = max(self.root.winfo_width(), 1)
        gap = 10
        x = kinito_x + kinito_w + gap
        y = kinito_y
        min_x, min_y, max_x, max_y = self.get_screen_bounds(self.MEDIA_WIDTH, self.MEDIA_HEIGHT)
        x = max(min_x, min(int(x), max_x))
        y = max(min_y, min(int(y), max_y))
        return x, y

    def show_allowed_image(self, *, quiet=False):
        """Pick a random user image and display it in a popup window."""
        if self._media_active:
            return

        image_path = pick_random_image()
        if not image_path or not is_allowed_image_path(image_path):
            if not quiet:
                self.speak(dlg.pick_line(dlg.MEDIA_NO_IMAGES_LINES))
            return

        x, y = self._get_media_position()
        intro = random.choice(MEDIA_IMAGE_OPEN_LINES)
        threading.Thread(
            target=self._launch_image,
            args=(image_path, x, y, intro),
            daemon=True,
        ).start()

    def show_allowed_video(self, *, quiet=False):
        """Pick a random local or allow-listed online video and open it."""
        if self._media_active:
            return

        choice = pick_random_video()
        if choice is None:
            if not quiet:
                self.speak(dlg.pick_line(dlg.MEDIA_NO_VIDEOS_LINES))
            return

        kind, item = choice
        x, y = self._get_media_position()
        intro = random.choice(MEDIA_VIDEO_OPEN_LINES)

        if kind == "local":
            if not is_allowed_video_path(item):
                self.speak(dlg.pick_line(dlg.MEDIA_ERROR_LINES))
                return
            threading.Thread(
                target=self._launch_local_video,
                args=(item, x, y, intro),
                daemon=True,
            ).start()
            return

        video = item
        url = video["url"]
        if not is_allowed_video_url(url):
            self.speak(dlg.pick_line(dlg.MEDIA_ERROR_LINES))
            return
        intro = f"{intro} I'm opening {video['title']}!"
        threading.Thread(
            target=self._launch_video_url,
            args=(url, x, y, intro),
            daemon=True,
        ).start()

    def _launch_image(self, image_path, x, y, intro):
        """Speak the intro, then show the image on the main thread."""
        self.speak(intro, show_bubble=True, wait_for_tts=True)
        if not self._running:
            return
        self._media_active = True
        self.root.after(0, lambda: self._open_image_window(image_path, x, y))

    def _open_image_window(self, image_path, x, y):
        """Display an allow-listed image in a resizable popup."""
        try:
            img = Image.open(image_path)
        except OSError:
            self._media_active = False
            self.speak(dlg.pick_line(dlg.MEDIA_ERROR_LINES))
            return

        popup = Toplevel(self.root)
        popup.title("Kinito's Picture")
        apply_window_icon(popup)
        popup.geometry(f"{self.MEDIA_WIDTH}x{self.MEDIA_HEIGHT}+{int(x)}+{int(y)}")
        popup.wm_attributes("-topmost", True)
        popup.minsize(self.MEDIA_MIN_WIDTH, self.MEDIA_MIN_HEIGHT)
        popup.resizable(True, True)

        label = Label(popup, bg="black")
        label.pack(fill=tk.BOTH, expand=True)

        state = {"image": img.copy()}

        def render_image():
            if not popup.winfo_exists():
                return
            try:
                popup.update_idletasks()
                width = max(popup.winfo_width() - 12, 160)
                height = max(popup.winfo_height() - 12, 120)
                frame = state["image"].copy()
                frame.thumbnail((width, height), Image.LANCZOS)
                photo = ImageTk.PhotoImage(frame)
                label.config(image=photo)
                label.image = photo
            except (OSError, tk.TclError):
                pass

        def on_configure(event=None):
            if event is not None and event.widget is not popup:
                return
            render_image()

        popup.bind("<Configure>", on_configure, add="+")
        render_image()

        def handle_close():
            self._finish_media_window()

        popup.protocol("WM_DELETE_WINDOW", handle_close)
        self._media_window = popup
        threading.Thread(target=self._wait_for_media_window_close, daemon=True).start()

    def _launch_local_video(self, video_path, x, y, intro):
        """Speak the intro, then play a local video file."""
        self.speak(intro, show_bubble=True, wait_for_tts=True)
        if not self._running:
            return

        try:
            import cv2
        except ImportError:
            self.speak(
                "I'd love to play a video, but you need opencv-python installed first."
            )
            return

        self._media_active = True
        self.root.after(0, lambda: self._open_local_video_window(video_path, x, y, cv2))

    def _open_local_video_window(self, video_path, x, y, cv2):
        """Play a local video with OpenCV frames in a Tk window."""
        cap = None
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                self._media_active = False
                self.speak(dlg.pick_line(dlg.MEDIA_ERROR_LINES))
                return

            self._media_video_cap = cap
            self._media_frame_timer = None
            self._media_last_frame = None
            self._media_window_size = None

            window = Toplevel(self.root)
            window.title("Kinito's Video")
            apply_window_icon(window)
            window.geometry(f"{self.MEDIA_WIDTH}x{self.MEDIA_HEIGHT}+{int(x)}+{int(y)}")
            window.wm_attributes("-topmost", True)
            window.minsize(self.MEDIA_MIN_WIDTH, self.MEDIA_MIN_HEIGHT)
            window.resizable(True, True)
            window.protocol("WM_DELETE_WINDOW", self.close_media)
            window.bind("<Configure>", self._on_media_window_configure, add="+")

            label = Label(window, bg="black", fg="white", text="Loading video...")
            label.pack(fill=tk.BOTH, expand=True)

            self._media_window = window
            self._media_label = label
            self._update_media_frame(cv2)
            threading.Thread(target=self._wait_for_media_window_close, daemon=True).start()
        except (OSError, tk.TclError, cv2.error):
            self._media_active = False
            self._media_video_cap = None
            if cap is not None:
                cap.release()
            self.speak(dlg.pick_line(dlg.MEDIA_ERROR_LINES))

    def _on_media_window_configure(self, event=None):
        """Scale the video frame when the media window is resized."""
        window = getattr(self, "_media_window", None)
        if event is not None and window is not None and event.widget is not window:
            return
        if not window or not window.winfo_exists():
            return
        size = (window.winfo_width(), window.winfo_height())
        if size == getattr(self, "_media_window_size", None):
            return
        self._media_window_size = size
        self._render_media_last_frame()

    def _render_media_last_frame(self):
        """Draw the latest video frame scaled to the current window size."""
        frame = getattr(self, "_media_last_frame", None)
        label = getattr(self, "_media_label", None)
        window = getattr(self, "_media_window", None)
        if frame is None or label is None or window is None:
            return
        if not window.winfo_exists():
            return
        try:
            window.update_idletasks()
            width = max(window.winfo_width() - 12, 160)
            height = max(window.winfo_height() - 12, 120)
            img = frame.copy()
            img.thumbnail((width, height), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            label.config(image=photo, text="")
            label.image = photo
        except (OSError, tk.TclError):
            pass

    def _update_media_frame(self, cv2):
        """Read one frame from the video file and schedule the next update."""
        self._media_frame_timer = None
        cap = getattr(self, "_media_video_cap", None)
        if not self._media_active or cap is None:
            return

        try:
            if not self.root.winfo_exists():
                self.close_media()
                return
        except tk.TclError:
            self.close_media()
            return

        try:
            ret, frame = cap.read()
        except cv2.error:
            self.close_media()
            return

        if ret and frame is not None and getattr(self, "_media_label", None) is not None:
            try:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self._media_last_frame = Image.fromarray(frame)
                self._render_media_last_frame()
            except (OSError, tk.TclError):
                self.close_media()
                return
        elif self._media_active:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        if self._media_active:
            schedule_after(
                self.root,
                self,
                "_media_frame_timer",
                self.MEDIA_FRAME_INTERVAL_MS,
                lambda: self._update_media_frame(cv2),
            )

    def _has_pywebview(self):
        """Return True if the pywebview package is installed."""
        return importlib.util.find_spec("webview") is not None

    def _launch_video_url(self, url, x, y, intro):
        """Speak the intro, then open an allow-listed video URL."""
        self.speak(intro, show_bubble=True, wait_for_tts=True)
        if not self._running:
            return
        if self._has_pywebview():
            self._start_video_process(url, x, y)
        else:
            if is_allowed_video_url(url):
                webbrowser.open(url)
            else:
                self.speak(dlg.pick_line(dlg.MEDIA_BLOCKED_LINES))

    def _start_video_process(self, url, x, y):
        """Spawn a child process running media_process with the target URL."""
        try:
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "kinito.features.media_process",
                    url,
                    str(x),
                    str(y),
                    str(self.MEDIA_WIDTH),
                    str(self.MEDIA_HEIGHT),
                ],
                stderr=subprocess.PIPE,
                text=True,
            )
        except OSError:
            self._media_active = False
            self._media_process = None
            self.speak(dlg.pick_line(dlg.MEDIA_ERROR_LINES))
            return

        self._media_process = process
        self._media_active = True
        threading.Thread(target=self._wait_for_video_process, daemon=True).start()

    def _wait_for_video_process(self):
        """Wait for the video subprocess and speak a closing line."""
        process = getattr(self, "_media_process", None)
        if process is None:
            return

        stderr = process.stderr.read() if process.stderr is not None else ""
        exit_code = process.wait()
        self._media_active = False
        self._media_process = None

        if not self._running:
            return

        if exit_code != 0:
            if "pywebview not installed" in stderr:
                self.speak(
                    "I'd love to play that video, but I need pywebview installed. "
                    "Try: pip install pywebview"
                )
            else:
                if stderr.strip():
                    print(f"Video process failed: {stderr.strip()}", flush=True)
                self.speak(dlg.pick_line(dlg.MEDIA_ERROR_LINES))
            return

        while self.talking and self._running:
            time.sleep(0.1)
        if self._running:
            self.speak(dlg.pick_line(dlg.MEDIA_CLOSE_LINES))

    def _wait_for_media_window_close(self):
        """Wait until the media window is closed, then speak a closing line."""
        while self._media_active and self._running:
            window = getattr(self, "_media_window", None)
            if window is None:
                break
            try:
                if not window.winfo_exists():
                    break
            except tk.TclError:
                break
            time.sleep(0.2)

        was_active = self._media_active
        self._finish_media_window(speak_close=False)

        if not self._running or not was_active:
            return
        while self.talking and self._running:
            time.sleep(0.1)
        if self._running:
            self.speak(dlg.pick_line(dlg.MEDIA_CLOSE_LINES))

    def _finish_media_window(self, *, speak_close=False):
        """Release media resources and clear active state."""
        cancel_after(self.root, self, "_media_frame_timer")

        cap = getattr(self, "_media_video_cap", None)
        if cap is not None:
            try:
                cap.release()
            except Exception:
                pass
            self._media_video_cap = None

        window = getattr(self, "_media_window", None)
        if window is not None:
            try:
                if window.winfo_exists():
                    window.destroy()
            except tk.TclError:
                pass
        self._media_window = None
        self._media_label = None
        self._media_last_frame = None
        self._media_window_size = None
        self._media_active = False

        if speak_close and self._running:
            self.speak(dlg.pick_line(dlg.MEDIA_CLOSE_LINES))

    def close_media(self):
        """Close any open media window or subprocess."""
        process = getattr(self, "_media_process", None)
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
        self._media_process = None
        self._finish_media_window(speak_close=False)
