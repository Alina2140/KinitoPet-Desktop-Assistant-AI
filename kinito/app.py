"""Main floating-assistant window: sprites, lifecycle, pause, and audio playback."""

import os
import random
import sys
import threading
import tkinter as tk

import pygame
from PIL import Image, ImageTk

from content import dialogue as dlg
from content.goodbye_lines import GOODBYE_LINES
from content.startup import STARTUP_LINES
from kinito.assets import (
    balconexe_directory,
    sprite_path_fancy,
    sprite_path_hug,
    sprite_path_hug2,
    sprite_path_idle,
    sprite_path_normal,
    sprite_path_normal_2,
    sprite_path_sleep,
    sprite_path_sleep1,
    sprite_path_sleep2,
    sprite_path_sleep3,
    sprite_path_surf_left,
    sprite_path_surf_right,
    sprite_path_talking,
    sprite_path_talking2,
    sprite_path_thinking,
    sprite_path_thinking2,
)
from kinito.features.browser import BrowserMixin
from kinito.features.camera import CameraMixin
from kinito.features.content import ContentMixin
from kinito.features.games import GamesMixin
from kinito.features.glitch import GlitchMixin
from kinito.features.hug import HugMixin
from kinito.features.music import MusicMixin
from kinito.features.programs import ProgramsMixin
from kinito.movement import MovementMixin
from kinito.speech import SpeechMixin
from kinito.tk_timers import cancel_after, schedule_after
from kinito.window_icon import set_default_window_icon


def _open_sprite(path, fallback_path):
    """Load a sprite image, falling back to *fallback_path* if missing or unreadable."""
    try:
        if os.path.isfile(path):
            return Image.open(path)
    except OSError:
        pass
    if path != fallback_path:
        print(f"Warning: missing sprite {path}, using fallback.", flush=True)
    return Image.open(fallback_path)


class FloatingAssistant(
    SpeechMixin,
    MovementMixin,
    GlitchMixin,
    HugMixin,
    ContentMixin,
    GamesMixin,
    MusicMixin,
    ProgramsMixin,
    CameraMixin,
    BrowserMixin,
):
    """Borderless desktop friend that combines speech, movement, and feature mixins."""

    STARTUP_REVEAL_DELAY_MS = 100
    GOODBYE_QUIT_EXTRA_MS = 1500
    AUTO_WAKE_NAP_SECONDS = (45, 120)
    SCREEN_EDGE_MARGIN = 10
    SCREEN_BOUNDS_WATCH_MS = 750

    def __init__(self, root, image_path=None):
        """Build the window, load sprites, and start background worker threads."""
        self.root = root
        self.is_dragging = False
        self._speech_lock = threading.Lock()
        set_default_window_icon(self.root)
        self.root.overrideredirect(True)
        self.root.attributes("-transparentcolor", "white")

        fallback = sprite_path_normal
        self.img_normal = _open_sprite(sprite_path_normal, fallback)
        self.img_normal_2 = _open_sprite(sprite_path_normal_2, fallback)
        self.img_idle = _open_sprite(sprite_path_idle, fallback)
        self.img_fancy = _open_sprite(sprite_path_fancy, fallback)
        self.img_surf_left = _open_sprite(sprite_path_surf_left, fallback)
        self.img_surf_right = _open_sprite(sprite_path_surf_right, fallback)
        self.img_sleep = _open_sprite(sprite_path_sleep, fallback)
        self.img_sleep1 = _open_sprite(sprite_path_sleep1, fallback)
        self.img_sleep2 = _open_sprite(sprite_path_sleep2, fallback)
        self.img_sleep3 = _open_sprite(sprite_path_sleep3, fallback)
        self.img_talking = _open_sprite(sprite_path_talking, fallback)
        self.img_talking2 = _open_sprite(sprite_path_talking2, fallback)
        self.img_thinking = _open_sprite(sprite_path_thinking, fallback)
        self.img_thinking2 = _open_sprite(sprite_path_thinking2, fallback)
        self.img_hug = _open_sprite(sprite_path_hug, fallback)
        self.img_hug2 = _open_sprite(sprite_path_hug2, fallback)
        self.tk_img_normal = ImageTk.PhotoImage(self.img_normal)
        self.tk_img_normal_2 = ImageTk.PhotoImage(self.img_normal_2)
        self.tk_img_idle = ImageTk.PhotoImage(self.img_idle)
        self.tk_img_fancy = ImageTk.PhotoImage(self.img_fancy)
        self.tk_img_surf_left = ImageTk.PhotoImage(self.img_surf_left)
        self.tk_img_surf_right = ImageTk.PhotoImage(self.img_surf_right)
        self.tk_img_sleep = ImageTk.PhotoImage(self.img_sleep)
        self.tk_img_sleep3 = ImageTk.PhotoImage(self.img_sleep3)
        self.tk_img_sleep2 = ImageTk.PhotoImage(self.img_sleep2)
        self.tk_img_sleep1 = ImageTk.PhotoImage(self.img_sleep1)
        self.tk_img_talking = ImageTk.PhotoImage(self.img_talking)
        self.tk_img_talking2 = ImageTk.PhotoImage(self.img_talking2)
        self.tk_img_thinking = ImageTk.PhotoImage(self.img_thinking)
        self.tk_img_thinking2 = ImageTk.PhotoImage(self.img_thinking2)
        self.tk_img_hug = ImageTk.PhotoImage(self.img_hug)
        self.tk_img_hug2 = ImageTk.PhotoImage(self.img_hug2)

        self.panel = tk.Label(self.root, bg="white")
        self.panel.pack(side="top", fill="both", expand="yes")
        self.change_sprite(self.tk_img_normal)
        self.setup_reminder_countdown_button()

        self.x = 0
        self.y = 0
        self.root.withdraw()
        self.root.after(0, self._place_at_screen_center)
        self.paused = False
        self.talking = False
        self.moving = False
        self.normalclosebubble = True
        self._running = True
        self._workers_started = False
        self._reminder_id = 0
        self._pending_story = None
        self._fancy_mode = False
        self._hug_mode = False
        self._camera_active = False
        self._camera_cap = None
        self._camera_window = None
        self._camera_label = None
        self._camera_line_timer = None
        self._camera_initial_check_id = None
        self._camera_frame_timer = None
        self._camera_feed_live = False
        self._camera_success_streak = 0
        self._camera_failed_reads = 0
        self._camera_open_line_spoken = False
        self._pending_camera_lines = None
        self._camera_comment_timer = None
        self._browser_active = False
        self._browser_process = None
        self._browser_category = None
        self._hug_timer = None
        self._bubble_close_timer = None
        self._speech_epoch = 0
        self._active_bubble_epoch = 0
        self._tts_process = None
        self._awaiting_response = False
        self._startup_complete = False
        self._allow_random_questions = False
        self._screen_effects_enabled = True
        self._focus_mode = False
        self._preserve_sprite = False
        self._talk_sprite_mode = "talking"
        self._surf_facing = "right"
        self._glitch_window = None
        self._glitch_hide_timer = None
        self._glitch_tk_image = None
        self._game_window = None
        self._auto_wake_timer = None
        self._bubble_position_timer = None
        self._screen_bounds_timer = None
        self._sfx_cache = {}
        self._last_virtual_screen_rect = None
        self._number_guess_target = None
        self._number_guess_attempts = 0
        self._available_voices = self._load_available_voices()
        self.root.wm_attributes("-topmost", True)

        self._log_optional_deps()
        self._start_worker_threads()
        self.root.bind("<Destroy>", self._on_destroy)
        self.root.bind("<Button-3>", self.ask_what_todo)

        self.is_dragging = False
        self._drag_moved = False
        self.mouse_click_offset_x = 0
        self.mouse_click_offset_y = 0
        self.setup_mouse_bindings()
        self.root.after(300, self._schedule_startup_line)

    def _log_optional_deps(self):
        """Print availability of optional dependencies (pywebview, opencv, balcon, pyttsx3)."""
        status = {}
        for label, module in (("pywebview", "webview"), ("opencv", "cv2")):
            try:
                __import__(module)
                status[label] = "ok"
            except ImportError:
                status[label] = "missing"
        status["balcon"] = "ok" if os.path.isfile(balconexe_directory) else "missing"
        from kinito.assets import engine as tts_engine

        status["pyttsx3"] = "ok" if tts_engine is not None else "missing"
        print(f"Kinito optional deps: {status}", flush=True)

    def _schedule_startup_line(self):
        """Start the welcome speech in a background thread after a short delay."""
        threading.Thread(target=self._play_startup_line, daemon=True).start()

    def _play_startup_line(self):
        """Speak a random startup line and mark startup as complete."""
        try:
            self.speak(random.choice(STARTUP_LINES))
        finally:
            self._startup_complete = True

    def _can_initiate_spontaneous_speech(self):
        """Return whether Kinito may ask questions or perform idle actions unprompted."""
        return (
            self._startup_complete
            and self._allow_random_questions
            and not getattr(self, "_focus_mode", False)
            and not self.moving
            and not self._is_busy_with_speech()
        )

    def toggle_focus(self):
        """Toggle quiet focus mode: roam and animate only, no speech or features."""
        if self._focus_mode:
            self._focus_mode = False
            self.speak(dlg.pick_line(dlg.FOCUS_OFF_LINES))
            return

        self.interrupt_speech()
        self.close_speech_bubble()
        self.end_hug()
        self.hide_screen_glitch()
        if hasattr(self, "_ensure_single_game_window"):
            self._ensure_single_game_window()
        self.close_camera()
        self.close_browser()
        self.speak(dlg.pick_line(dlg.FOCUS_ON_LINES))
        self._focus_mode = True

    @staticmethod
    def _windows_virtual_screen_rect():
        """Return (x, y, width, height) for the Windows virtual desktop, if available."""
        if sys.platform != "win32":
            return None
        try:
            import ctypes

            user32 = ctypes.windll.user32
            x = user32.GetSystemMetrics(76)  # SM_XVIRTUALSCREEN
            y = user32.GetSystemMetrics(77)  # SM_YVIRTUALSCREEN
            width = user32.GetSystemMetrics(78)  # SM_CXVIRTUALSCREEN
            height = user32.GetSystemMetrics(79)  # SM_CYVIRTUALSCREEN
            if width <= 0 or height <= 0:
                return None
            return x, y, width, height
        except (OSError, AttributeError, ValueError):
            return None

    def _query_virtual_screen_rect(self):
        """Return the combined virtual screen as (x, y, width, height)."""
        rect = self._windows_virtual_screen_rect()
        if rect is not None:
            return rect

        self.root.update_idletasks()
        x = self.root.winfo_vrootx()
        y = self.root.winfo_vrooty()
        width = self.root.winfo_vrootwidth()
        height = self.root.winfo_vrootheight()
        if width > 1 and height > 1:
            return x, y, width, height

        return 0, 0, self.root.winfo_screenwidth(), self.root.winfo_screenheight()

    def get_screen_bounds(self, window_w=None, window_h=None):
        """Return (min_x, min_y, max_x, max_y) for keeping a window on the virtual screen."""
        if window_w is None or window_h is None:
            measured_w, measured_h = self._window_screen_size()
            if window_w is None:
                window_w = measured_w
            if window_h is None:
                window_h = measured_h

        vroot_x, vroot_y, vroot_w, vroot_h = self._query_virtual_screen_rect()
        margin = self.SCREEN_EDGE_MARGIN

        min_x = vroot_x + margin
        min_y = vroot_y + margin
        max_x = vroot_x + vroot_w - window_w - margin
        max_y = vroot_y + vroot_h - window_h - margin
        return (
            min_x,
            min_y,
            max(min_x, max_x),
            max(min_y, max_y),
        )

    def _is_within_screen_bounds(self, x, y, bounds=None):
        """Return True when (*x*, *y*) lies inside the clamped desktop bounds."""
        if bounds is None:
            bounds = self.get_screen_bounds()
        min_x, min_y, max_x, max_y = bounds
        return min_x <= x <= max_x and min_y <= y <= max_y

    def _window_screen_size(self):
        """Measure the assistant window size in screen pixels."""
        self.root.update_idletasks()
        sprite_w = getattr(getattr(self, "img_normal", None), "width", 0)
        sprite_h = getattr(getattr(self, "img_normal", None), "height", 0)
        width = max(
            self.root.winfo_width(),
            self.root.winfo_reqwidth(),
            getattr(self, "panel", self.root).winfo_reqwidth(),
            sprite_w,
            1,
        )
        height = max(
            self.root.winfo_height(),
            self.root.winfo_reqheight(),
            getattr(self, "panel", self.root).winfo_reqheight(),
            sprite_h,
            1,
        )
        return width, height

    def _place_at_screen_center(self):
        """Position the friend at screen center, then reveal after a short delay."""
        if not self._running:
            return
        self.root.update_idletasks()
        self.root.update()
        self.x, self.y = self.center_position_on_screen()
        self.root.geometry(f"+{self.x}+{self.y}")
        self.root.after(self.STARTUP_REVEAL_DELAY_MS, self._reveal_startup_window)

    def _reveal_startup_window(self):
        """Show the assistant after startup positioning has settled."""
        if not self._running:
            return
        try:
            self.root.deiconify()
            self.root.wm_attributes("-topmost", True)
        except tk.TclError:
            pass

    def clamp_position(self, x, y):
        """Clamp *x*/*y* so the assistant stays within screen bounds."""
        min_x, min_y, max_x, max_y = self.get_screen_bounds()
        return max(min_x, min(int(x), max_x)), max(min_y, min(int(y), max_y))

    def _cancel_periodic_timers(self):
        """Stop recurring ``after`` loops (bubble follow, screen watch, camera frames)."""
        for attr in (
            "_bubble_position_timer",
            "_screen_bounds_timer",
            "_camera_frame_timer",
            "_camera_comment_timer",
            "_reminder_tick_timer",
        ):
            cancel_after(self.root, self, attr)

    def ensure_on_screen(self):
        """Reposition the assistant (and bubbles) if it drifted off-screen."""
        if not self._running or self.is_dragging:
            return

        self.root.update_idletasks()
        bounds = self.get_screen_bounds()
        x = self.root.winfo_rootx()
        y = self.root.winfo_rooty()
        if not self._is_within_screen_bounds(x, y, bounds):
            target_x, target_y = x, y
        elif not self._is_within_screen_bounds(
            getattr(self, "x", x),
            getattr(self, "y", y),
            bounds,
        ):
            target_x, target_y = self.x, self.y
        else:
            return

        clamped_x, clamped_y = self.clamp_position(target_x, target_y)
        if clamped_x == x and clamped_y == y:
            self.x, self.y = clamped_x, clamped_y
            return

        self.x, self.y = clamped_x, clamped_y
        self.root.geometry(f"+{clamped_x}+{clamped_y}")
        if self._has_active_speech_bubble():
            self.position_speech_bubble()

    def _watch_screen_geometry(self):
        """Keep Kinito on-screen when monitors are added, removed, or resized."""
        self._screen_bounds_timer = None
        if not getattr(self, "_running", True):
            return
        try:
            if not self.root.winfo_exists():
                return
        except tk.TclError:
            return
        try:
            current = self._query_virtual_screen_rect()
            self._last_virtual_screen_rect = current
            self.ensure_on_screen()
        except tk.TclError:
            pass
        schedule_after(
            self.root,
            self,
            "_screen_bounds_timer",
            self.SCREEN_BOUNDS_WATCH_MS,
            self._watch_screen_geometry,
        )

    def center_position_on_screen(self):
        """Return the top-left position that centers the assistant on screen."""
        min_x, min_y, max_x, max_y = self.get_screen_bounds()
        return (min_x + max_x) // 2, (min_y + max_y) // 2

    def random_position_on_screen(self):
        """Pick a random on-screen position for autonomous movement."""
        min_x, min_y, max_x, max_y = self.get_screen_bounds()
        return random.randint(min_x, max_x), random.randint(min_y, max_y)

    def toggle_pause(self):
        """Switch between sleep (paused) and awake state."""
        if self.paused:
            self.unpause()
        else:
            self.pause()

    def _cancel_auto_wake_timer(self):
        """Cancel a scheduled spontaneous wake-up."""
        if getattr(self, "_auto_wake_timer", None) is not None:
            try:
                self.root.after_cancel(self._auto_wake_timer)
            except (tk.TclError, ValueError):
                pass
            self._auto_wake_timer = None

    def pause(self, *, spontaneous=False):
        """Enter sleep mode with a nap line and sleep sprites."""
        self._cancel_auto_wake_timer()
        self.speak(dlg.pick_line(dlg.PAUSE_LINES))
        self.paused = True
        if spontaneous:
            delay_ms = random.randint(*self.AUTO_WAKE_NAP_SECONDS) * 1000
            self._auto_wake_timer = self.root.after(delay_ms, self._wake_from_spontaneous_nap)

    def _wake_from_spontaneous_nap(self):
        """Wake up after an idle nap if still sleeping."""
        self._auto_wake_timer = None
        if self.paused and self._running:
            self.unpause()

    def unpause(self):
        """Leave sleep mode and restore the normal sprite."""
        self._cancel_auto_wake_timer()
        self.paused = False
        self.change_sprite(self.tk_img_normal)
        self.speak(dlg.pick_line(dlg.UNPAUSE_LINES))

    def show_credits(self):
        """Show attribution for KinitoPET, the template repo, and third-party assets."""
        from content.credits import CREDITS_TEXT

        self.speak(
            CREDITS_TEXT,
            long_bubble=True,
            allow_in_focus=True,
            preserve_sprite=True,
        )

    def say_goodbye(self):
        """Shut down features, speak a farewell, then quit the application."""
        self._running = False
        self._cancel_periodic_timers()
        self._cancel_auto_wake_timer()
        if hasattr(self, "_clear_reminder"):
            self._clear_reminder()
        self.close_camera()
        self.close_browser()
        self._ensure_single_game_window()
        self.end_hug()
        self.hide_screen_glitch()
        line = random.choice(GOODBYE_LINES)

        def run_goodbye():
            self.speak(line, show_bubble=True, wait_for_tts=True)
            delay = self._bubble_close_delay_after_tts(line) + self.GOODBYE_QUIT_EXTRA_MS
            self.root.after(delay, self._quit_app)

        threading.Thread(target=run_goodbye, daemon=True).start()

    def _quit_app(self):
        """Close the speech bubble and destroy the Tk root."""
        self.close_speech_bubble()
        try:
            self.root.quit()
            self.root.destroy()
        except tk.TclError:
            pass

    def _on_destroy(self, event=None):
        """Clean up camera, browser, and love bubble when the root window closes."""
        if event is not None and event.widget is not self.root:
            return
        self._running = False
        self._cancel_periodic_timers()
        self._cancel_auto_wake_timer()
        if hasattr(self, "_cancel_bubble_close_timer"):
            self._cancel_bubble_close_timer()
        if hasattr(self, "_clear_reminder"):
            self._clear_reminder()
        self.close_camera()
        self.close_browser()
        self._ensure_single_game_window()
        self.end_hug()
        self.hide_screen_glitch()

    def _start_worker_threads(self):
        """Start movement, idle animation, and speech-bubble position update loops."""
        if self._workers_started:
            return
        self._workers_started = True
        threading.Thread(target=self.smooth_movement, daemon=True).start()
        threading.Thread(target=self.idle_animation, daemon=True).start()
        schedule_after(
            self.root,
            self,
            "_bubble_position_timer",
            100,
            self._update_speech_bubble_position,
        )
        schedule_after(
            self.root,
            self,
            "_screen_bounds_timer",
            self.SCREEN_BOUNDS_WATCH_MS,
            self._watch_screen_geometry,
        )

    def _ensure_mixer(self):
        """Initialize pygame mixer once with enough channels for music + SFX."""
        if not pygame.mixer.get_init():
            pygame.mixer.init()
            pygame.mixer.set_num_channels(12)

    def stop_background_music(self):
        """Stop any MP3 currently playing on the pygame music channel."""
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except pygame.error:
            pass

    def play_sfx(self, file_path, volume=1.0):
        """Play a short sound effect without interrupting background music."""
        if not os.path.isfile(file_path):
            return
        try:
            self._ensure_mixer()
            if not hasattr(self, "_sfx_cache"):
                self._sfx_cache = {}
            if file_path not in self._sfx_cache:
                self._sfx_cache[file_path] = pygame.mixer.Sound(file_path)
            sound = self._sfx_cache[file_path]
            sound.set_volume(volume)
            sound.play()
        except (OSError, pygame.error):
            pass

    def play_mp3(self, file_path, volume=1.0):
        """Play an MP3 file via pygame mixer; silently skip missing or broken files."""
        if not os.path.isfile(file_path):
            return
        try:
            self._ensure_mixer()
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play()
        except (OSError, pygame.error):
            pass
