"""Local MP3 discovery and playback from the user's Music/Downloads folders."""

import os
import random
import threading
from tkinter import filedialog

import pygame

from content import dialogue as dlg
from content.music_player_lines import MUSIC_PLAYER_LINES


class MusicMixin:
    """Pick or randomly play MP3 files from common user directories."""

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

        song_name = os.path.splitext(os.path.basename(file_path))[0]
        line = random.choice(MUSIC_PLAYER_LINES).format(song=song_name)
        threading.Thread(target=lambda: self.speak(line), daemon=True).start()
