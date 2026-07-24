"""Autonomous movement, drag handling, and idle sprite animations."""

import math
import random
import threading
import time
import tkinter as tk

from PIL import Image, ImageTk

from kinito.assets import (
    bomp_file_path,
    look_direction_from_delta,
    page_turn_file_path,
    surf_file_path,
)
from kinito.tk_timers import cancel_after, schedule_after


class MovementMixin:
    """Mouse drag, smooth roaming, and idle sprite cycling."""

    MENU_ACTION_CHANCE = 0.22
    MEMORY_QUESTION_CHANCE = 0.18
    SPONTANEOUS_CHANCE = 0.28
    IDLE_READING_CHANCE = 0.19
    READING_WISDOM_CHANCE = 0.10
    READING_STORY_CHANCE = 0.03
    IDLE_FANCY_CHANCE = 0.02
    IDLE_GLASSES_CHANCE = 0.28
    NORMAL_DEFAULT_LOOK_CHANCE = 0.82
    LOOK_AROUND_COOLDOWN_SECONDS = 10.0
    READING_DURATION_SECONDS = (10, 32)
    READING_PAGE_TURN_CHANCE = 0.14
    READING_PAGE_TURN_VOLUME = 0.3
    READING_PAGE_TURN_SOUND_LEAD_SECONDS = 2.00
    READING_PAGE_TURN_FRAME_SECONDS = 0.2
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
    MOUSE_LOOK_RADIUS_PX = 230
    MOUSE_FOLLOW_RADIUS_PX = 180
    MOUSE_LOOK_DEADZONE_PX = 40
    MOUSE_LOOK_POLL_MS = 80
    MOUSE_FOLLOW_CHANCE = 0.35
    MOUSE_THINK_SECONDS = (0.6, 1.2)
    MOUSE_FOLLOW_MAX_PX = 160
    MOUSE_FOLLOW_COOLDOWN_SECONDS = (15, 35)
    MOUSE_LOOK_STANCE_SECONDS = 1.0

    def setup_mouse_bindings(self):
        """Bind drag to the sprite only so control buttons stay clickable."""
        self.panel.bind("<Button-1>", self.on_mouse_down)
        self.root.bind("<Configure>", self._on_root_moved)
        self._sync_kinito_screen_position()

    def _sync_kinito_screen_position(self):
        """Keep tracked screen coordinates aligned with the root window."""
        if getattr(self, "moving", False):
            return
        try:
            x = self.root.winfo_rootx()
            y = self.root.winfo_rooty()
        except tk.TclError:
            return
        if x > 0 and y > 0:
            self.x, self.y = x, y

    def _start_drag_tracking(self):
        """Track drag globally so motion still works over other top-level windows."""
        self.root.bind_all("<B1-Motion>", self.on_mouse_move)
        self.root.bind_all("<ButtonRelease-1>", self.on_mouse_up)

    def _stop_drag_tracking(self):
        """Remove global drag bindings after mouse up."""
        try:
            self.root.unbind_all("<B1-Motion>")
            self.root.unbind_all("<ButtonRelease-1>")
        except tk.TclError:
            pass

    def _follow_speech_bubble_to_kinito(self, kinito_x=None, kinito_y=None):
        """Reposition an open speech bubble to follow Kinito's current location."""
        if not hasattr(self, "_has_active_speech_bubble") or not self._has_active_speech_bubble():
            return
        if kinito_x is None or kinito_y is None:
            kinito_x, kinito_y = getattr(self, "x", 0), getattr(self, "y", 0)
        if getattr(self, "is_dragging", False) and hasattr(self, "_move_speech_bubble_with_kinito"):
            self._move_speech_bubble_with_kinito(kinito_x, kinito_y)
        elif hasattr(self, "position_speech_bubble"):
            self.position_speech_bubble()

    def _on_root_moved(self, event):
        """Keep speech bubbles aligned whenever Kinito's window moves."""
        if event.widget is not self.root:
            return
        if getattr(self, "moving", False):
            return
        prev_x = getattr(self, "x", None)
        prev_y = getattr(self, "y", None)
        self._sync_kinito_screen_position()
        if prev_x == getattr(self, "x", None) and prev_y == getattr(self, "y", None):
            return
        self._follow_speech_bubble_to_kinito(self.x, self.y)

    def _stop_audio_for_drag(self) -> None:
        """Stop ambient background music on drag, but keep sing/poem and user songs."""
        if getattr(self, "_user_music_path", None):
            return
        if getattr(self, "_speech_accompaniment_active", False):
            return
        if hasattr(self, "stop_background_music"):
            self.stop_background_music()

    def on_mouse_down(self, event):
        """Begin dragging, stop roam sounds, and play the bomp click sound."""
        self.is_dragging = True
        self._drag_moved = False
        self.moving = False
        self._stop_audio_for_drag()
        if not self._should_skip_drag_sounds():
            self.play_sfx(bomp_file_path)
        self.root.update_idletasks()
        self._sync_kinito_screen_position()
        root_x = self.x
        root_y = self.y
        self.mouse_click_offset_x = root_x - event.x_root
        self.mouse_click_offset_y = root_y - event.y_root
        self._start_drag_tracking()
        if hasattr(self, "_capture_speech_bubble_drag_offset"):
            self._capture_speech_bubble_drag_offset()
        if hasattr(self, "_keep_assistant_on_top"):
            self._keep_assistant_on_top()

    def on_mouse_move(self, event):
        """Move the window while dragging and keep speech/love bubbles aligned."""
        if not self.is_dragging:
            return
        self._drag_moved = True
        new_x = event.x_root + self.mouse_click_offset_x
        new_y = event.y_root + self.mouse_click_offset_y
        new_x, new_y = self.clamp_position(new_x, new_y)
        self.x, self.y = new_x, new_y
        self.root.geometry(f"+{new_x}+{new_y}")
        self._follow_speech_bubble_to_kinito(new_x, new_y)

    def on_mouse_up(self, event):
        """End dragging and play the drop sound after a real drag."""
        if not self.is_dragging:
            return
        if self._drag_moved and not self._should_skip_drag_sounds():
            self.play_sfx(bomp_file_path)
        self.is_dragging = False
        self._drag_moved = False
        self._bubble_kinito_offset_x = None
        self._bubble_kinito_offset_y = None
        self._stop_drag_tracking()
        self._follow_speech_bubble_to_kinito()
        if hasattr(self, "ensure_on_screen"):
            self.root.after(0, self.ensure_on_screen)
        if hasattr(self, "_keep_assistant_on_top"):
            self.root.after(0, self._keep_assistant_on_top)

    def change_sprite(self, new_sprite):
        """Swap the visible sprite unless the user is currently dragging."""
        if self.is_dragging:
            return
        try:
            if self.panel.winfo_exists():
                self.panel.config(image=new_sprite)
        except tk.TclError:
            pass

    def _start_mouse_attention(self) -> None:
        """Begin polling the cursor for look-at / occasional follow behavior."""
        if getattr(self, "_mouse_attention_timer", None) is not None:
            return
        self._schedule_mouse_attention_poll()

    def _schedule_mouse_attention_poll(self) -> None:
        """Schedule the next mouse-attention tick on the Tk thread."""
        if not getattr(self, "_running", True):
            return
        schedule_after(
            self.root,
            self,
            "_mouse_attention_timer",
            self.MOUSE_LOOK_POLL_MS,
            self._update_mouse_attention,
        )

    def _stop_mouse_attention(self) -> None:
        """Cancel mouse-attention timers (e.g. on window destroy)."""
        cancel_after(self.root, self, "_mouse_attention_timer")
        cancel_after(self.root, self, "_mouse_think_timer")
        self._mouse_look_active = False
        if getattr(self, "_mouse_follow_state", "idle") == "thinking":
            self._mouse_follow_state = "idle"

    def _buddy_center(self) -> tuple[float, float]:
        """Return the screen-space center of Kinito's window."""
        width, height = 1, 1
        if hasattr(self, "_window_screen_size"):
            width, height = self._window_screen_size()
        else:
            try:
                width = max(int(self.root.winfo_width()), 1)
                height = max(int(self.root.winfo_height()), 1)
            except tk.TclError:
                pass
        x = float(getattr(self, "x", 0))
        y = float(getattr(self, "y", 0))
        return x + width / 2.0, y + height / 2.0

    def _cursor_screen_pos(self) -> tuple[float, float] | None:
        """Return the current pointer position in screen coordinates."""
        try:
            return float(self.root.winfo_pointerx()), float(self.root.winfo_pointery())
        except tk.TclError:
            return None

    def _can_look_at_mouse(self) -> bool:
        """Return True when mouse look may change the standing sprite."""
        if not getattr(self, "_running", True):
            return False
        if not getattr(self, "_startup_complete", False):
            return False
        if getattr(self, "paused", False) or getattr(self, "is_dragging", False):
            return False
        if getattr(self, "moving", False):
            return False
        if getattr(self, "_fancy_mode", False):
            return False
        if getattr(self, "_reading_idle_active", False):
            return False
        if getattr(self, "_hug_mode", False):
            return False
        if getattr(self, "_preserve_sprite", False):
            return False
        if getattr(self, "_ai_generating", False):
            return False
        if getattr(self, "_focus_mode", False):
            return False
        if getattr(self, "_is_game_active", lambda: False)():
            return False
        if getattr(self, "_chat_mode", False):
            return False
        if getattr(self, "talking", False):
            return False
        if getattr(self, "_awaiting_response", False):
            return False
        return not (hasattr(self, "_is_busy_with_speech") and self._is_busy_with_speech())

    def _can_follow_mouse(self) -> bool:
        """Return True when Kinito may start a think-then-maybe-follow attempt."""
        if not self._can_look_at_mouse():
            return False
        if getattr(self, "talking", False):
            return False
        if getattr(self, "_awaiting_response", False):
            return False
        if getattr(self, "_mouse_follow_state", "idle") != "idle":
            return False
        return time.monotonic() >= float(getattr(self, "_mouse_follow_ready_at", 0.0))

    def _mouse_attention_owns_sprite(self) -> bool:
        """Return True when idle animation must not overwrite mouse-driven sprites."""
        if getattr(self, "_mouse_look_active", False):
            return True
        return getattr(self, "_mouse_follow_state", "idle") in {"thinking", "chasing"}

    def _sprite_for_look_direction(self, direction: str, *, crouch: bool = False):
        """Return the PhotoImage for *direction*, falling back to center/front."""
        mapping = getattr(
            self,
            "_standing2_dir_sprites" if crouch else "_standing_dir_sprites",
            {},
        )
        if not isinstance(mapping, dict) or not mapping:
            return getattr(self, "tk_img_normal_2" if crouch else "tk_img_normal", None)
        return mapping.get(direction) or mapping.get("center") or getattr(
            self, "tk_img_normal_2" if crouch else "tk_img_normal", None
        )

    def _refresh_mouse_look_stance(self, *, force: bool = False) -> None:
        """Alternate standing and crouch about once per second while looking."""
        now = time.monotonic()
        until = float(getattr(self, "_mouse_look_stance_until", 0.0))
        if not force and now < until:
            return
        if force:
            self._mouse_look_crouch = False
        else:
            self._mouse_look_crouch = not bool(getattr(self, "_mouse_look_crouch", False))
        self._mouse_look_stance_until = now + float(self.MOUSE_LOOK_STANCE_SECONDS)

    def _apply_mouse_look_sprite(self, direction: str) -> None:
        """Show the standing or crouch sprite facing *direction*."""
        crouch = bool(getattr(self, "_mouse_look_crouch", False))
        sprite = self._sprite_for_look_direction(direction, crouch=crouch)
        if sprite is None:
            return
        self._mouse_look_direction = direction
        self.change_sprite(sprite)

    def _begin_mouse_follow_cooldown(self) -> None:
        """Start the post-attempt cooldown so follow stays occasional."""
        low, high = self.MOUSE_FOLLOW_COOLDOWN_SECONDS
        self._mouse_follow_ready_at = time.monotonic() + random.uniform(low, high)
        self._mouse_follow_state = "idle"
        cancel_after(self.root, self, "_mouse_think_timer")

    def _mouse_follow_target(self, cursor_x: float, cursor_y: float) -> tuple[float, float]:
        """Return a short window target toward the cursor (not a full chase)."""
        center_x, center_y = self._buddy_center()
        dx = cursor_x - center_x
        dy = cursor_y - center_y
        distance = math.hypot(dx, dy)
        max_dist = float(self.MOUSE_FOLLOW_MAX_PX)
        if distance > max_dist and distance > 0:
            scale = max_dist / distance
            dx *= scale
            dy *= scale
        return float(getattr(self, "x", 0)) + dx, float(getattr(self, "y", 0)) + dy

    def _start_mouse_think(self, cursor_x: float, cursor_y: float) -> None:
        """Enter a brief pause before deciding whether to follow (keep looking)."""
        self._mouse_follow_state = "thinking"
        # Keep the current look sprite — no Thinking pose for a maybe-no decision.
        self._mouse_look_active = True
        delay_ms = int(random.uniform(*self.MOUSE_THINK_SECONDS) * 1000)
        schedule_after(
            self.root,
            self,
            "_mouse_think_timer",
            delay_ms,
            lambda: self._finish_mouse_think(cursor_x, cursor_y),
        )

    def _finish_mouse_think(self, cursor_x: float, cursor_y: float) -> None:
        """Roll the follow chance after thinking; chase briefly or cool down."""
        if getattr(self, "_mouse_follow_state", "idle") != "thinking":
            return
        if getattr(self, "_chat_mode", False) or getattr(self, "talking", False):
            self._begin_mouse_follow_cooldown()
            return
        if getattr(self, "paused", False) or getattr(self, "is_dragging", False):
            self._mouse_follow_state = "idle"
            return
        if getattr(self, "_fancy_mode", False) or getattr(self, "_reading_idle_active", False):
            self._mouse_follow_state = "idle"
            return
        if getattr(self, "_hug_mode", False) or getattr(self, "_preserve_sprite", False):
            self._mouse_follow_state = "idle"
            return
        if getattr(self, "_ai_generating", False) or getattr(self, "_focus_mode", False):
            self._mouse_follow_state = "idle"
            return
        if getattr(self, "_is_game_active", lambda: False)():
            self._mouse_follow_state = "idle"
            return

        if random.random() >= self.MOUSE_FOLLOW_CHANCE:
            self._begin_mouse_follow_cooldown()
            return

        target_x, target_y = self._mouse_follow_target(cursor_x, cursor_y)
        self._mouse_follow_state = "chasing"
        self.moving = True

        def worker():
            try:
                self.play_sfx(surf_file_path)
                self.move_towards(target_x, target_y)
            finally:
                self.moving = False
                self._finish_surf_movement()
                self.root.after(0, self._on_mouse_chase_finished)

        threading.Thread(target=worker, daemon=True).start()

    def _on_mouse_chase_finished(self) -> None:
        """Return to idle/look after a short mouse follow."""
        self._begin_mouse_follow_cooldown()
        if hasattr(self, "ensure_on_screen"):
            self.ensure_on_screen()
        if hasattr(self, "_keep_assistant_on_top"):
            self._keep_assistant_on_top()

    def _update_mouse_attention(self) -> None:
        """Poll cursor proximity and update look / follow state."""
        try:
            if not getattr(self, "_running", True):
                return

            follow_state = getattr(self, "_mouse_follow_state", "idle")
            if follow_state == "chasing":
                self._schedule_mouse_attention_poll()
                return

            if not self._can_look_at_mouse():
                self._mouse_look_active = False
                self._mouse_look_crouch = False
                self._mouse_look_stance_until = 0.0
                self._schedule_mouse_attention_poll()
                return

            cursor = self._cursor_screen_pos()
            if cursor is None:
                self._mouse_look_active = False
                self._mouse_look_crouch = False
                self._mouse_look_stance_until = 0.0
                self._schedule_mouse_attention_poll()
                return

            cursor_x, cursor_y = cursor
            center_x, center_y = self._buddy_center()
            dx = cursor_x - center_x
            dy = cursor_y - center_y
            distance = math.hypot(dx, dy)

            if distance > self.MOUSE_LOOK_RADIUS_PX:
                was_looking = getattr(self, "_mouse_look_active", False)
                self._mouse_look_active = False
                if was_looking:
                    self._mouse_look_crouch = False
                    self._mouse_look_stance_until = 0.0
                self._schedule_mouse_attention_poll()
                return

            direction = look_direction_from_delta(
                dx,
                dy,
                deadzone_px=self.MOUSE_LOOK_DEADZONE_PX,
            )
            was_looking = getattr(self, "_mouse_look_active", False)
            self._mouse_look_active = True
            self._refresh_mouse_look_stance(force=not was_looking)
            self._apply_mouse_look_sprite(direction)

            # Already deciding whether to follow — keep looking, don't re-trigger.
            if follow_state == "thinking":
                self._schedule_mouse_attention_poll()
                return

            if distance <= self.MOUSE_FOLLOW_RADIUS_PX and self._can_follow_mouse():
                self._start_mouse_think(cursor_x, cursor_y)

            self._schedule_mouse_attention_poll()
        except Exception:
            # Never let mouse polling crash the assistant; reschedule next tick.
            try:
                self._schedule_mouse_attention_poll()
            except Exception:
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

    def _stop_roaming(self) -> None:
        """Abort an in-progress surf move so speech bubbles stay with Kinito."""
        self.moving = False
        self._finish_surf_movement()

    def _realign_speech_bubble_after_move(self) -> None:
        """Keep an open speech bubble anchored above Kinito after movement stops."""
        if not hasattr(self, "_has_active_speech_bubble"):
            return
        if not self._has_active_speech_bubble():
            return
        if hasattr(self, "position_speech_bubble"):
            self.root.after(0, self.position_speech_bubble)

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

    def _pick_normal_idle_sprite(self, *, crouch: bool = False):
        """Pick standing or crouch idle sprite; look-arounds are rare and cooled down."""
        if crouch:
            default = getattr(self, "tk_img_normal_2", None)
            variants = getattr(self, "_standing2_look_sprites", ())
        else:
            default = getattr(self, "tk_img_normal", None)
            variants = getattr(self, "_standing_look_sprites", ())

        if default is None:
            return None

        ready_at = getattr(self, "_look_around_ready_at", 0.0)
        on_cooldown = time.monotonic() < ready_at
        if (
            on_cooldown
            or not variants
            or random.random() < self.NORMAL_DEFAULT_LOOK_CHANCE
        ):
            return default

        self._look_around_ready_at = time.monotonic() + self.LOOK_AROUND_COOLDOWN_SECONDS
        return random.choice(variants)

    def maybe_trigger_screen_glitch(self) -> bool:
        """No-op unless GlitchMixin is mixed in."""
        return False

    def maybe_trigger_blue_screen(self) -> bool:
        """No-op unless GlitchMixin is mixed in."""
        return False

    def maybe_trigger_random_ad(self) -> bool:
        """No-op unless AdsMixin is mixed in."""
        return False

    def maybe_trigger_ambient_reminder(self) -> bool:
        """No-op unless NudgesMixin is mixed in."""
        return False

    def _is_reading_idle_active(self) -> bool:
        """Return True while Kinito is uninterrupted in the book-idle animation."""
        return (
            getattr(self, "_reading_idle_active", False)
            and self._running
            and not self.paused
            and not self.moving
            and not self.is_dragging
            and not getattr(self, "_focus_mode", False)
            and not getattr(self, "_fancy_mode", False)
            and (not self.talking or getattr(self, "_preserve_sprite", False))
        )

    def _can_play_reading_page_turn(self, session: int) -> bool:
        """Return True only while an uninterrupted reading-idle session is still active."""
        return (
            getattr(self, "_reading_idle_session", None) == session
            and getattr(self, "_reading_idle_active", False)
            and self._running
            and not self.paused
            and not self.moving
            and not self.is_dragging
            and not self.talking
            and not getattr(self, "_focus_mode", False)
            and not getattr(self, "_fancy_mode", False)
        )

    def _maybe_play_reading_page_turn(self, session: int, *, page_sprites=(), restore_sprite=None) -> bool:
        """Play a page-turn sound/animation during an active, uninterrupted reading idle."""
        if not self._can_play_reading_page_turn(session):
            return False
        if random.random() >= self.READING_PAGE_TURN_CHANCE:
            return False
        if not self._can_play_reading_page_turn(session):
            return False

        frames = tuple(page_sprites) if page_sprites else ()
        if frames:
            self.play_sfx(page_turn_file_path, volume=self.READING_PAGE_TURN_VOLUME)
            # Give pygame a moment to start audio before the visual flip.
            time.sleep(self.READING_PAGE_TURN_SOUND_LEAD_SECONDS)
            if not self._can_play_reading_page_turn(session):
                return True
            for sprite in frames:
                if not self._can_play_reading_page_turn(session):
                    return True
                self.change_sprite(sprite)
                time.sleep(self.READING_PAGE_TURN_FRAME_SECONDS)
            if restore_sprite is not None and self._is_reading_idle_active():
                self.change_sprite(restore_sprite)
            return True

        self.play_sfx(page_turn_file_path, volume=self.READING_PAGE_TURN_VOLUME)
        return True

    def _run_reading_idle(self):
        """Animate book sprites, optionally play page-turn sounds, and trigger speech."""
        use_glasses = random.random() < self.IDLE_GLASSES_CHANCE
        if use_glasses:
            reading_sprites = getattr(
                self,
                "_reading_glasses_sprites",
                getattr(self, "_reading_sprites", (self.tk_img_idle,)),
            )
            page_sprites = getattr(self, "_reading_glasses_page_sprites", ())
        else:
            reading_sprites = getattr(self, "_reading_sprites", (self.tk_img_idle,))
            page_sprites = getattr(self, "_reading_page_sprites", ())
        session = getattr(self, "_reading_idle_session", 0) + 1
        self._reading_idle_session = session
        self._reading_idle_active = True
        try:
            frame = 0
            self.change_sprite(reading_sprites[frame % len(reading_sprites)])
            if random.random() < self.READING_STORY_CHANCE:
                threading.Thread(target=self.offer_random_story, daemon=True).start()
            elif random.random() < self.READING_WISDOM_CHANCE:
                threading.Thread(target=self.say_random_wisdom, daemon=True).start()

            duration = random.randint(*self.READING_DURATION_SECONDS)
            elapsed = 0.0
            while elapsed < duration:
                if not self._is_reading_idle_active():
                    break
                time.sleep(self.READING_SPRITE_SWAP_SECONDS)
                elapsed += self.READING_SPRITE_SWAP_SECONDS
                if not self._is_reading_idle_active():
                    break
                frame += 1
                current = reading_sprites[frame % len(reading_sprites)]
                self.change_sprite(current)
                self._maybe_play_reading_page_turn(
                    session,
                    page_sprites=page_sprites,
                    restore_sprite=current,
                )
        finally:
            if getattr(self, "_reading_idle_session", None) == session:
                self._reading_idle_active = False

    def smooth_movement(self):
        """Background loop: roam the screen or trigger spontaneous speech/actions."""
        while self._running:
            if (
                self.paused
                or self.is_dragging
                or not self._startup_complete
                or self._is_busy_with_speech()
                or self._is_background_music_playing()
                or getattr(self, "_reading_idle_active", False)
                or getattr(self, "_mouse_follow_state", "idle") in {"thinking", "chasing"}
            ):
                time.sleep(0.1)
                continue
            self.maybe_trigger_screen_glitch()
            self.maybe_trigger_blue_screen()
            self.maybe_trigger_random_ad()
            self.maybe_trigger_ambient_reminder()
            if (
                random.random() < self.SPONTANEOUS_CHANCE
                and self._allow_random_questions
                and not getattr(self, "_focus_mode", False)
                and not getattr(self, "_is_game_active", lambda: False)()
            ):
                if random.random() < self.MENU_ACTION_CHANCE:
                    self.perform_random_menu_action()
                elif random.random() < self.MEMORY_QUESTION_CHANCE:
                    self.speak_memory_question_idle()
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
                if hasattr(self, "_keep_assistant_on_top"):
                    self.root.after(0, self._keep_assistant_on_top)
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
            if self.paused or self.is_dragging or self._is_busy_with_speech():
                self._finish_surf_movement()
                self._realign_speech_bubble_after_move()
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
                if self._mouse_attention_owns_sprite():
                    time.sleep(0.25)
                    continue
                idle_roll = random.random()
                focus_mode = getattr(self, "_focus_mode", False)
                game_active = getattr(self, "_is_game_active", lambda: False)()
                if (
                    not focus_mode
                    and not game_active
                    and idle_roll < self.IDLE_READING_CHANCE
                    and self._allow_random_questions
                ):
                    self._run_reading_idle()
                    continue
                if (
                    not focus_mode
                    and not game_active
                    and idle_roll < self.IDLE_READING_CHANCE + self.IDLE_FANCY_CHANCE
                    and self._allow_random_questions
                ):
                    self._run_fancy_idle()
                    continue
                self.change_sprite(self._pick_normal_idle_sprite(crouch=False))
                time.sleep(1)
                if not self._running:
                    break
                if self._mouse_attention_owns_sprite():
                    continue
                self.change_sprite(self._pick_normal_idle_sprite(crouch=True))
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
