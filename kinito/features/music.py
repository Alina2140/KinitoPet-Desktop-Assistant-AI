"""Folder-based MP3 playlist and Kinito's Musik Player window."""

from __future__ import annotations

import os
import random
import threading
import tkinter as tk
from tkinter import filedialog

import pygame
from PIL import Image, ImageTk

from content import dialogue as dlg
from content.music_player_lines import MUSIC_PLAYER_LINES
from kinito.assets import (
    favicon_path,
    music_player_order_icon_path,
    music_player_pause_icon_path,
    music_player_play_icon_path,
    music_player_repeat_all_icon_path,
    music_player_repeat_one_icon_path,
    music_player_shuffle_icon_path,
    music_player_skip_backward_icon_path,
    music_player_skip_forward_icon_path,
)
from kinito.settings_store import clamp_music_volume
from kinito.tk_timers import cancel_after, schedule_after
from kinito.window_icon import apply_window_icon


class MusicMixin:
    """Play MP3s from a chosen folder via a dedicated music player window."""

    _MUSIC_POLL_GRACE_TICKS = 3
    _MUSIC_PLAYER_WIDTH = 420
    _MUSIC_PLAYER_HEIGHT = 168
    _MUSIC_UI_BG = "#e6ded5"
    _MUSIC_TITLEBAR_BG = "#d4ccc2"
    _MUSIC_BTN_BG = "#d9d9d9"
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
        self._music_shuffle = False
        self._music_repeat_mode = self._MUSIC_REPEAT_ALL
        self._music_player_window = None
        self._music_player_widgets: dict = {}
        self._music_player_photos: dict = {}
        self._music_player_drag = None
        if not hasattr(self, "_music_folder"):
            self._music_folder = ""
        if not hasattr(self, "_music_volume"):
            self._music_volume = 75

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
        self._music_index = 0
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
        """Scan the music folder for MP3s and store a sorted playlist."""
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
        if file_path in getattr(self, "_music_playlist", []):
            self._music_index = self._music_playlist.index(file_path)
        self._refresh_music_player_ui()
        self._schedule_user_music_poll()

    def _on_background_music_stopped(self) -> None:
        """Clear user-music playback state after an external stop."""
        self._user_music_path = None
        self._user_music_name = None
        self._user_music_poll_misses = 0
        self._music_paused = False
        cancel_after(self.root, self, "_user_music_poll_timer")
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

        if getattr(self, "_music_paused", False):
            self._user_music_poll_misses = 0
            schedule_after(
                self.root,
                self,
                "_user_music_poll_timer",
                1000,
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
                    1000,
                    self._user_music_poll,
                )
            return

        self._user_music_poll_misses = 0
        schedule_after(
            self.root,
            self,
            "_user_music_poll_timer",
            1000,
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
        """Toggle between sequential order and shuffle playback."""
        self._music_shuffle = not bool(getattr(self, "_music_shuffle", False))
        self._refresh_music_player_ui()

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
        threading.Thread(target=lambda: self.speak(line), daemon=True).start()

    @staticmethod
    def _format_track_duration(seconds: float | None) -> str:
        """Return m:ss for a duration in seconds."""
        if seconds is None or seconds < 0:
            return "--:--"
        total = int(round(seconds))
        minutes, secs = divmod(total, 60)
        return f"{minutes}:{secs:02d}"

    def _probe_track_duration(self, file_path: str | None) -> float | None:
        """Return track length in seconds, or None when unknown."""
        if not file_path or not os.path.isfile(file_path):
            return None
        try:
            if hasattr(self, "_ensure_mixer"):
                self._ensure_mixer()
            sound = pygame.mixer.Sound(file_path)
            return float(sound.get_length())
        except (OSError, pygame.error, TypeError, ValueError):
            return None

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
                    existing.lift()
                    existing.focus_force()
                    self._refresh_music_player_ui()
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
            activebackground="#c4bbb0",
            command=self._close_music_player_window,
        )
        close_btn.pack(side="right", padx=4, pady=2)

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
            text="--:--",
            bg=self._MUSIC_UI_BG,
            fg="#333333",
            font=("Segoe UI", 9),
            anchor="e",
        )
        duration_label.pack(side="right", padx=(8, 0))
        widgets["song"] = song_label
        widgets["duration"] = duration_label

        controls = tk.Frame(body, bg=self._MUSIC_UI_BG)
        controls.pack(pady=(12, 4))

        def _icon_button(parent, photo_key, command):
            image = photos.get(photo_key)
            if image is not None:
                return tk.Button(
                    parent,
                    image=image,
                    command=command,
                    relief=tk.RIDGE,
                    bd=1,
                    padx=6,
                    pady=4,
                    bg=self._MUSIC_BTN_BG,
                    activebackground=self._MUSIC_BTN_BG,
                    highlightthickness=0,
                )
            return tk.Button(
                parent,
                text=photo_key,
                command=command,
                relief=tk.RIDGE,
                bd=1,
                padx=8,
                pady=2,
                bg=self._MUSIC_BTN_BG,
                activebackground=self._MUSIC_BTN_BG,
            )

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

        volume_row = tk.Frame(body, bg=self._MUSIC_UI_BG)
        volume_row.pack(fill="x", pady=(8, 0))
        tk.Label(
            volume_row,
            text="Volume",
            bg=self._MUSIC_UI_BG,
            font=("Segoe UI", 8),
        ).pack(side="left")
        volume = tk.Scale(
            volume_row,
            from_=0,
            to=100,
            orient="horizontal",
            showvalue=True,
            length=220,
            bg=self._MUSIC_UI_BG,
            highlightthickness=0,
            troughcolor="#cfc6bc",
            command=lambda value: self.set_music_volume(value),
        )
        volume.set(clamp_music_volume(getattr(self, "_music_volume", 75)))
        volume.pack(side="left", fill="x", expand=True, padx=(8, 0))
        widgets["volume"] = volume

        self._music_player_widgets = widgets
        window.protocol("WM_DELETE_WINDOW", self._close_music_player_window)
        self._refresh_music_player_ui()

    def _center_music_player(self, window: tk.Toplevel) -> None:
        """Place the player near the center of the virtual desktop."""
        try:
            self.root.update_idletasks()
            vroot_x = self.root.winfo_vrootx()
            vroot_y = self.root.winfo_vrooty()
            vroot_w = self.root.winfo_vrootwidth()
            vroot_h = self.root.winfo_vrootheight()
        except tk.TclError:
            return
        x = vroot_x + (vroot_w - self._MUSIC_PLAYER_WIDTH) // 2
        y = vroot_y + (vroot_h - self._MUSIC_PLAYER_HEIGHT) // 2
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

    def _close_music_player_window(self):
        """Close the player and stop any user song that is still playing."""
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
        """Sync title, duration, and control icons with current playback state."""
        window = getattr(self, "_music_player_window", None)
        widgets = getattr(self, "_music_player_widgets", {})
        if window is None or not widgets:
            return
        try:
            if not window.winfo_exists():
                return
        except tk.TclError:
            return

        song_name = getattr(self, "_user_music_name", None)
        if not song_name:
            playlist = getattr(self, "_music_playlist", [])
            index = int(getattr(self, "_music_index", 0))
            if playlist:
                song_name = os.path.splitext(os.path.basename(playlist[index]))[0]
            else:
                song_name = "No songs"
        path = getattr(self, "_user_music_path", None)
        if path is None:
            playlist = getattr(self, "_music_playlist", [])
            index = int(getattr(self, "_music_index", 0))
            if playlist:
                path = playlist[index]
        duration = self._format_track_duration(self._probe_track_duration(path))

        song_label = widgets.get("song")
        duration_label = widgets.get("duration")
        play_btn = widgets.get("play")
        shuffle_btn = widgets.get("shuffle")
        repeat_btn = widgets.get("repeat")
        photos = getattr(self, "_music_player_photos", {})
        try:
            if song_label is not None:
                song_label.config(text=song_name)
            if duration_label is not None:
                duration_label.config(text=duration)
            if play_btn is not None:
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
