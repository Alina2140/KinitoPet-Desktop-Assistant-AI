"""Autonomous movement, drag handling, and idle sprite animations."""

import math
import random
import threading
import time
import tkinter as tk

from kinito.assets import bomp_file_path, surf_file_path


class MovementMixin:
    """Mouse drag, smooth roaming, and idle sprite cycling."""

    MENU_ACTION_CHANCE = 0.22
    SPONTANEOUS_CHANCE = 0.28
    IDLE_READING_CHANCE = 0.19
    READING_WISDOM_CHANCE = 0.10
    READING_STORY_CHANCE = 0.03
    IDLE_FANCY_CHANCE = 0.02
    IDLE_WAIT_SHORT = (20, 40)
    IDLE_WAIT_NORMAL = (40, 80)
    IDLE_WAIT_LONG = (85, 140)

    def setup_mouse_bindings(self):
        """Bind left-click drag events for repositioning Kinito."""
        self.root.bind("<Button-1>", self.on_mouse_down)
        self.root.bind("<B1-Motion>", self.on_mouse_move)
        self.root.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.x, self.y = self.root.winfo_rootx(), self.root.winfo_rooty()

    def on_mouse_down(self, event):
        """Begin dragging, stop roam sounds, and play the bomp click sound."""
        self.is_dragging = True
        self._drag_moved = False
        self.moving = False
        if hasattr(self, "stop_background_music"):
            self.stop_background_music()
        if not self._should_skip_drag_sounds():
            self.play_sfx(bomp_file_path)
        self.root.update_idletasks()
        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        self.mouse_click_offset_x = root_x - event.x_root
        self.mouse_click_offset_y = root_y - event.y_root

    def on_mouse_move(self, event):
        """Move the window while dragging and keep speech/love bubbles aligned."""
        if self.is_dragging:
            self._drag_moved = True
            new_x = event.x_root + self.mouse_click_offset_x
            new_y = event.y_root + self.mouse_click_offset_y
            new_x, new_y = self.clamp_position(new_x, new_y)
            self.x, self.y = new_x, new_y
            self.root.geometry(f"+{new_x}+{new_y}")
            if self._has_active_speech_bubble():
                self.position_speech_bubble()

    def on_mouse_up(self, event):
        """End dragging and play the drop sound after a real drag."""
        if self.is_dragging and self._drag_moved and not self._should_skip_drag_sounds():
            self.play_sfx(bomp_file_path)
        self.is_dragging = False
        self._drag_moved = False
        if hasattr(self, "ensure_on_screen"):
            self.root.after(0, self.ensure_on_screen)

    def change_sprite(self, new_sprite):
        """Swap the visible sprite unless the user is currently dragging."""
        if self.is_dragging:
            return
        try:
            if self.panel.winfo_exists():
                self.panel.config(image=new_sprite)
        except tk.TclError:
            pass

    def _surf_sprite_for_movement(self, dx):
        """Pick the left or right surf sprite from horizontal movement."""
        if abs(dx) >= 1:
            self._surf_facing = "left" if dx < 0 else "right"
        if self._surf_facing == "left":
            return self.tk_img_surf_left
        return self.tk_img_surf_right

    def _talking_sprite_pair(self):
        """Return the two-frame sprite pair for the current speech mode."""
        if getattr(self, "_talk_sprite_mode", "talking") == "thinking":
            return self.tk_img_thinking, self.tk_img_thinking2
        return self.tk_img_talking, self.tk_img_talking2

    def _idle_wait_before_next_action(self):
        """Return a random pause (seconds) before the next autonomous action."""
        roll = random.random()
        if roll < 0.15:
            return random.randint(*self.IDLE_WAIT_SHORT)
        if roll < 0.75:
            return random.randint(*self.IDLE_WAIT_NORMAL)
        return random.randint(*self.IDLE_WAIT_LONG)

    def maybe_trigger_screen_glitch(self) -> bool:
        """No-op unless GlitchMixin is mixed in."""
        return False

    def smooth_movement(self):
        """Background loop: roam the screen or trigger spontaneous speech/actions."""
        while self._running:
            if (
                self.paused
                or self.is_dragging
                or not self._startup_complete
                or self._is_busy_with_speech()
                or self._is_background_music_playing()
            ):
                time.sleep(0.1)
                continue
            self.maybe_trigger_screen_glitch()
            if (
                random.random() < self.SPONTANEOUS_CHANCE
                and self._allow_random_questions
                and not getattr(self, "_focus_mode", False)
            ):
                if random.random() < self.MENU_ACTION_CHANCE:
                    self.perform_random_menu_action()
                elif self._should_use_ai_idle_line():
                    self.speak_ai_idle_line()
                else:
                    self.speak_random_question()
            else:
                self.ensure_on_screen()
                target_x, target_y = self.random_position_on_screen()
                self.moving = True
                current_x = self.root.winfo_rootx()
                self.change_sprite(self._surf_sprite_for_movement(target_x - current_x))
                self.play_sfx(surf_file_path)
                self.move_towards(target_x, target_y, speed=5)
                self.moving = False
                self.change_sprite(self.tk_img_normal)
                self.root.after(0, self.ensure_on_screen)
            time.sleep(self._idle_wait_before_next_action())
            if self._startup_complete:
                self._allow_random_questions = True

    def move_towards(self, target_x, target_y, speed):
        """Animate movement toward (*target_x*, *target_y*) at *speed* pixels per step."""
        current_x, current_y = self.root.winfo_rootx(), self.root.winfo_rooty()
        current_x, current_y = self.clamp_position(current_x, current_y)
        self.x, self.y = current_x, current_y
        if (current_x, current_y) != (self.root.winfo_rootx(), self.root.winfo_rooty()):
            self.root.geometry(f"+{current_x}+{current_y}")

        target_x, target_y = self.clamp_position(target_x, target_y)
        while self._running:
            if self.paused or self.is_dragging:
                return
            current_x, current_y = self.root.winfo_rootx(), self.root.winfo_rooty()
            dx = target_x - current_x
            dy = target_y - current_y
            distance = ((dx**2) + (dy**2)) ** 0.5
            if distance < 1:
                break
            self.change_sprite(self._surf_sprite_for_movement(dx))
            steps = min(speed, distance)
            theta = math.atan2(dy, dx)
            self.x = current_x + steps * math.cos(theta)
            self.y = current_y + steps * math.sin(theta)
            self.x, self.y = self.clamp_position(self.x, self.y)
            self.root.geometry(f"+{self.x}+{self.y}")
            self.root.update()
            time.sleep(0.015)

    def idle_animation(self):
        """Background loop: alternate normal sprites, reading, fancy, sleep, and thinking."""
        while self._running:
            if self.moving:
                time.sleep(0.1)
                continue
            if not self.paused and not self.talking:
                idle_roll = random.random()
                focus_mode = getattr(self, "_focus_mode", False)
                if (
                    not focus_mode
                    and idle_roll < self.IDLE_READING_CHANCE
                    and self._allow_random_questions
                ):
                    self.change_sprite(self.tk_img_idle)
                    if random.random() < self.READING_STORY_CHANCE:
                        threading.Thread(target=self.offer_random_story, daemon=True).start()
                    elif random.random() < self.READING_WISDOM_CHANCE:
                        threading.Thread(target=self.say_random_wisdom, daemon=True).start()
                    for _ in range(random.randint(5, 12)):
                        if not self._running or self.paused:
                            break
                        if self.talking and not getattr(self, "_preserve_sprite", False):
                            break
                        time.sleep(1)
                    continue
                if (
                    not focus_mode
                    and idle_roll < self.IDLE_READING_CHANCE + self.IDLE_FANCY_CHANCE
                    and self._allow_random_questions
                ):
                    self._run_fancy_idle()
                    continue
                self.change_sprite(self.tk_img_normal)
                time.sleep(1)
                if not self._running:
                    break
                self.change_sprite(self.tk_img_normal_2)
                time.sleep(1)
            elif self.paused and not self.talking:
                for sprite in (
                    self.tk_img_sleep,
                    self.tk_img_sleep1,
                    self.tk_img_sleep2,
                    self.tk_img_sleep3,
                ):
                    if not self._running:
                        return
                    self.change_sprite(sprite)
                    time.sleep(1)
            elif self.talking:
                if getattr(self, "_preserve_sprite", False):
                    time.sleep(0.1)
                    continue
                if self._fancy_mode:
                    self.change_sprite(self.tk_img_fancy)
                    time.sleep(1)
                    continue
                if self._hug_mode:
                    self.change_sprite(self.tk_img_hug)
                    time.sleep(1)
                    if not self._running:
                        break
                    self.change_sprite(self.tk_img_hug2)
                    time.sleep(1)
                    continue
                sprite_a, sprite_b = self._talking_sprite_pair()
                self.change_sprite(sprite_a)
                time.sleep(1)
                if not self._running:
                    break
                self.change_sprite(sprite_b)
                time.sleep(1)
            else:
                time.sleep(0.1)
