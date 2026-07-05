"""Autonomous movement, drag handling, and idle sprite animations."""

import math
import random
import threading
import time
import tkinter as tk

from PIL import Image, ImageTk

from kinito.assets import bomp_file_path, page_turn_file_path, surf_file_path


class MovementMixin:
    """Mouse drag, smooth roaming, and idle sprite cycling."""

    MENU_ACTION_CHANCE = 0.22
    SPONTANEOUS_CHANCE = 0.28
    IDLE_READING_CHANCE = 0.19
    READING_WISDOM_CHANCE = 0.10
    READING_STORY_CHANCE = 0.03
    IDLE_FANCY_CHANCE = 0.02
    READING_DURATION_SECONDS = (10, 32)
    READING_PAGE_TURN_CHANCE = 0.45
    READING_PAGE_TURN_START = True
    READING_SPRITE_SWAP_SECONDS = 2.4
    IDLE_WAIT_SHORT = (20, 40)
    IDLE_WAIT_NORMAL = (40, 80)
    IDLE_WAIT_LONG = (85, 140)
    SURF_WAVE_AMPLITUDE = 8
    SURF_WAVE_STEP = 0.1
    SURF_WAVE_TILT_MAX = 6.0
    SURF_TILT_PHASE_SCALE = 0.55
    SURF_MAX_TILT = 12.0
    SURF_TILT_QUANTUM = 0.5
    SURF_MOVE_SPEED = 5
    SURF_MOVE_FRAME_DELAY = 0.022

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

    def _update_surf_facing(self, dx: float) -> None:
        """Remember whether Kinito is surfing left or right."""
        if abs(dx) >= 1:
            self._surf_facing = "left" if dx < 0 else "right"

    def _surf_sprite_for_movement(self, dx):
        """Pick the left or right surf sprite from horizontal movement."""
        self._update_surf_facing(dx)
        if self._surf_facing == "left":
            return self.tk_img_surf_left
        return self.tk_img_surf_right

    @classmethod
    def _surf_wave_offset(cls, phase: float) -> float:
        """Return a vertical bob offset for the surf animation."""
        return cls.SURF_WAVE_AMPLITUDE * math.sin(phase)

    def _surf_tilt_degrees(self, wave_phase: float) -> float:
        """Lean with the wave face: up on a crest, down in a trough."""
        wave_slope = math.cos(wave_phase * self.SURF_TILT_PHASE_SCALE)
        tilt = self.SURF_WAVE_TILT_MAX * wave_slope
        if self._surf_facing == "left":
            tilt = -tilt
        return max(-self.SURF_MAX_TILT, min(self.SURF_MAX_TILT, tilt))

    @staticmethod
    def _defringe_rgba(image: Image.Image) -> Image.Image:
        """Undo white-matte tint on semi-transparent pixels only."""
        rgba = image.convert("RGBA")
        pixels = rgba.load()
        for y in range(rgba.height):
            for x in range(rgba.width):
                r, g, b, a = pixels[x, y]
                if a in (0, 255):
                    continue
                alpha = a / 255.0
                pixels[x, y] = (
                    max(0, min(255, int((r - 255 * (1 - alpha)) / alpha))),
                    max(0, min(255, int((g - 255 * (1 - alpha)) / alpha))),
                    max(0, min(255, int((b - 255 * (1 - alpha)) / alpha))),
                    a,
                )
        return rgba

    @staticmethod
    def _snap_soft_edges_to_white(rgb: Image.Image, source_rgba: Image.Image) -> Image.Image:
        """Turn semi-transparent edge pixels pure white without touching solid art."""
        rgb_pixels = rgb.load()
        alpha = source_rgba.split()[3].load()
        for y in range(rgb.height):
            for x in range(rgb.width):
                if alpha[x, y] == 255:
                    continue
                rgb_pixels[x, y] = (255, 255, 255)
        return rgb

    @staticmethod
    def _flatten_sprite_on_white(image: Image.Image) -> Image.Image:
        """Composite an RGBA sprite onto white for Tk's transparentcolor mode."""
        if image.mode != "RGBA":
            return image.convert("RGB")
        rgba = MovementMixin._defringe_rgba(image)
        background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        composited = Image.alpha_composite(background, rgba)
        rgb = composited.convert("RGB")
        return MovementMixin._snap_soft_edges_to_white(rgb, rgba)

    @staticmethod
    def _rotate_sprite_padded(image: Image.Image, angle: float) -> Image.Image:
        """Rotate *image* without changing its canvas size."""
        if abs(angle) < 0.05:
            return MovementMixin._flatten_sprite_on_white(image)
        rgba = image.convert("RGBA")
        rotated = rgba.rotate(
            -angle,
            resample=Image.Resampling.BICUBIC,
            expand=True,
            fillcolor=(0, 0, 0, 0),
        )
        canvas = Image.new("RGBA", image.size, (0, 0, 0, 0))
        offset_x = (image.width - rotated.width) // 2
        offset_y = (image.height - rotated.height) // 2
        canvas.paste(rotated, (offset_x, offset_y), rotated)
        return MovementMixin._flatten_sprite_on_white(canvas)

    def _render_surf_sprite(self, dx: float, wave_phase: float) -> None:
        """Show a surf sprite tilted with the current wave slope."""
        if self.is_dragging:
            return
        self._update_surf_facing(dx)
        tilt = round(
            self._surf_tilt_degrees(wave_phase) / self.SURF_TILT_QUANTUM
        ) * self.SURF_TILT_QUANTUM
        facing = self._surf_facing
        if abs(tilt) < 0.05:
            photo = self.tk_img_surf_left if facing == "left" else self.tk_img_surf_right
        else:
            cache = getattr(self, "_surf_render_cache", None)
            if cache is None:
                self._surf_render_cache = {}
                cache = self._surf_render_cache
            cache_key = (facing, tilt)
            photo = cache.get(cache_key)
            if photo is None:
                base = self.img_surf_left if facing == "left" else self.img_surf_right
                rendered = self._rotate_sprite_padded(base, tilt)
                photo = ImageTk.PhotoImage(rendered, master=self.root)
                cache[cache_key] = photo
        try:
            if self.panel.winfo_exists():
                self.panel.config(image=photo)
                self._surf_tk_image = photo
        except tk.TclError:
            pass

    def _finish_surf_movement(self) -> None:
        """Reset surf visuals after roaming."""
        cache = getattr(self, "_surf_render_cache", None)
        if cache is not None:
            cache.clear()
        self.change_sprite(self.tk_img_normal)

    def _apply_surf_geometry(self, x: float, y: float, wave_phase: float) -> None:
        """Move the window along the path while bobbing on a sine wave."""
        display_y = y + self._surf_wave_offset(wave_phase)
        clamped_x, clamped_y = self.clamp_position(x, display_y)
        self.x, self.y = x, y
        self.root.geometry(f"+{int(clamped_x)}+{int(clamped_y)}")

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

    def maybe_trigger_blue_screen(self) -> bool:
        """No-op unless GlitchMixin is mixed in."""
        return False

    def maybe_trigger_random_ad(self) -> bool:
        """No-op unless AdsMixin is mixed in."""
        return False

    def _run_reading_idle(self):
        """Animate book sprites, optionally play page-turn sounds, and trigger speech."""
        reading_sprites = getattr(self, "_reading_sprites", (self.tk_img_idle,))
        frame = 0
        self.change_sprite(reading_sprites[frame % len(reading_sprites)])
        if random.random() < self.READING_STORY_CHANCE:
            threading.Thread(target=self.offer_random_story, daemon=True).start()
        elif random.random() < self.READING_WISDOM_CHANCE:
            threading.Thread(target=self.say_random_wisdom, daemon=True).start()

        duration = random.randint(*self.READING_DURATION_SECONDS)
        elapsed = 0.0
        if self.READING_PAGE_TURN_START:
            self.play_sfx(page_turn_file_path, volume=0.3)
        while elapsed < duration:
            if not self._running or self.paused:
                break
            if self.talking and not getattr(self, "_preserve_sprite", False):
                break
            if random.random() < self.READING_PAGE_TURN_CHANCE:
                self.play_sfx(page_turn_file_path, volume=0.3)
            time.sleep(self.READING_SPRITE_SWAP_SECONDS)
            elapsed += self.READING_SPRITE_SWAP_SECONDS
            frame += 1
            self.change_sprite(reading_sprites[frame % len(reading_sprites)])

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
            self.maybe_trigger_blue_screen()
            self.maybe_trigger_random_ad()
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
                self._render_surf_sprite(target_x - current_x, 0.0)
                self.play_sfx(surf_file_path)
                self.move_towards(target_x, target_y)
                self.moving = False
                self._finish_surf_movement()
                self.root.after(0, self.ensure_on_screen)
            time.sleep(self._idle_wait_before_next_action())
            if self._startup_complete:
                self._allow_random_questions = True

    def move_towards(self, target_x, target_y, speed=None, frame_delay=None):
        """Animate movement toward (*target_x*, *target_y*) at *speed* pixels per step."""
        if speed is None:
            speed = self.SURF_MOVE_SPEED
        if frame_delay is None:
            frame_delay = self.SURF_MOVE_FRAME_DELAY
        current_x, current_y = self.root.winfo_rootx(), self.root.winfo_rooty()
        current_x, current_y = self.clamp_position(current_x, current_y)
        self.x, self.y = current_x, current_y
        if (current_x, current_y) != (self.root.winfo_rootx(), self.root.winfo_rooty()):
            self.root.geometry(f"+{current_x}+{current_y}")

        target_x, target_y = self.clamp_position(target_x, target_y)
        wave_phase = 0.0
        while self._running:
            if self.paused or self.is_dragging:
                return
            current_x, current_y = self.x, self.y
            dx = target_x - current_x
            dy = target_y - current_y
            distance = ((dx**2) + (dy**2)) ** 0.5
            if distance < 1:
                self.x, self.y = target_x, target_y
                self.root.geometry(f"+{int(self.x)}+{int(self.y)}")
                break
            self._render_surf_sprite(dx, wave_phase)
            steps = min(speed, distance)
            theta = math.atan2(dy, dx)
            next_x = current_x + steps * math.cos(theta)
            next_y = current_y + steps * math.sin(theta)
            wave_phase += self.SURF_WAVE_STEP
            self._apply_surf_geometry(next_x, next_y, wave_phase)
            self.root.update()
            time.sleep(frame_delay)

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
                    self._run_reading_idle()
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
                if getattr(self, "_ai_generating", False):
                    sprite_a, sprite_b = self._talking_sprite_pair()
                    self.change_sprite(sprite_a)
                    time.sleep(1)
                    if not self._running:
                        break
                    self.change_sprite(sprite_b)
                    time.sleep(1)
                    continue
                if self._fancy_mode:
                    magician_sprites = getattr(self, "_magician_sprites", (self.tk_img_fancy,))
                    frame = getattr(self, "_magician_frame", 0)
                    self.change_sprite(magician_sprites[frame % len(magician_sprites)])
                    self._magician_frame = frame + 1
                    time.sleep(0.45)
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
