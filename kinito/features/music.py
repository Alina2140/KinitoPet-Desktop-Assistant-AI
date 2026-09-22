"""Folder-based MP3 playlist and Kinito's Musik Player window."""

from __future__ import annotations

import os
import random
import tkinter as tk
from tkinter import filedialog

import pygame
from PIL import Image, ImageTk

from content import dialogue as dlg
from content.music_player_lines import MUSIC_PLAYER_LINES
from kinito.assets import (
    favicon_path,
    music_player_list_icon_path,
    music_player_order_icon_path,
    music_player_pause_icon_path,
    music_player_play_icon_path,
    music_player_repeat_all_icon_path,
    music_player_repeat_one_icon_path,
    music_player_shuffle_icon_path,
    music_player_skip_backward_icon_path,
    music_player_skip_forward_icon_path,
    music_player_volume_icon_path,
)
from kinito.settings_store import clamp_music_volume
from kinito.tk_timers import cancel_after, schedule_after
from kinito.window_icon import apply_window_icon


class MusicMixin:
    """Play MP3s from a chosen folder via a dedicated music player window."""

    _MUSIC_POLL_GRACE_TICKS = 2
    _MUSIC_POLL_INTERVAL_MS = 250
    _MUSIC_PROGRESS_TICK_MS = 250
    _MUSIC_PLAYER_WIDTH = 420
    _MUSIC_PLAYER_HEIGHT = 196
    _MUSIC_VOLUME_POPUP_WIDTH = 168
    _MUSIC_VOLUME_POPUP_HEIGHT = 46
    _MUSIC_TRACK_PICKER_WIDTH = 320
    _MUSIC_TRACK_PICKER_HEIGHT = 360
    _MUSIC_LIST_HOVER_BG = "#efe8df"
    _MUSIC_LIST_SELECTED_BG = "#ffff80"
    _MUSIC_UI_BG = "#e6ded5"
    _MUSIC_TITLEBAR_BG = "#d4ccc2"
    _MUSIC_TITLEBAR_HOVER_BG = "#c4bbb0"
    _MUSIC_CLOSE_HOVER_BG = "#e81123"
    _MUSIC_BTN_BG = "#d9d9d9"
    _MUSIC_BTN_HOVER_BG = "#c4c4c4"
    _MUSIC_PROGRESS_BG = "#cfc6bc"
    _MUSIC_PROGRESS_FG = "#6b5e52"
    _MUSIC_REPEAT_ONE = "one"
    _MUSIC_REPEAT_ALL = "all"

    def setup_music_player(self):
        """Initialize music-player state (no on-sprite controls)."""
        self._user_music_path = None
        self._user_music_name = None
        self._user_music_poll_timer = None
        self._user_music_poll_misses = 0
        self._music_playlist: list[str] = []
        self._music_index = 0
        self._music_paused = False
        if not hasattr(self, "_music_shuffle"):
            self._music_shuffle = False
        self._music_repeat_mode = self._MUSIC_REPEAT_ALL
        self._music_player_window = None
        self._music_player_widgets: dict = {}
        self._music_player_photos: dict = {}
        self._music_player_drag = None
        self._music_volume_popup = None
        self._music_volume_outside_bound = False
        self._music_track_picker_window = None
        self._music_track_picker_drag = None
        self._music_track_picker_canvas = None
        self._music_track_picker_buttons: dict = {}
        self._music_track_picker_wheel_bound = False
        self._music_progress_timer = None
        self._music_track_duration = None
        self._music_track_duration_path = None
        self._music_seek_offset = 0.0
        self._music_scrubbing = False
        self._music_scrub_seconds = 0.0
        self._music_was_playing_before_scrub = False
        self._music_progress_updating = False
        if not hasattr(self, "_music_folder"):
            self._music_folder = ""
        if not hasattr(self, "_music_volume"):
            self._music_volume = 75
        if not hasattr(self, "_player_focus_enabled"):
            self._player_focus_enabled = True

    def _is_music_player_open(self) -> bool:
        """Return True while the music player window exists (including minimized)."""
        window = getattr(self, "_music_player_window", None)
        if window is None:
            return False
        try:
            return bool(window.winfo_exists())
        except tk.TclError:
            return False

    def _is_music_player_minimized(self) -> bool:
        """Return True when the player exists but is hidden via minimize."""
        window = getattr(self, "_music_player_window", None)
        if window is None:
            return False
        try:
            return bool(window.winfo_exists()) and str(window.state()) == "withdrawn"
        except tk.TclError:
            return False

    def _player_focus_active(self) -> bool:
        """True when Player Focus is enabled and the music player is open."""
        if not getattr(self, "_player_focus_enabled", True):
            return False
        return self._is_music_player_open()

    def _silence_for_player_focus(self) -> None:
        """Stop talking when Player Focus applies to the open player."""
        if not self._player_focus_active():
            return
        interrupt = getattr(self, "interrupt_speech", None)
        if callable(interrupt):
            interrupt()

    def toggle_player_focus(self):
        """Enable or disable quiet mode while the music player is open."""
        self._player_focus_enabled = not getattr(self, "_player_focus_enabled", True)
        if hasattr(self, "_persist_settings"):
            self._persist_settings()
        if self._player_focus_active():
            self._silence_for_player_focus()
        lines = (
            dlg.PLAYER_FOCUS_ON_LINES
            if self._player_focus_enabled
            else dlg.PLAYER_FOCUS_OFF_LINES
        )
        self.speak(dlg.pick_line(lines), skip_ai=True, allow_in_focus=True)

    def ask_music_player_pick(self):
        """Open the music player (menu entry compatibility)."""
        self.open_music_player()

    def offer_random_music(self):
        """Ask the user before opening the music player."""
        if self._is_busy_with_speech():
            return
        self.speak(dlg.pick_line(dlg.MUSIC_PLAYER_QUESTIONS), 45, True)

    def open_music_player(self):
        """Ensure a music folder, load the playlist, and show the player window."""
        if not self._ensure_music_folder(prompt=True):
            return
        if not self._reload_music_playlist():
            self.speak(dlg.pick_line(dlg.MUSIC_PLAYER_NOT_FOUND_LINES))
            return
        self._show_music_player_window()
        if not self._user_music_is_active() and not self._music_paused:
            self._play_playlist_index(self._music_index, announce=True)

    def choose_music_folder(self):
        """Let the user pick a new playlist folder (Settings or first open)."""
        initial = self._music_folder if os.path.isdir(self._music_folder or "") else (
            os.path.join(os.path.expanduser("~"), "Music")
        )
        if not os.path.isdir(initial):
            initial = os.path.expanduser("~")
        folder = filedialog.askdirectory(
            parent=self.root,
            title="Choose a music folder for Kinito",
            initialdir=initial,
        )
        if not folder:
            return False
        self._music_folder = folder
        if hasattr(self, "_persist_settings"):
            self._persist_settings()
        if not self._reload_music_playlist():
            self.speak(dlg.pick_line(dlg.MUSIC_PLAYER_NOT_FOUND_LINES))
            self._refresh_music_player_ui()
            return False
        # New folder: always start from the top of the active queue order.
        self._music_index = 0
        if getattr(self, "_music_shuffle", False):
            self._reshuffle_playlist_from_current()
        self._refresh_music_player_ui()
        if getattr(self, "_music_player_window", None) is not None:
            self._play_playlist_index(0, announce=True)
        return True

    def _ensure_music_folder(self, *, prompt: bool) -> bool:
        """Return True when a valid music folder is available."""
        folder = getattr(self, "_music_folder", "") or ""
        if folder and os.path.isdir(folder):
            return True
        if not prompt:
            return False
        return bool(self.choose_music_folder())

    def _reload_music_playlist(self) -> bool:
        """Scan the music folder and build the active playlist (shuffled if enabled)."""
        folder = getattr(self, "_music_folder", "") or ""
        files = self._list_folder_mp3s(folder)
        self._music_playlist = files
        if not files:
            self._music_index = 0
            return False
        if self._music_index >= len(files):
            self._music_index = 0
        current = getattr(self, "_user_music_path", None)
        if current in files:
            self._music_index = files.index(current)
        if getattr(self, "_music_shuffle", False):
            self._reshuffle_playlist_from_current()
        return True

    @staticmethod
    def _list_folder_mp3s(folder: str) -> list[str]:
        """Return alphabetically sorted MP3 paths directly inside *folder*."""
        if not folder or not os.path.isdir(folder):
            return []
        files = []
        try:
            names = os.listdir(folder)
        except OSError:
            return []
        for name in names:
            if not name.lower().endswith(".mp3"):
                continue
            path = os.path.join(folder, name)
            if os.path.isfile(path):
                files.append(path)
        files.sort(key=lambda path: os.path.basename(path).casefold())
        return files

    def _music_volume_fraction(self) -> float:
        """Return the current music volume as 0.0–1.0 for pygame."""
        return clamp_music_volume(getattr(self, "_music_volume", 75)) / 100.0

    def _user_music_is_active(self) -> bool:
        """Return True while a user-selected song is playing (not paused-stopped)."""
        if not getattr(self, "_user_music_path", None):
            return False
        if getattr(self, "_music_paused", False):
            return True
        return bool(self._is_background_music_playing())

    def _begin_user_music(self, file_path: str) -> None:
        """Track the current user song and start end-of-track polling."""
        self._user_music_path = file_path
        self._user_music_name = os.path.splitext(os.path.basename(file_path))[0]
        self._user_music_poll_misses = 0
        self._music_paused = False
        self._music_track_duration_path = file_path
        self._music_track_duration = self._probe_track_duration(file_path)
        self._music_seek_offset = 0.0
        self._music_scrubbing = False
        self._music_scrub_seconds = 0.0
        self._music_was_playing_before_scrub = False
        if file_path in getattr(self, "_music_playlist", []):
            self._music_index = self._music_playlist.index(file_path)
        self._refresh_music_player_ui()
        self._schedule_user_music_poll()
        self._schedule_music_progress_tick()

    def _on_background_music_stopped(self) -> None:
        """Clear user-music playback state after an external stop."""
        self._user_music_path = None
        self._user_music_name = None
        self._user_music_poll_misses = 0
        self._music_paused = False
        self._music_track_duration = None
        self._music_track_duration_path = None
        self._music_seek_offset = 0.0
        self._music_scrubbing = False
        self._music_scrub_seconds = 0.0
        self._music_was_playing_before_scrub = False
        cancel_after(self.root, self, "_user_music_poll_timer")
        cancel_after(self.root, self, "_music_progress_timer")
        self._refresh_music_player_ui()

    def _on_user_track_finished(self) -> None:
        """Advance according to repeat/shuffle mode when a track ends."""
        playlist = getattr(self, "_music_playlist", [])
        if not playlist:
            self._music_paused = False
            cancel_after(self.root, self, "_user_music_poll_timer")
            self._refresh_music_player_ui()
            return
        if getattr(self, "_music_repeat_mode", self._MUSIC_REPEAT_ALL) == self._MUSIC_REPEAT_ONE:
            self._play_playlist_index(int(getattr(self, "_music_index", 0)), announce=False)
            return
        next_index = self._resolve_next_track_index(wrap=True)
        if next_index is None:
            self._music_paused = False
            cancel_after(self.root, self, "_user_music_poll_timer")
            self._refresh_music_player_ui()
            return
        self._play_playlist_index(next_index, announce=False)

    def _pick_shuffle_index(self) -> int | None:
        """Return a random playlist index, preferring a different track."""
        playlist = getattr(self, "_music_playlist", [])
        if not playlist:
            return None
        if len(playlist) == 1:
            return 0
        current = int(getattr(self, "_music_index", 0))
        choices = [i for i in range(len(playlist)) if i != current]
        return random.choice(choices)

    def _resolve_next_track_index(self, *, wrap: bool) -> int | None:
        """Pick the next index for auto-advance or the next button."""
        playlist = getattr(self, "_music_playlist", [])
        if not playlist:
            return None
        if getattr(self, "_music_shuffle", False):
            return self._pick_shuffle_index()
        index = int(getattr(self, "_music_index", 0)) + 1
        if index >= len(playlist):
            return 0 if wrap else None
        return index

    def _resolve_previous_track_index(self) -> int | None:
        """Pick the previous index for the previous button."""
        playlist = getattr(self, "_music_playlist", [])
        if not playlist:
            return None
        if getattr(self, "_music_shuffle", False):
            return self._pick_shuffle_index()
        index = int(getattr(self, "_music_index", 0)) - 1
        if index < 0:
            return len(playlist) - 1
        return index

    def _schedule_user_music_poll(self):
        """Poll pygame until the current user song finishes."""
        cancel_after(self.root, self, "_user_music_poll_timer")
        if not getattr(self, "_running", True):
            return
        if not getattr(self, "_user_music_path", None):
            return
        try:
            if not self.root.winfo_exists():
                return
        except tk.TclError:
            return

        if getattr(self, "_music_paused", False) or getattr(
            self, "_music_scrubbing", False
        ):
            self._user_music_poll_misses = 0
            schedule_after(
                self.root,
                self,
                "_user_music_poll_timer",
                self._MUSIC_POLL_INTERVAL_MS,
                self._user_music_poll,
            )
            return

        if not self._is_background_music_playing():
            misses = getattr(self, "_user_music_poll_misses", 0) + 1
            self._user_music_poll_misses = misses
            if misses >= self._MUSIC_POLL_GRACE_TICKS:
                self._on_user_track_finished()
            else:
                schedule_after(
                    self.root,
                    self,
                    "_user_music_poll_timer",
                    self._MUSIC_POLL_INTERVAL_MS,
                    self._user_music_poll,
                )
            return

        self._user_music_poll_misses = 0
        schedule_after(
            self.root,
            self,
            "_user_music_poll_timer",
            self._MUSIC_POLL_INTERVAL_MS,
            self._user_music_poll,
        )

    def _user_music_poll(self):
        """Single music poll tick; reschedule while playback continues."""
        self._user_music_poll_timer = None
        self._schedule_user_music_poll()

    def stop_user_music(self):
        """Stop the current user-selected song."""
        if not getattr(self, "_user_music_path", None):
            return
        self.stop_background_music()
        self.speak(dlg.pick_line(dlg.MUSIC_STOPPED_LINES))

    def toggle_music_playback(self):
        """Pause or resume the current track, or start it when stopped."""
        if getattr(self, "_music_paused", False):
            self._unpause_user_music()
            return
        if self._is_background_music_playing() and getattr(self, "_user_music_path", None):
            self._pause_user_music()
            return
        playlist = getattr(self, "_music_playlist", [])
        if not playlist:
            if not self._ensure_music_folder(prompt=True):
                return
            if not self._reload_music_playlist():
                self.speak(dlg.pick_line(dlg.MUSIC_PLAYER_NOT_FOUND_LINES))
                return
            playlist = self._music_playlist
        self._play_playlist_index(self._music_index, announce=False)

    def play_previous_track(self):
        """Play the previous track (or a random one when shuffle is on)."""
        index = self._resolve_previous_track_index()
        if index is None:
            return
        self._play_playlist_index(index, announce=False)

    def play_next_track(self):
        """Play the next track (or a random one when shuffle is on)."""
        index = self._resolve_next_track_index(wrap=True)
        if index is None:
            return
        self._play_playlist_index(index, announce=False)

    def toggle_music_shuffle(self):
        """Toggle shuffle: reshuffle queue with current track first, or restore A–Z order."""
        enabling = not bool(getattr(self, "_music_shuffle", False))
        self._music_shuffle = enabling
        if enabling:
            self._reshuffle_playlist_from_current()
        else:
            self._restore_sorted_playlist()
        if hasattr(self, "_persist_settings"):
            self._persist_settings()
        self._refresh_music_player_ui()

    def _current_playlist_path(self) -> str | None:
        """Return the path of the current/selected track, if any."""
        path = getattr(self, "_user_music_path", None)
        playlist = getattr(self, "_music_playlist", [])
        if path in playlist:
            return path
        index = int(getattr(self, "_music_index", 0))
        if playlist and 0 <= index < len(playlist):
            return playlist[index]
        return None

    def _reshuffle_playlist_from_current(self) -> None:
        """Put the current track first and shuffle the rest of the queue."""
        playlist = list(getattr(self, "_music_playlist", []))
        if not playlist:
            self._music_index = 0
            return
        current = self._current_playlist_path() or playlist[0]
        rest = [path for path in playlist if path != current]
        random.shuffle(rest)
        self._music_playlist = [current] + rest
        self._music_index = 0

    def _restore_sorted_playlist(self) -> None:
        """Restore alphabetical folder order and keep the current track selected."""
        current = self._current_playlist_path()
        folder = getattr(self, "_music_folder", "") or ""
        files = self._list_folder_mp3s(folder)
        if not files:
            files = sorted(
                getattr(self, "_music_playlist", []),
                key=lambda path: os.path.basename(path).casefold(),
            )
        self._music_playlist = files
        if current in files:
            self._music_index = files.index(current)
        else:
            self._music_index = 0

    def toggle_music_repeat(self):
        """Toggle between repeating one track and the whole playlist."""
        mode = getattr(self, "_music_repeat_mode", self._MUSIC_REPEAT_ALL)
        self._music_repeat_mode = (
            self._MUSIC_REPEAT_ONE
            if mode == self._MUSIC_REPEAT_ALL
            else self._MUSIC_REPEAT_ALL
        )
        self._refresh_music_player_ui()

    def set_music_volume(self, volume: int | float) -> None:
        """Set and persist music volume (0–100), applying it to the mixer."""
        self._music_volume = clamp_music_volume(volume)
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.set_volume(self._music_volume_fraction())
        except pygame.error:
            pass
        if hasattr(self, "_persist_settings"):
            self._persist_settings()
        widgets = getattr(self, "_music_player_widgets", {})
        scale = widgets.get("volume")
        if scale is not None:
            try:
                if int(float(scale.get())) != self._music_volume:
                    scale.set(self._music_volume)
            except tk.TclError:
                pass

    def toggle_music_volume_popup(self):
        """Show or hide the compact volume slider popup."""
        if self._is_music_volume_popup_open():
            self._close_music_volume_popup()
            return
        self._show_music_volume_popup()

    def _is_music_volume_popup_open(self) -> bool:
        """Return True while the volume popup exists."""
        popup = getattr(self, "_music_volume_popup", None)
        if popup is None:
            return False
        try:
            return bool(popup.winfo_exists())
        except tk.TclError:
            return False

    def _show_music_volume_popup(self):
        """Open a small volume slider anchored above the speaker button."""
        if not self._is_music_player_open() or self._is_music_player_minimized():
            return
        self._close_music_volume_popup()
        self._close_music_track_picker()
        player = self._music_player_window
        widgets = getattr(self, "_music_player_widgets", {})
        anchor = widgets.get("volume_btn")
        if player is None or anchor is None:
            return

        popup = tk.Toplevel(player)
        self._music_volume_popup = popup
        popup.overrideredirect(True)
        popup.wm_attributes("-topmost", True)
        popup.configure(bg="#111111")
        popup.geometry(
            f"{self._MUSIC_VOLUME_POPUP_WIDTH}x{self._MUSIC_VOLUME_POPUP_HEIGHT}"
        )

        inner = tk.Frame(popup, bg=self._MUSIC_UI_BG, padx=6, pady=2)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        current_volume = clamp_music_volume(getattr(self, "_music_volume", 75))
        scale = tk.Scale(
            inner,
            from_=0,
            to=100,
            orient="horizontal",
            showvalue=True,
            length=140,
            bg=self._MUSIC_UI_BG,
            highlightthickness=0,
            troughcolor="#cfc6bc",
            cursor="hand2",
        )
        # Set before binding command so the Scale's initial 0 does not persist.
        scale.set(current_volume)
        scale.configure(command=lambda value: self.set_music_volume(value))
        scale.pack(fill="x")
        widgets["volume"] = scale

        try:
            player.update_idletasks()
            anchor.update_idletasks()
            popup.update_idletasks()
            ax = int(anchor.winfo_rootx())
            ay = int(anchor.winfo_rooty())
            aw = int(anchor.winfo_width())
            pw = self._MUSIC_VOLUME_POPUP_WIDTH
            ph = self._MUSIC_VOLUME_POPUP_HEIGHT
            x = ax + (aw // 2) - (pw // 2)
            y = ay - ph - 4
            popup.geometry(f"{pw}x{ph}+{x}+{y}")
        except tk.TclError:
            pass
        self._arm_music_volume_outside_close()

    def _arm_music_volume_outside_close(self) -> None:
        """Listen for outside clicks so the volume popup can dismiss."""
        if getattr(self, "_music_volume_outside_bound", False):
            return
        root = getattr(self, "root", None)
        if root is None:
            return
        try:
            root.bind_all(
                "<ButtonPress-1>",
                self._on_music_volume_outside_click,
                add="+",
            )
            self._music_volume_outside_bound = True
        except tk.TclError:
            pass

    @staticmethod
    def _pointer_inside_widget(widget, x_root: int, y_root: int) -> bool:
        """Return True when screen point (*x_root*, *y_root*) lies on *widget*."""
        try:
            left = int(widget.winfo_rootx())
            top = int(widget.winfo_rooty())
            right = left + int(widget.winfo_width())
            bottom = top + int(widget.winfo_height())
        except (tk.TclError, TypeError, ValueError):
            return False
        return left <= int(x_root) < right and top <= int(y_root) < bottom

    def _on_music_volume_outside_click(self, event) -> None:
        """Close the volume popup when the user clicks outside it."""
        if not self._is_music_volume_popup_open():
            return
        popup = getattr(self, "_music_volume_popup", None)
        widgets = getattr(self, "_music_player_widgets", {})
        volume_btn = widgets.get("volume_btn")
        try:
            x_root = int(event.x_root)
            y_root = int(event.y_root)
        except (TypeError, ValueError, AttributeError):
            return
        if popup is not None and self._pointer_inside_widget(popup, x_root, y_root):
            return
        if volume_btn is not None and self._pointer_inside_widget(
            volume_btn, x_root, y_root
        ):
            return
        self._close_music_volume_popup()

    def _close_music_volume_popup(self):
        """Destroy the volume popup if it is open."""
        popup = getattr(self, "_music_volume_popup", None)
        widgets = getattr(self, "_music_player_widgets", {})
        if "volume" in widgets:
            widgets.pop("volume", None)
        self._music_volume_popup = None
        if popup is None:
            return
        try:
            popup.destroy()
        except tk.TclError:
            pass

    def toggle_music_track_picker(self):
        """Show or hide the scrollable track picker popup."""
        if self._is_music_track_picker_open():
            self._close_music_track_picker()
            return
        self._show_music_track_picker()

    def _is_music_track_picker_open(self) -> bool:
        """Return True while the track picker window exists."""
        window = getattr(self, "_music_track_picker_window", None)
        if window is None:
            return False
        try:
            return bool(window.winfo_exists())
        except tk.TclError:
            return False

    def _show_music_track_picker(self):
        """Open a scrollable list of playlist tracks by display name."""
        if not self._is_music_player_open() or self._is_music_player_minimized():
            return
        self._close_music_volume_popup()
        self._close_music_track_picker()

        playlist = list(getattr(self, "_music_playlist", []))
        if not playlist:
            return

        parent = self._music_player_window or self.root
        window = tk.Toplevel(parent)
        self._music_track_picker_window = window
        window.title("Choose a song")
        apply_window_icon(window)
        window.wm_attributes("-topmost", True)
        window.overrideredirect(True)
        window.configure(bg=self._MUSIC_UI_BG)
        window.geometry(
            f"{self._MUSIC_TRACK_PICKER_WIDTH}x{self._MUSIC_TRACK_PICKER_HEIGHT}"
        )
        self._center_music_track_picker(window)

        titlebar = tk.Frame(window, bg=self._MUSIC_TITLEBAR_BG, height=28)
        titlebar.pack(fill="x", side="top")
        titlebar.pack_propagate(False)
        title_label = tk.Label(
            titlebar,
            text="Choose a song",
            bg=self._MUSIC_TITLEBAR_BG,
            fg="#111111",
            font=("Segoe UI", 10, "bold"),
        )
        title_label.pack(side="left", padx=10)
        close_btn = tk.Button(
            titlebar,
            text="✕",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            bd=0,
            padx=8,
            pady=0,
            bg=self._MUSIC_TITLEBAR_BG,
            fg="#111111",
            activebackground=self._MUSIC_CLOSE_HOVER_BG,
            activeforeground="#ffffff",
            cursor="hand2",
            command=self._close_music_track_picker,
        )
        close_btn.pack(side="right", padx=(0, 4), pady=2)
        self._bind_music_player_button_hover(
            close_btn,
            self._MUSIC_TITLEBAR_BG,
            self._MUSIC_CLOSE_HOVER_BG,
            normal_fg="#111111",
            hover_fg="#ffffff",
        )
        for widget in (titlebar, title_label):
            widget.bind("<ButtonPress-1>", self._start_music_track_picker_drag)
            widget.bind("<B1-Motion>", self._drag_music_track_picker)

        body = tk.Frame(window, bg=self._MUSIC_UI_BG)
        body.pack(fill="both", expand=True, padx=8, pady=(6, 8))

        canvas = tk.Canvas(body, bg=self._MUSIC_UI_BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(body, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        list_frame = tk.Frame(canvas, bg=self._MUSIC_UI_BG)
        inner_id = canvas.create_window((0, 0), window=list_frame, anchor="nw")

        def _on_list_configure(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_configure(event):
            canvas.itemconfigure(inner_id, width=event.width)

        list_frame.bind("<Configure>", _on_list_configure)
        canvas.bind("<Configure>", _on_canvas_configure)
        self._music_track_picker_canvas = canvas
        self._arm_music_track_picker_wheel()

        buttons: dict[str, tk.Button] = {}
        current_path = self._current_playlist_path()
        for path in playlist:
            name = os.path.splitext(os.path.basename(path))[0] or os.path.basename(path)
            is_current = path == current_path
            normal_bg = (
                self._MUSIC_LIST_SELECTED_BG if is_current else self._MUSIC_UI_BG
            )
            btn = tk.Button(
                list_frame,
                text=name,
                anchor="w",
                justify="left",
                relief=tk.FLAT,
                bd=0,
                padx=8,
                pady=6,
                bg=normal_bg,
                activebackground=self._MUSIC_LIST_HOVER_BG,
                fg="#111111",
                font=("Segoe UI", 9),
                cursor="hand2",
                command=lambda p=path: self._pick_music_track(p),
            )
            btn._kinito_normal_bg = normal_bg  # noqa: SLF001
            btn.pack(fill="x", pady=1)
            self._bind_music_list_item_hover(btn)
            buttons[path] = btn
        self._music_track_picker_buttons = buttons

        window.protocol("WM_DELETE_WINDOW", self._close_music_track_picker)

    def _bind_music_list_item_hover(self, button: tk.Button) -> None:
        """Hover styling that follows the item's current normal/selected background."""

        def _enter(_event=None):
            try:
                button.configure(bg=self._MUSIC_LIST_HOVER_BG)
            except tk.TclError:
                pass

        def _leave(_event=None):
            try:
                button.configure(
                    bg=getattr(button, "_kinito_normal_bg", self._MUSIC_UI_BG)
                )
            except tk.TclError:
                pass

        button.bind("<Enter>", _enter)
        button.bind("<Leave>", _leave)

    def _refresh_music_track_picker_selection(self) -> None:
        """Update only the yellow highlight for the current track; keep scroll position."""
        buttons = getattr(self, "_music_track_picker_buttons", {})
        if not buttons or not self._is_music_track_picker_open():
            return
        current_path = self._current_playlist_path()
        for path, button in buttons.items():
            normal_bg = (
                self._MUSIC_LIST_SELECTED_BG
                if path == current_path
                else self._MUSIC_UI_BG
            )
            try:
                button._kinito_normal_bg = normal_bg  # noqa: SLF001
                # Avoid fighting an active hover tint on the hovered row.
                if str(button.cget("bg")) != self._MUSIC_LIST_HOVER_BG:
                    button.configure(bg=normal_bg)
            except tk.TclError:
                pass

    def _arm_music_track_picker_wheel(self) -> None:
        """Bind mouse-wheel scrolling for the track picker once."""
        if getattr(self, "_music_track_picker_wheel_bound", False):
            return
        root = getattr(self, "root", None)
        if root is None:
            return
        try:
            root.bind_all(
                "<MouseWheel>",
                self._on_music_track_picker_wheel,
                add="+",
            )
            self._music_track_picker_wheel_bound = True
        except tk.TclError:
            pass

    def _on_music_track_picker_wheel(self, event) -> None:
        """Scroll the track picker when it is open."""
        if not self._is_music_track_picker_open():
            return
        canvas = getattr(self, "_music_track_picker_canvas", None)
        if canvas is None:
            return
        try:
            canvas.yview_scroll(int(-event.delta / 120), "units")
        except (tk.TclError, TypeError, ValueError):
            pass

    def _center_music_track_picker(self, window: tk.Toplevel) -> None:
        """Place the track picker near the center of the primary monitor."""
        try:
            self.root.update_idletasks()
            x, y = self._centered_origin_on_primary(
                self._MUSIC_TRACK_PICKER_WIDTH,
                self._MUSIC_TRACK_PICKER_HEIGHT,
            )
        except (tk.TclError, AttributeError):
            return
        window.geometry(
            f"{self._MUSIC_TRACK_PICKER_WIDTH}x{self._MUSIC_TRACK_PICKER_HEIGHT}"
            f"+{int(x)}+{int(y)}"
        )

    def _start_music_track_picker_drag(self, event):
        """Remember pointer offset when dragging the track picker title bar."""
        window = getattr(self, "_music_track_picker_window", None)
        if window is None:
            return
        self._music_track_picker_drag = (
            event.x_root - window.winfo_x(),
            event.y_root - window.winfo_y(),
        )

    def _drag_music_track_picker(self, event):
        """Move the borderless track picker with its title bar."""
        window = getattr(self, "_music_track_picker_window", None)
        drag = getattr(self, "_music_track_picker_drag", None)
        if window is None or drag is None:
            return
        x = event.x_root - drag[0]
        y = event.y_root - drag[1]
        try:
            window.geometry(f"+{int(x)}+{int(y)}")
        except tk.TclError:
            pass

    def _pick_music_track(self, path: str) -> None:
        """Play the chosen track and close the picker."""
        self._close_music_track_picker()
        playlist = getattr(self, "_music_playlist", [])
        if path in playlist:
            self._play_playlist_index(playlist.index(path), announce=False)
            return
        if os.path.isfile(path):
            self.play_user_mp3(path, announce=False)

    def _close_music_track_picker(self):
        """Destroy the track picker if it is open."""
        window = getattr(self, "_music_track_picker_window", None)
        self._music_track_picker_window = None
        self._music_track_picker_drag = None
        self._music_track_picker_canvas = None
        self._music_track_picker_buttons = {}
        if window is None:
            return
        try:
            window.destroy()
        except tk.TclError:
            pass

    def _pause_user_music(self) -> None:
        """Pause pygame music without clearing user-music state."""
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.pause()
        except pygame.error:
            pass
        self._music_paused = True
        self._refresh_music_player_ui()

    def _unpause_user_music(self) -> None:
        """Resume a paused user track."""
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.unpause()
        except pygame.error:
            pass
        self._music_paused = False
        self._user_music_poll_misses = 0
        self._refresh_music_player_ui()
        self._schedule_user_music_poll()

    def _play_playlist_index(self, index: int, *, announce: bool) -> None:
        """Play playlist[*index*] if available."""
        playlist = getattr(self, "_music_playlist", [])
        if not playlist:
            return
        index = max(0, min(index, len(playlist) - 1))
        self._music_index = index
        self.play_user_mp3(playlist[index], announce=announce)

    def play_user_mp3(self, file_path, *, announce: bool = True):
        """Validate and play an MP3, then optionally announce the song name."""
        if not file_path.lower().endswith(".mp3") or not os.path.isfile(file_path):
            self.speak(dlg.pick_line(dlg.MUSIC_PLAYER_ERROR_LINES))
            return

        try:
            self.play_mp3(file_path, volume=self._music_volume_fraction())
        except (OSError, pygame.error):
            self.speak(dlg.pick_line(dlg.MUSIC_PLAYER_ERROR_LINES))
            return

        self._begin_user_music(file_path)
        if not announce:
            return
        song_name = os.path.splitext(os.path.basename(file_path))[0]
        line = random.choice(MUSIC_PLAYER_LINES).format(song=song_name)
        # Speak on the UI thread — speak() already runs TTS in the background.
        # A nested Thread + optional AI sprite update can deadlock Tk on Windows.
        self.speak(line, skip_ai=True)

    @staticmethod
    def _format_queue_position(index: int, total: int) -> str:
        """Return 1-based queue position like '5/87', or '0/0' when empty."""
        if total <= 0:
            return "0/0"
        position = max(1, min(int(index) + 1, int(total)))
        return f"{position}/{int(total)}"

    @staticmethod
    def _format_track_duration(seconds: float | None) -> str:
        """Return m:ss for a duration in seconds."""
        if seconds is None or seconds < 0:
            return "0:00"
        total = int(seconds)
        minutes, secs = divmod(total, 60)
        return f"{minutes}:{secs:02d}"

    def _probe_track_duration(self, file_path: str | None) -> float | None:
        """Return track length in seconds without fully decoding the MP3."""
        if not file_path or not os.path.isfile(file_path):
            return None
        return self._probe_mp3_duration_fast(file_path)

    @staticmethod
    def _probe_mp3_duration_fast(file_path: str) -> float | None:
        """Estimate MP3 length from Xing/Info headers or CBR bitrate (header only)."""
        # MPEG-1/2 Layer III bitrates (kbps); index 0 and 15 are invalid.
        bitrates = {
            3: (0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0),
            2: (0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 0),
            0: (0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 0),
        }
        sample_rates = {
            3: (44100, 48000, 32000, 0),
            2: (22050, 24000, 16000, 0),
            0: (11025, 12000, 8000, 0),
        }
        try:
            file_size = os.path.getsize(file_path)
            with open(file_path, "rb") as handle:
                preamble = handle.read(10)
                data_offset = 0
                if len(preamble) >= 10 and preamble[:3] == b"ID3":
                    id3_size = (
                        ((preamble[6] & 0x7F) << 21)
                        | ((preamble[7] & 0x7F) << 14)
                        | ((preamble[8] & 0x7F) << 7)
                        | (preamble[9] & 0x7F)
                    )
                    data_offset = 10 + id3_size
                handle.seek(data_offset)
                chunk = handle.read(65536)
        except OSError:
            return None
        if len(chunk) < 4:
            return None

        frame_at = None
        for index in range(0, len(chunk) - 4):
            if chunk[index] == 0xFF and (chunk[index + 1] & 0xE0) == 0xE0:
                frame_at = index
                break
        if frame_at is None:
            return None

        header = chunk[frame_at : frame_at + 4]
        version_id = (header[1] >> 3) & 0x03
        layer_id = (header[1] >> 1) & 0x03
        bitrate_index = (header[2] >> 4) & 0x0F
        sample_index = (header[2] >> 2) & 0x03
        padding = (header[2] >> 1) & 0x01
        channel_mode = (header[3] >> 6) & 0x03
        if version_id == 1 or layer_id != 1 or bitrate_index in (0, 15) or sample_index == 3:
            return None

        bitrate = bitrates.get(version_id, (0,) * 16)[bitrate_index] * 1000
        sample_rate = sample_rates.get(version_id, (0, 0, 0, 0))[sample_index]
        if bitrate <= 0 or sample_rate <= 0:
            return None

        samples_per_frame = 1152 if version_id == 3 else 576
        # Side-info size for Layer III.
        if version_id == 3:
            side_info = 17 if channel_mode == 3 else 32
        else:
            side_info = 9 if channel_mode == 3 else 17
        xing_at = frame_at + 4 + side_info
        if xing_at + 12 <= len(chunk) and chunk[xing_at : xing_at + 4] in (b"Xing", b"Info"):
            flags = int.from_bytes(chunk[xing_at + 4 : xing_at + 8], "big")
            cursor = xing_at + 8
            frames = None
            if flags & 0x1 and cursor + 4 <= len(chunk):
                frames = int.from_bytes(chunk[cursor : cursor + 4], "big")
            if frames and frames > 0:
                return frames * samples_per_frame / float(sample_rate)

        frame_length = (samples_per_frame // 8 * bitrate) // sample_rate + padding
        if frame_length <= 0:
            return None
        audio_bytes = max(0, file_size - (data_offset + frame_at))
        return audio_bytes * 8.0 / float(bitrate)

    def _progress_track_path(self) -> str | None:
        """Return the path used for progress/total display."""
        path = getattr(self, "_user_music_path", None)
        if path:
            return path
        playlist = getattr(self, "_music_playlist", [])
        index = int(getattr(self, "_music_index", 0))
        if playlist and 0 <= index < len(playlist):
            return playlist[index]
        return None

    def _ensure_music_track_duration(self) -> float | None:
        """Cache and return the duration for the current progress track."""
        path = self._progress_track_path()
        if not path:
            self._music_track_duration = None
            self._music_track_duration_path = None
            return None
        if (
            getattr(self, "_music_track_duration_path", None) == path
            and getattr(self, "_music_track_duration", None) is not None
        ):
            return self._music_track_duration
        self._music_track_duration_path = path
        self._music_track_duration = self._probe_track_duration(path)
        return self._music_track_duration

    def _get_music_elapsed_seconds(self) -> float:
        """Return how far the current track has played, in seconds."""
        if getattr(self, "_music_scrubbing", False):
            return max(0.0, float(getattr(self, "_music_scrub_seconds", 0.0)))
        if not getattr(self, "_user_music_path", None):
            return 0.0
        try:
            if not pygame.mixer.get_init():
                return 0.0
            pos_ms = pygame.mixer.music.get_pos()
            if pos_ms < 0:
                elapsed = float(getattr(self, "_music_seek_offset", 0.0))
            else:
                elapsed = float(getattr(self, "_music_seek_offset", 0.0)) + (
                    pos_ms / 1000.0
                )
            total = getattr(self, "_music_track_duration", None)
            if total is not None:
                elapsed = min(elapsed, float(total))
            return max(0.0, elapsed)
        except pygame.error:
            return 0.0

    def _clamp_music_seek_seconds(self, seconds: float) -> float:
        """Clamp a seek target into the current track duration."""
        total = self._ensure_music_track_duration()
        value = max(0.0, float(seconds))
        if total is not None and total > 0:
            # Keep a tiny tail so pygame does not immediately finish the track.
            value = min(value, max(0.0, float(total) - 0.05))
        return value

    def _music_progress_seconds_from_event(self, event) -> float | None:
        """Map a click/drag X position on the progress bar to seconds."""
        widgets = getattr(self, "_music_player_widgets", {})
        bar = widgets.get("progress_bar")
        if bar is None or not getattr(self, "_user_music_path", None):
            return None
        total = self._ensure_music_track_duration()
        if not total or total <= 0:
            return None
        try:
            width = max(1, int(bar.winfo_width()))
        except tk.TclError:
            return None
        fraction = max(0.0, min(1.0, float(event.x) / float(width)))
        return self._clamp_music_seek_seconds(fraction * float(total))

    def _seek_user_music(self, seconds: float, *, resume: bool) -> None:
        """Jump the current track to *seconds* and optionally resume playback."""
        path = getattr(self, "_user_music_path", None)
        if not path or not os.path.isfile(path):
            return
        target = self._clamp_music_seek_seconds(seconds)
        try:
            if hasattr(self, "_ensure_mixer"):
                self._ensure_mixer()
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self._music_volume_fraction())
            pygame.mixer.music.play(start=target)
            self._music_seek_offset = target
            self._user_music_poll_misses = 0
            if resume:
                self._music_paused = False
                self._schedule_user_music_poll()
            else:
                pygame.mixer.music.pause()
                self._music_paused = True
        except (OSError, pygame.error, TypeError, ValueError):
            # Fallback for builds that reject play(start=...) on MP3.
            try:
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(self._music_volume_fraction())
                pygame.mixer.music.play()
                pygame.mixer.music.set_pos(target)
                self._music_seek_offset = target
                self._user_music_poll_misses = 0
                if resume:
                    self._music_paused = False
                    self._schedule_user_music_poll()
                else:
                    pygame.mixer.music.pause()
                    self._music_paused = True
            except (OSError, pygame.error, TypeError, ValueError):
                return
        self._refresh_music_player_ui()

    def _on_music_progress_press(self, event) -> None:
        """Start scrubbing: pause playback and move the progress fill."""
        seconds = self._music_progress_seconds_from_event(event)
        if seconds is None:
            return
        was_playing = (
            bool(getattr(self, "_user_music_path", None))
            and not getattr(self, "_music_paused", False)
            and self._is_background_music_playing()
        )
        self._music_was_playing_before_scrub = was_playing
        self._music_scrubbing = True
        self._music_scrub_seconds = seconds
        self._user_music_poll_misses = 0
        if was_playing:
            try:
                if pygame.mixer.get_init():
                    pygame.mixer.music.pause()
            except pygame.error:
                pass
        self._update_music_progress_ui()

    def _on_music_progress_drag(self, event) -> None:
        """Update the scrub position while the mouse button stays down."""
        if not getattr(self, "_music_scrubbing", False):
            return
        seconds = self._music_progress_seconds_from_event(event)
        if seconds is None:
            return
        self._music_scrub_seconds = seconds
        self._update_music_progress_ui()

    def _on_music_progress_release(self, event) -> None:
        """Seek to the scrubbed position and resume if playback was active."""
        if not getattr(self, "_music_scrubbing", False):
            return
        seconds = self._music_progress_seconds_from_event(event)
        if seconds is None:
            seconds = float(getattr(self, "_music_scrub_seconds", 0.0))
        resume = bool(getattr(self, "_music_was_playing_before_scrub", False))
        self._music_scrubbing = False
        self._music_scrub_seconds = 0.0
        self._music_was_playing_before_scrub = False
        self._seek_user_music(seconds, resume=resume)

    def _schedule_music_progress_tick(self) -> None:
        """Keep the progress bar updating while the player window is open."""
        cancel_after(self.root, self, "_music_progress_timer")
        if not self._is_music_player_open():
            return
        if not getattr(self, "_running", True):
            return
        schedule_after(
            self.root,
            self,
            "_music_progress_timer",
            self._MUSIC_PROGRESS_TICK_MS,
            self._music_progress_tick,
        )

    def _music_progress_tick(self) -> None:
        """Single progress UI tick; reschedule while the player stays open."""
        self._music_progress_timer = None
        self._update_music_progress_ui()
        if self._is_music_player_open():
            self._schedule_music_progress_tick()

    def _update_music_progress_ui(self) -> None:
        """Refresh elapsed/total labels and the filled progress bar."""
        if getattr(self, "_music_progress_updating", False):
            return
        widgets = getattr(self, "_music_player_widgets", {})
        if not widgets:
            return
        elapsed_label = widgets.get("elapsed")
        total_label = widgets.get("total")
        bar = widgets.get("progress_bar")
        fill_id = widgets.get("progress_fill")
        if elapsed_label is None or total_label is None or bar is None:
            return

        self._music_progress_updating = True
        try:
            total = self._ensure_music_track_duration()
            elapsed = self._get_music_elapsed_seconds()
            elapsed_label.config(text=self._format_track_duration(elapsed))
            total_label.config(text=self._format_track_duration(total))
            if fill_id is not None:
                try:
                    width = max(0, int(bar.winfo_width()))
                    height = max(1, int(bar.winfo_height()))
                except tk.TclError:
                    return
                fraction = 0.0
                if total and total > 0:
                    fraction = min(1.0, max(0.0, elapsed / float(total)))
                bar.coords(fill_id, 0, 0, int(width * fraction), height)
        except tk.TclError:
            pass
        finally:
            self._music_progress_updating = False

    def _load_music_player_icons(self, window: tk.Misc) -> dict:
        """Load PNG control icons as PhotoImages kept alive on *window*."""
        photos: dict[str, tk.PhotoImage] = {}
        mapping = {
            "play": music_player_play_icon_path,
            "pause": music_player_pause_icon_path,
            "prev": music_player_skip_backward_icon_path,
            "next": music_player_skip_forward_icon_path,
            "order": music_player_order_icon_path,
            "shuffle": music_player_shuffle_icon_path,
            "repeat_one": music_player_repeat_one_icon_path,
            "repeat_all": music_player_repeat_all_icon_path,
            "volume": music_player_volume_icon_path,
            "list": music_player_list_icon_path,
        }
        for key, path in mapping.items():
            if not os.path.isfile(path):
                continue
            try:
                photos[key] = tk.PhotoImage(file=path, master=window)
            except tk.TclError:
                try:
                    image = Image.open(path).convert("RGBA")
                    photos[key] = ImageTk.PhotoImage(image, master=window)
                except (OSError, tk.TclError):
                    pass
        self._music_player_photos = photos
        return photos

    def _show_music_player_window(self):
        """Create or raise the music player popup."""
        existing = getattr(self, "_music_player_window", None)
        if existing is not None:
            try:
                if existing.winfo_exists():
                    if str(existing.state()) == "withdrawn":
                        existing.deiconify()
                    existing.lift()
                    existing.focus_force()
                    self._refresh_music_player_ui()
                    self._schedule_music_progress_tick()
                    self._silence_for_player_focus()
                    return
            except tk.TclError:
                self._music_player_window = None

        window = tk.Toplevel(self.root)
        self._music_player_window = window
        window.title("Kinito's Musik Player")
        apply_window_icon(window)
        window.wm_attributes("-topmost", True)
        window.overrideredirect(True)
        window.configure(bg=self._MUSIC_UI_BG)
        window.geometry(f"{self._MUSIC_PLAYER_WIDTH}x{self._MUSIC_PLAYER_HEIGHT}")
        self._center_music_player(window)

        photos = self._load_music_player_icons(window)
        widgets: dict = {}

        titlebar = tk.Frame(window, bg=self._MUSIC_TITLEBAR_BG, height=28)
        titlebar.pack(fill="x", side="top")
        titlebar.pack_propagate(False)

        icon_label = tk.Label(titlebar, bg=self._MUSIC_TITLEBAR_BG)
        if os.path.isfile(favicon_path):
            try:
                fav = tk.PhotoImage(file=favicon_path, master=window)
                # Keep a small icon in the title bar.
                if fav.width() > 20:
                    factor = max(1, fav.width() // 16)
                    fav = fav.subsample(factor, factor)
                photos["favicon"] = fav
                icon_label.configure(image=fav)
            except tk.TclError:
                pass
        icon_label.pack(side="left", padx=(8, 4), pady=4)

        title_label = tk.Label(
            titlebar,
            text="Kinito's Musik Player",
            bg=self._MUSIC_TITLEBAR_BG,
            fg="#111111",
            font=("Segoe UI", 10, "bold"),
        )
        title_label.pack(side="left", padx=2)

        close_btn = tk.Button(
            titlebar,
            text="✕",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            bd=0,
            padx=8,
            pady=0,
            bg=self._MUSIC_TITLEBAR_BG,
            fg="#111111",
            activebackground=self._MUSIC_CLOSE_HOVER_BG,
            activeforeground="#ffffff",
            cursor="hand2",
            command=self._close_music_player_window,
        )
        close_btn.pack(side="right", padx=(0, 4), pady=2)
        self._bind_music_player_button_hover(
            close_btn,
            self._MUSIC_TITLEBAR_BG,
            self._MUSIC_CLOSE_HOVER_BG,
            normal_fg="#111111",
            hover_fg="#ffffff",
        )

        minimize_btn = tk.Button(
            titlebar,
            text="−",
            font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT,
            bd=0,
            padx=8,
            pady=0,
            bg=self._MUSIC_TITLEBAR_BG,
            activebackground=self._MUSIC_TITLEBAR_HOVER_BG,
            cursor="hand2",
            command=self._minimize_music_player_window,
        )
        minimize_btn.pack(side="right", padx=0, pady=2)
        self._bind_music_player_button_hover(
            minimize_btn,
            self._MUSIC_TITLEBAR_BG,
            self._MUSIC_TITLEBAR_HOVER_BG,
        )

        for widget in (titlebar, icon_label, title_label):
            widget.bind("<ButtonPress-1>", self._start_music_player_drag)
            widget.bind("<B1-Motion>", self._drag_music_player)

        body = tk.Frame(window, bg=self._MUSIC_UI_BG)
        body.pack(fill="both", expand=True, padx=12, pady=(8, 10))

        info = tk.Frame(body, bg=self._MUSIC_UI_BG)
        info.pack(fill="x")
        song_label = tk.Label(
            info,
            text="—",
            bg=self._MUSIC_UI_BG,
            fg="#111111",
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        )
        song_label.pack(side="left", fill="x", expand=True)
        duration_label = tk.Label(
            info,
            text="0/0",
            bg=self._MUSIC_UI_BG,
            fg="#333333",
            font=("Segoe UI", 9),
            anchor="e",
        )
        duration_label.pack(side="right", padx=(8, 0))
        widgets["song"] = song_label
        widgets["queue"] = duration_label

        progress_row = tk.Frame(body, bg=self._MUSIC_UI_BG)
        progress_row.pack(fill="x", pady=(8, 0))
        elapsed_label = tk.Label(
            progress_row,
            text="0:00",
            bg=self._MUSIC_UI_BG,
            fg="#333333",
            font=("Segoe UI", 8),
            width=6,
            anchor="w",
        )
        total_label = tk.Label(
            progress_row,
            text="0:00",
            bg=self._MUSIC_UI_BG,
            fg="#333333",
            font=("Segoe UI", 8),
            width=6,
            anchor="e",
        )
        # Pack sides first so the expanding bar cannot hide the total time.
        total_label.pack(side="right")
        elapsed_label.pack(side="left")
        progress_bar = tk.Canvas(
            progress_row,
            height=12,
            bg=self._MUSIC_PROGRESS_BG,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        progress_bar.pack(side="left", fill="x", expand=True, padx=(8, 8))
        progress_fill = progress_bar.create_rectangle(
            0,
            0,
            0,
            12,
            fill=self._MUSIC_PROGRESS_FG,
            width=0,
        )
        widgets["elapsed"] = elapsed_label
        widgets["total"] = total_label
        widgets["progress_bar"] = progress_bar
        widgets["progress_fill"] = progress_fill
        progress_bar.bind(
            "<Configure>",
            lambda _event: self._update_music_progress_ui(),
        )
        progress_bar.bind("<ButtonPress-1>", self._on_music_progress_press)
        progress_bar.bind("<B1-Motion>", self._on_music_progress_drag)
        progress_bar.bind("<ButtonRelease-1>", self._on_music_progress_release)

        controls_row = tk.Frame(body, bg=self._MUSIC_UI_BG)
        controls_row.pack(fill="x", pady=(8, 4))
        controls_row.grid_columnconfigure(0, weight=1)
        controls_row.grid_columnconfigure(2, weight=1)

        def _icon_button(parent, photo_key, command):
            image = photos.get(photo_key)
            kwargs = dict(
                command=command,
                relief=tk.RIDGE,
                bd=1,
                bg=self._MUSIC_BTN_BG,
                activebackground=self._MUSIC_BTN_HOVER_BG,
                highlightthickness=0,
                cursor="hand2",
            )
            if image is not None:
                btn = tk.Button(parent, image=image, padx=6, pady=4, **kwargs)
            else:
                btn = tk.Button(parent, text=photo_key, padx=8, pady=2, **kwargs)
            self._bind_music_player_button_hover(
                btn,
                self._MUSIC_BTN_BG,
                self._MUSIC_BTN_HOVER_BG,
            )
            return btn

        volume_slot = tk.Frame(controls_row, bg=self._MUSIC_UI_BG)
        volume_slot.grid(row=0, column=0, sticky="w")
        volume_btn = _icon_button(volume_slot, "volume", self.toggle_music_volume_popup)
        volume_btn.pack(side="left")

        controls = tk.Frame(controls_row, bg=self._MUSIC_UI_BG)
        controls.grid(row=0, column=1)

        list_slot = tk.Frame(controls_row, bg=self._MUSIC_UI_BG)
        list_slot.grid(row=0, column=2, sticky="e")
        list_btn = _icon_button(list_slot, "list", self.toggle_music_track_picker)
        list_btn.pack(side="right")

        shuffle_btn = _icon_button(controls, "order", self.toggle_music_shuffle)
        prev_btn = _icon_button(controls, "prev", self.play_previous_track)
        play_btn = _icon_button(controls, "play", self.toggle_music_playback)
        next_btn = _icon_button(controls, "next", self.play_next_track)
        repeat_btn = _icon_button(controls, "repeat_all", self.toggle_music_repeat)
        shuffle_btn.pack(side="left", padx=4)
        prev_btn.pack(side="left", padx=4)
        play_btn.pack(side="left", padx=4)
        next_btn.pack(side="left", padx=4)
        repeat_btn.pack(side="left", padx=4)
        widgets["shuffle"] = shuffle_btn
        widgets["play"] = play_btn
        widgets["prev"] = prev_btn
        widgets["next"] = next_btn
        widgets["repeat"] = repeat_btn
        widgets["volume_btn"] = volume_btn
        widgets["list_btn"] = list_btn

        self._music_player_widgets = widgets
        window.protocol("WM_DELETE_WINDOW", self._close_music_player_window)
        self._refresh_music_player_ui()
        self._schedule_music_progress_tick()
        self._silence_for_player_focus()

    def _center_music_player(self, window: tk.Toplevel) -> None:
        """Place the player in the center of the primary monitor."""
        try:
            self.root.update_idletasks()
            x, y = self._centered_origin_on_primary(
                self._MUSIC_PLAYER_WIDTH,
                self._MUSIC_PLAYER_HEIGHT,
            )
        except (tk.TclError, AttributeError):
            return
        window.geometry(
            f"{self._MUSIC_PLAYER_WIDTH}x{self._MUSIC_PLAYER_HEIGHT}+{int(x)}+{int(y)}"
        )

    def _start_music_player_drag(self, event):
        """Remember the pointer offset when dragging the custom title bar."""
        window = getattr(self, "_music_player_window", None)
        if window is None:
            return
        self._music_player_drag = (event.x_root - window.winfo_x(), event.y_root - window.winfo_y())

    def _drag_music_player(self, event):
        """Move the borderless player window with the title bar."""
        window = getattr(self, "_music_player_window", None)
        drag = getattr(self, "_music_player_drag", None)
        if window is None or drag is None:
            return
        x = event.x_root - drag[0]
        y = event.y_root - drag[1]
        try:
            window.geometry(f"+{int(x)}+{int(y)}")
        except tk.TclError:
            pass

    @staticmethod
    def _bind_music_player_button_hover(
        button: tk.Button,
        normal_bg: str,
        hover_bg: str,
        *,
        normal_fg: str | None = None,
        hover_fg: str | None = None,
    ) -> None:
        """Show a hand cursor and swap background (and optional text) on hover."""

        def _enter(_event=None):
            try:
                button.configure(bg=hover_bg)
                if hover_fg is not None:
                    button.configure(fg=hover_fg)
            except tk.TclError:
                pass

        def _leave(_event=None):
            try:
                button.configure(bg=normal_bg)
                if normal_fg is not None:
                    button.configure(fg=normal_fg)
            except tk.TclError:
                pass

        button.bind("<Enter>", _enter)
        button.bind("<Leave>", _leave)

    def _minimize_music_player_window(self):
        """Hide the player UI without stopping playback."""
        self._close_music_volume_popup()
        self._close_music_track_picker()
        window = getattr(self, "_music_player_window", None)
        if window is None:
            return
        try:
            if window.winfo_exists():
                window.withdraw()
        except tk.TclError:
            pass

    def _close_music_player_window(self):
        """Close the player and stop any user song that is still playing."""
        cancel_after(self.root, self, "_music_progress_timer")
        self._close_music_volume_popup()
        self._close_music_track_picker()
        if getattr(self, "_user_music_path", None):
            self.stop_background_music()
        window = getattr(self, "_music_player_window", None)
        self._music_player_window = None
        self._music_player_widgets = {}
        self._music_player_photos = {}
        self._music_player_drag = None
        if window is None:
            return
        try:
            window.destroy()
        except tk.TclError:
            pass

    def _refresh_music_player_ui(self):
        """Sync title, queue position, progress, and control icons."""
        window = getattr(self, "_music_player_window", None)
        widgets = getattr(self, "_music_player_widgets", {})
        if window is None or not widgets:
            return
        try:
            if not window.winfo_exists():
                return
        except tk.TclError:
            return

        playlist = getattr(self, "_music_playlist", [])
        index = int(getattr(self, "_music_index", 0))
        song_name = getattr(self, "_user_music_name", None)
        if not song_name:
            if playlist:
                safe_index = max(0, min(index, len(playlist) - 1))
                song_name = os.path.splitext(os.path.basename(playlist[safe_index]))[0]
            else:
                song_name = "No songs"
        queue_text = self._format_queue_position(index, len(playlist))

        song_label = widgets.get("song")
        queue_label = widgets.get("queue")
        play_btn = widgets.get("play")
        shuffle_btn = widgets.get("shuffle")
        repeat_btn = widgets.get("repeat")
        photos = getattr(self, "_music_player_photos", {})
        try:
            if song_label is not None:
                song_label.config(text=song_name)
            if queue_label is not None:
                queue_label.config(text=queue_text)
            if play_btn is not None:
                if getattr(self, "_music_scrubbing", False):
                    playing = bool(
                        getattr(self, "_music_was_playing_before_scrub", False)
                    )
                else:
                    playing = (
                        bool(getattr(self, "_user_music_path", None))
                        and not getattr(self, "_music_paused", False)
                        and self._is_background_music_playing()
                    )
                icon = photos.get("pause" if playing else "play")
                if icon is not None:
                    play_btn.config(image=icon)
            if shuffle_btn is not None:
                shuffle_icon = photos.get(
                    "shuffle" if getattr(self, "_music_shuffle", False) else "order"
                )
                if shuffle_icon is not None:
                    shuffle_btn.config(image=shuffle_icon)
            if repeat_btn is not None:
                repeat_one = (
                    getattr(self, "_music_repeat_mode", self._MUSIC_REPEAT_ALL)
                    == self._MUSIC_REPEAT_ONE
                )
                repeat_icon = photos.get("repeat_one" if repeat_one else "repeat_all")
                if repeat_icon is not None:
                    repeat_btn.config(image=repeat_icon)
        except tk.TclError:
            pass
        self._update_music_progress_ui()
        self._refresh_music_track_picker_selection()
