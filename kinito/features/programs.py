"""Desktop shortcuts, secret images, reminders, and window tricks."""

import os
import random
import time
import tkinter as tk
from datetime import datetime
from tkinter import Label, Toplevel

import pyautogui
from PIL import Image, ImageTk

from content import dialogue as dlg
from kinito.assets import secret_images_directory, timer_file_path
from kinito.tk_timers import cancel_after, schedule_after
from kinito.window_icon import apply_window_icon


class ProgramsMixin:
    """Launch programs, show images, set timers, and report the time."""

    _REMINDER_COUNTDOWN_GAP = 10
    _REMINDER_COUNTDOWN_BOTTOM_MARGIN = 4

    def setup_reminder_countdown_button(self):
        """Create the on-screen countdown button (hidden until a timer runs)."""
        self._reminder_end_at = None
        self._reminder_tick_timer = None
        self._reminder_countdown_btn = tk.Button(
            self.root,
            text="0:00",
            font=("Arial", 9, "bold"),
            relief=tk.RIDGE,
            bd=1,
            padx=4,
            pady=1,
            bg="#d9d9d9",
            activebackground="#d9d9d9",
            highlightthickness=0,
            command=self._open_reminder_controls,
        )

    @staticmethod
    def _parse_reminder_minutes(minutes_text: str) -> int | None:
        """Return whole minutes parsed from *minutes_text*, or None if invalid."""
        digits = [char for char in minutes_text if char.isdigit()]
        if not digits:
            return None
        value = int("".join(digits))
        return value if value > 0 else None

    @staticmethod
    def format_reminder_countdown(total_seconds: int) -> str:
        """Format *total_seconds* as M:SS or H:MM:SS for the countdown button."""
        total_seconds = max(0, total_seconds)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    def _reminder_seconds_left(self) -> int:
        end_at = getattr(self, "_reminder_end_at", None)
        if end_at is None:
            return 0
        return max(0, int(end_at - time.monotonic()))

    def _reminder_is_active(self) -> bool:
        return self._reminder_seconds_left() > 0

    def _update_reminder_countdown_button(self):
        """Refresh countdown label text from the remaining time."""
        button = getattr(self, "_reminder_countdown_btn", None)
        if button is None:
            return
        try:
            button.config(text=self.format_reminder_countdown(self._reminder_seconds_left()))
        except tk.TclError:
            pass

    def _sprite_display_height(self) -> int:
        """Return the visible sprite height in pixels."""
        panel = getattr(self, "panel", None)
        if panel is not None:
            try:
                self.root.update_idletasks()
                height = panel.winfo_height()
                if height > 1:
                    return height
            except tk.TclError:
                pass
        img = getattr(self, "img_normal", None)
        return max(getattr(img, "height", 0), 1)

    def _reminder_countdown_window_height(self) -> int:
        """Return the assistant window height needed for sprite + countdown."""
        button = getattr(self, "_reminder_countdown_btn", None)
        self.root.update_idletasks()
        button_h = button.winfo_reqheight() if button is not None else 22
        return (
            self._sprite_display_height()
            + self._REMINDER_COUNTDOWN_GAP
            + button_h
            + self._REMINDER_COUNTDOWN_BOTTOM_MARGIN
        )

    def _extend_window_for_reminder_countdown(self):
        """Reserve space below the sprite so the countdown does not overlap the feet."""
        if getattr(self, "_reminder_countdown_extended", False):
            return
        try:
            self.root.update_idletasks()
            width = max(self.root.winfo_width(), self._window_screen_size()[0], 1)
            self._reminder_countdown_prev_height = max(self.root.winfo_height(), 1)
            target_h = self._reminder_countdown_window_height()
            x = getattr(self, "x", self.root.winfo_x())
            y = getattr(self, "y", self.root.winfo_y())
            self.root.geometry(f"{width}x{target_h}+{x}+{y}")
            self._reminder_countdown_extended = True
        except tk.TclError:
            pass

    def _restore_window_after_reminder_countdown(self):
        """Shrink the assistant window after the countdown is hidden."""
        if not getattr(self, "_reminder_countdown_extended", False):
            return
        try:
            self.root.update_idletasks()
            width = max(self.root.winfo_width(), 1)
            height = getattr(self, "_reminder_countdown_prev_height", None)
            if height is None:
                height = self._sprite_display_height()
            x = getattr(self, "x", self.root.winfo_x())
            y = getattr(self, "y", self.root.winfo_y())
            self.root.geometry(f"{width}x{height}+{x}+{y}")
        except tk.TclError:
            pass
        finally:
            self._reminder_countdown_extended = False
            self._reminder_countdown_prev_height = None

    def _show_reminder_countdown_button(self):
        """Show the countdown button centered under Kinito's sprite."""
        button = getattr(self, "_reminder_countdown_btn", None)
        if button is None:
            return
        self._update_reminder_countdown_button()
        try:
            if not button.winfo_ismapped():
                self._extend_window_for_reminder_countdown()
                y = self._sprite_display_height() + self._REMINDER_COUNTDOWN_GAP
                button.place(relx=0.5, y=y, anchor="n")
        except tk.TclError:
            pass

    def _hide_reminder_countdown_button(self):
        """Hide the countdown button when no timer is running."""
        button = getattr(self, "_reminder_countdown_btn", None)
        if button is None:
            return
        try:
            if button.winfo_ismapped():
                button.place_forget()
        except tk.TclError:
            pass
        self._restore_window_after_reminder_countdown()

    def _clear_reminder(self):
        """Stop the active reminder and hide the countdown button."""
        if getattr(self, "_reminder_end_at", None) is not None:
            self._reminder_id = getattr(self, "_reminder_id", 0) + 1
        self._reminder_end_at = None
        cancel_after(self.root, self, "_reminder_tick_timer")
        self._hide_reminder_countdown_button()

    def _start_reminder(self, total_seconds: int):
        """Begin or replace a reminder countdown for *total_seconds*."""
        self._reminder_id = getattr(self, "_reminder_id", 0) + 1
        self._reminder_end_at = time.monotonic() + total_seconds
        self._show_reminder_countdown_button()
        self._schedule_reminder_tick()

    def _schedule_reminder_tick(self):
        """Update the countdown once per second until the reminder fires."""
        cancel_after(self.root, self, "_reminder_tick_timer")
        if not getattr(self, "_running", True):
            return
        if self._reminder_end_at is None:
            return
        try:
            if not self.root.winfo_exists():
                return
        except tk.TclError:
            return

        remaining = self._reminder_seconds_left()
        if remaining <= 0:
            self._reminder_end_at = None
            self._hide_reminder_countdown_button()
            self._fire_reminder()
            return

        self._update_reminder_countdown_button()
        schedule_after(
            self.root,
            self,
            "_reminder_tick_timer",
            1000,
            self._reminder_tick,
        )

    def _reminder_tick(self):
        """Single countdown tick; reschedule while time remains."""
        self._reminder_tick_timer = None
        self._schedule_reminder_tick()

    def _open_reminder_controls(self):
        """Open cancel/adjust options for the running reminder."""
        if not self._reminder_is_active():
            return
        self.speak(dlg.REMINDER_MANAGE_PROMPT, 45, True)

    def cancel_reminder(self):
        """Cancel the running reminder."""
        if self._reminder_end_at is None:
            return
        self._clear_reminder()
        self.speak(dlg.pick_line(dlg.REMINDER_CANCELLED_LINES))

    def _launch_shortcut(self, shortcut_path):
        """Open a Windows .lnk shortcut; return True on success."""
        try:
            os.startfile(shortcut_path)
            return True
        except OSError:
            return False

    def play_random_program(self):
        """Launch a random desktop shortcut or explain why none was found."""
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

        try:
            if os.path.exists(desktop_path) and os.path.isdir(desktop_path):
                shortcut_files = [
                    file for file in os.listdir(desktop_path) if file.endswith(".lnk")
                ]
                if shortcut_files:
                    selected_shortcut = random.choice(shortcut_files)
                    if self._launch_shortcut(os.path.join(desktop_path, selected_shortcut)):
                        return
                else:
                    self.speak(dlg.pick_line(dlg.NO_DESKTOP_SHORTCUTS_LINES))
                    self.speak_random_question()
                    return

            onedrive_path = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
            if os.path.exists(onedrive_path) and os.path.isdir(onedrive_path):
                onedrive_shortcuts = [
                    file for file in os.listdir(onedrive_path) if file.endswith(".lnk")
                ]
                if onedrive_shortcuts:
                    selected_shortcut = random.choice(onedrive_shortcuts)
                    if self._launch_shortcut(os.path.join(onedrive_path, selected_shortcut)):
                        return
                self.speak(dlg.pick_line(dlg.NO_ONEDRIVE_SHORTCUTS_LINES))
                self.speak_random_question()
                return

            self.speak(dlg.pick_line(dlg.DESKTOP_NOT_FOUND_LINES))
            self.speak_random_question()
        except OSError:
            self.speak(dlg.pick_line(dlg.DESKTOP_NOT_FOUND_LINES))
            self.speak_random_question()

    def minimize_current_window(self):
        """Send Win+Down to minimize the active window."""
        try:
            pyautogui.hotkey("winleft", "down")
        except (OSError, pyautogui.FailSafeException):
            pass

    def show_image(self):
        """Pick a random image from SecretImages and display it."""
        secret_images_folder = secret_images_directory

        if os.path.exists(secret_images_folder) and os.path.isdir(secret_images_folder):
            image_files = [
                file
                for file in os.listdir(secret_images_folder)
                if file.endswith((".jpg", ".jpeg", ".png"))
            ]

            if image_files:
                selected_image = random.choice(image_files)
                image_path = os.path.join(secret_images_folder, selected_image)
                self.show_image_window(image_path)
            else:
                self.speak(dlg.pick_line(dlg.NO_SECRET_IMAGES_LINES))
                self.speak_random_question()
        else:
            self.speak(dlg.pick_line(dlg.SECRET_IMAGES_NOT_FOUND_LINES))
            self.speak_random_question()

    def show_popup_image(
        self,
        image_path,
        *,
        width=360,
        height=280,
        x=None,
        y=None,
        title="KinitoPET",
        on_close=None,
        modal=False,
    ):
        """Show *image_path* in a compact popup window."""
        try:
            img = Image.open(image_path)
        except OSError:
            if on_close is not None:
                on_close()
            return

        popup = Toplevel(self.root)
        popup.title(title)
        apply_window_icon(popup)
        popup.geometry(f"{width}x{height}")
        popup.wm_attributes("-topmost", True)

        tk_img = ImageTk.PhotoImage(img)
        label = Label(popup, image=tk_img)
        label.image = tk_img
        label.pack(fill="both", expand=True)

        if x is None or y is None:
            vroot_x = self.root.winfo_vrootx()
            vroot_y = self.root.winfo_vrooty()
            vroot_w = self.root.winfo_vrootwidth()
            vroot_h = self.root.winfo_vrootheight()
            x = vroot_x + (vroot_w - width) // 2
            y = vroot_y + (vroot_h - height) // 2
        popup.geometry(f"{width}x{height}+{int(x)}+{int(y)}")

        def _handle_close():
            if on_close is not None:
                on_close()
            try:
                popup.destroy()
            except tk.TclError:
                pass

        popup.protocol("WM_DELETE_WINDOW", _handle_close)
        if modal:
            popup.wait_window(popup)

    def show_image_window(self, image_path):
        """Show *image_path* in a modal window and freeze mouse until closed."""
        try:
            img = Image.open(image_path)
        except OSError:
            self.speak(dlg.pick_line(dlg.NO_SECRET_IMAGES_LINES))
            self.speak_random_question()
            return

        image_window = Toplevel(self.root)
        image_window.title("Image.png From: KinitoPET")
        apply_window_icon(image_window)
        image_window.geometry("800x600")

        tk_img = ImageTk.PhotoImage(img)
        label = Label(image_window, image=tk_img)
        label.image = tk_img
        label.pack(fill="both", expand="yes")

        vroot_x = self.root.winfo_vrootx()
        vroot_y = self.root.winfo_vrooty()
        vroot_w = self.root.winfo_vrootwidth()
        vroot_h = self.root.winfo_vrootheight()
        x = vroot_x + (vroot_w - 800) // 2
        y = vroot_y + (vroot_h - 600) // 2
        image_window.geometry(f"800x600+{x}+{y}")

        image_window.wait_window(image_window)
        self.unfreeze_mouse()

    def freeze_mouse(self):
        """Block mouse motion events on the assistant root (used during image reveal)."""
        self.root.bind("<Motion>", lambda event: "break")

    def unfreeze_mouse(self):
        """Restore normal mouse motion handling."""
        self.root.unbind("<Motion>")

    def set_reminder(self, minutes):
        """Start a background timer for the given number of minutes."""
        parsed = self._parse_reminder_minutes(minutes)
        if parsed is None:
            self.speak(dlg.pick_line(dlg.REMINDER_INVALID_LINES), 45, True)
            return

        self._start_reminder(parsed * 60)
        self.speak(dlg.pick_line(dlg.REMINDER_SET_LINES), show_bubble=False)

    def adjust_reminder(self, minutes):
        """Replace the running reminder with a new duration in minutes."""
        parsed = self._parse_reminder_minutes(minutes)
        if parsed is None:
            self.speak(dlg.pick_line(dlg.REMINDER_INVALID_LINES), 45, True)
            return

        self._start_reminder(parsed * 60)
        self.speak(dlg.pick_line(dlg.REMINDER_ADJUSTED_LINES), show_bubble=False)

    def _fire_reminder(self):
        """Play the timer sound and speak the reminder-done line."""
        if not self._running:
            return
        self.play_sfx(timer_file_path)
        self.speak(dlg.pick_line(dlg.REMINDER_DONE_LINES))

    def print_current_datetime(self):
        """Speak the current local time."""
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%H:%M")
        self.speak(dlg.pick_line(dlg.TIME_RESPONSES).format(time=formatted_datetime))
