"""Local MP3 discovery and playback from the user's Music/Downloads folders."""

import os
import random
import threading
import tkinter as tk
from tkinter import filedialog

import pygame

from content import dialogue as dlg
from content.music_player_lines import MUSIC_PLAYER_LINES
from kinito.tk_timers import cancel_after, schedule_after


class MusicMixin:
    """Pick or randomly play MP3 files from common user directories."""

    _MUSIC_BUTTON_LABEL_MAX = 18
    _MUSIC_POLL_GRACE_TICKS = 3

    def setup_music_control_button(self):
        """Create the on-screen music button (hidden until user music plays)."""
        self._user_music_path = None
        self._user_music_name = None
        self._user_music_poll_timer = None
        self._music_control_btn = tk.Button(
            self.root,
            text="♪ Music",
            font=("Arial", 9, "bold"),
            relief=tk.RIDGE,
            bd=1,
            padx=4,
            pady=1,
            bg="#d9d9d9",
            activebackground="#d9d9d9",
            highlightthickness=0,
            command=self._open_music_controls,
        )

    def ask_music_player_pick(self):
        """Ask whether the user wants to pick a song or get a random one."""
        if self._is_busy_with_speech():
            return
        self.speak(dlg.MUSIC_PLAYER_PICK_QUESTION, 45, True)

    def offer_random_music(self):
        """Ask the user before playing music from their computer."""
        if self._is_busy_with_speech():
            return
        self.speak(dlg.pick_line(dlg.MUSIC_PLAYER_QUESTIONS), 45, True)

    @classmethod
    def _format_music_button_label(cls, song_name: str) -> str:
        """Return a compact song label for the on-screen music button."""
        label = song_name.strip() or "Music"
        if len(label) <= cls._MUSIC_BUTTON_LABEL_MAX:
            return f"♪ {label}"
        return f"♪ {label[: cls._MUSIC_BUTTON_LABEL_MAX - 1]}…"

    def _user_music_controls_visible(self) -> bool:
        """Return True while the on-screen music button should stay available."""
        return bool(getattr(self, "_user_music_path", None))

    def _user_music_is_active(self) -> bool:
        """Return True while a user-selected song is still playing."""
        return self._user_music_controls_visible() and self._is_background_music_playing()

    def _update_music_control_button(self):
        """Refresh the music button label from the current song name."""
        button = getattr(self, "_music_control_btn", None)
        if button is None:
            return
        song_name = getattr(self, "_user_music_name", None) or "Music"
        try:
            button.config(text=self._format_music_button_label(song_name))
        except tk.TclError:
            pass

    def _begin_user_music(self, file_path: str) -> None:
        """Track a user-selected song and show the on-screen music controls."""
        self._user_music_path = file_path
        self._user_music_name = os.path.splitext(os.path.basename(file_path))[0]
        self._user_music_poll_misses = 0
        self._update_music_control_button()
        if hasattr(self, "_sync_assistant_controls_layout"):
            self._sync_assistant_controls_layout()
        self._schedule_user_music_poll()

    def _on_background_music_stopped(self) -> None:
        """Hide music controls after playback ends or is interrupted."""
        had_user_music = bool(getattr(self, "_user_music_path", None))
        self._user_music_path = None
        self._user_music_name = None
        self._user_music_poll_misses = 0
        cancel_after(self.root, self, "_user_music_poll_timer")
        if had_user_music and hasattr(self, "_sync_assistant_controls_layout"):
            self._sync_assistant_controls_layout()

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

        if not self._is_background_music_playing():
            misses = getattr(self, "_user_music_poll_misses", 0) + 1
            self._user_music_poll_misses = misses
            if misses >= self._MUSIC_POLL_GRACE_TICKS:
                self._on_background_music_stopped()
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

    def _open_music_controls(self):
        """Open stop/change options for the running song."""
        if not self._user_music_controls_visible():
            return
        self.speak(dlg.MUSIC_MANAGE_PROMPT, 45, True)

    def stop_user_music(self):
        """Stop the current user-selected song."""
        if not getattr(self, "_user_music_path", None):
            return
        self.stop_background_music()
        self.speak(dlg.pick_line(dlg.MUSIC_STOPPED_LINES))

    def _music_search_roots(self):
        """Return folders to scan for MP3 files (Music, Downloads, OneDrive)."""
        home = os.path.expanduser("~")
        return [
            os.path.join(home, "Music"),
            os.path.join(home, "Downloads"),
            os.path.join(home, "OneDrive", "Music"),
            os.path.join(home, "OneDrive", "Downloads"),
        ]

    def _find_mp3_files(self, limit=300):
        """Collect up to *limit* MP3 paths from the search roots."""
        mp3_files = []
        for root in self._music_search_roots():
            if not os.path.isdir(root):
                continue
            for dirpath, _, filenames in os.walk(root):
                if dirpath[len(root) :].count(os.sep) > 4:
                    continue
                for filename in filenames:
                    if filename.lower().endswith(".mp3"):
                        mp3_files.append(os.path.join(dirpath, filename))
                        if len(mp3_files) >= limit:
                            return mp3_files
        return mp3_files

    def pick_and_play_mp3(self):
        """Open a file dialog and play the chosen MP3."""
        music_dir = os.path.join(os.path.expanduser("~"), "Music")
        if not os.path.isdir(music_dir):
            music_dir = os.path.expanduser("~")

        file_path = filedialog.askopenfilename(
            parent=self.root,
            title="Pick an MP3 for Kinito to play",
            filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")],
            initialdir=music_dir,
        )
        if file_path:
            self.play_user_mp3(file_path)
        else:
            self.speak(dlg.pick_line(dlg.MUSIC_PLAYER_CANCELLED_LINES))

    def play_random_mp3(self):
        """Pick a random MP3 from discovered files and play it."""
        mp3_files = self._find_mp3_files()
        if not mp3_files:
            self.speak(dlg.pick_line(dlg.MUSIC_PLAYER_NOT_FOUND_LINES))
            return
        self.play_user_mp3(random.choice(mp3_files))

    def play_user_mp3(self, file_path):
        """Validate and play an MP3, then announce the song name."""
        if not file_path.lower().endswith(".mp3") or not os.path.isfile(file_path):
            self.speak(dlg.pick_line(dlg.MUSIC_PLAYER_ERROR_LINES))
            return

        try:
            self.play_mp3(file_path, volume=0.75)
        except (OSError, pygame.error):
            self.speak(dlg.pick_line(dlg.MUSIC_PLAYER_ERROR_LINES))
            return

        self._begin_user_music(file_path)
        song_name = os.path.splitext(os.path.basename(file_path))[0]
        line = random.choice(MUSIC_PLAYER_LINES).format(song=song_name)
        threading.Thread(target=lambda: self.speak(line), daemon=True).start()
