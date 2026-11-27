"""Mini companion pets that wander the desktop near Kinito."""

from __future__ import annotations

import math
import random
import time
import tkinter as tk
from tkinter import Frame, IntVar, Label, Scale, Toplevel

from PIL import Image, ImageTk

from content import dialogue as dlg
from kinito.assets import bomp_file_path
from kinito.tk_timers import cancel_after, schedule_after
from kinito.tk_toplevels import (
    create_staged_toplevel,
    detach_toplevel_owner,
    reveal_staged_toplevel,
)
from kinito.window_icon import apply_window_icon

PET_STATE_FOLLOW = "follow"
PET_STATE_WANDER = "wander"
PET_STATE_MOUSE = "mouse"
PET_STATE_SLEEP = "sleep"
PET_STATE_REST = "rest"
PET_STATE_HOPOUT = "hopout"
PET_STATE_DANCE = "dance"
PET_STATE_LEAVE = "leave"

_TRANSPARENT = "#ff00ff"
_UI_BG = "#e6ded5"


def _composite_on_chroma(img: Image.Image) -> Image.Image:
    """Flatten RGBA onto the chroma key used by -transparentcolor."""
    bg = Image.new("RGBA", img.size, (255, 0, 255, 255))
    bg.alpha_composite(img)
    return bg.convert("RGB")


# Which way the base sprite faces (some minis are drawn looking left).
PET_BASE_FACING = {"kinito": "left", "jade": "left"}


def _load_pet_photos(sprite: dict, scale: float = 1.0) -> dict:
    """Build Tk PhotoImages (right/left-facing, optional sleep) for a sprite."""
    photos: dict = {}
    try:
        img = Image.open(sprite["path"]).convert("RGBA")
    except (OSError, KeyError):
        return photos
    if abs(scale - 1.0) > 0.02:
        size = (
            max(1, int(round(img.width * scale))),
            max(1, int(round(img.height * scale))),
        )
        img = img.resize(size, Image.Resampling.NEAREST)
    flipped = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    if PET_BASE_FACING.get(sprite.get("id", ""), "right") == "left":
        img, flipped = flipped, img
    photos["right"] = ImageTk.PhotoImage(_composite_on_chroma(img))
    photos["left"] = ImageTk.PhotoImage(_composite_on_chroma(flipped))
    sleep_path = sprite.get("sleep_path") or ""
    if sleep_path:
        try:
            sleep_img = Image.open(sleep_path).convert("RGBA")
            if abs(scale - 1.0) > 0.02:
                sleep_img = sleep_img.resize(
                    (
                        max(1, int(round(sleep_img.width * scale))),
                        max(1, int(round(sleep_img.height * scale))),
                    ),
                    Image.Resampling.NEAREST,
                )
            photos["sleep"] = ImageTk.PhotoImage(_composite_on_chroma(sleep_img))
        except OSError:
            pass
    return photos


class MiniPet:
    """One small companion window with a wander/follow/sleep state machine."""

    def __init__(self, app, sprite: dict, photos: dict):
        self.app = app
        self.sprite_id = sprite["id"]
        self.name = sprite["name"]
        self.photos = photos
        self.window = None
        self.label = None
        self.dismiss_popup = None
        self.x = 0.0
        self.y = 0.0
        self.state = PET_STATE_FOLLOW
        self.target: tuple[float, float] | None = None
        self.facing_left = False
        self.sleeping = False
        self.hop_phase = random.random() * math.tau
        self.dance_phase = 0.0
        self.dance_until = 0.0
        self.mouse_until = 0.0
        self.idle_until = 0.0
        self.away_since: float | None = None
        self.rest_until = 0.0
        self.hop_until = 0.0
        self.hurry_until = 0.0
        self.idle_hop_until = 0.0
        self.rest_after_wander = True
        self.social: dict | None = None
        self.orbit_angle = random.uniform(0, math.tau)
        self.dragging = False
        self._drag_offset = (0, 0)
        self._drag_moved = False
        self.destroyed = False

    # -- window lifecycle ------------------------------------------------

    def create_window(self, x: float, y: float) -> None:
        """Create the borderless transparent pet window at (*x*, *y*)."""
        self.x, self.y = float(x), float(y)
        window = create_staged_toplevel(self.app.root)
        window.overrideredirect(True)
        window.configure(bg=_TRANSPARENT)
        try:
            window.attributes("-transparentcolor", _TRANSPARENT)
        except tk.TclError:
            pass
        label = Label(
            window,
            image=self.photos.get("right"),
            bg=_TRANSPARENT,
            bd=0,
            highlightthickness=0,
        )
        label.pack()
        label.bind("<Button-1>", self._on_drag_start)
        label.bind("<B1-Motion>", self._on_drag_move)
        label.bind("<ButtonRelease-1>", self._on_drag_end)
        label.bind("<Button-3>", self._on_right_click)
        window.bind("<Button-3>", self._on_right_click)
        window.update_idletasks()
        w = max(window.winfo_reqwidth(), 1)
        h = max(window.winfo_reqheight(), 1)
        reveal_staged_toplevel(
            window, geometry=f"{w}x{h}+{int(self.x)}+{int(self.y)}", noactivate=True
        )
        self.window = window
        self.label = label

    def _on_drag_start(self, event=None):
        """Begin dragging the pet with the left mouse button."""
        self.dragging = True
        self._drag_moved = False
        self.social = None
        self._close_dismiss_popup()
        play = getattr(self.app, "play_sfx", None)
        if callable(play):
            play(bomp_file_path)
        try:
            self._drag_offset = (
                int(event.x_root) - int(round(self.x)),
                int(event.y_root) - int(round(self.y)),
            )
        except (AttributeError, TypeError):
            self._drag_offset = (0, 0)

    def _on_drag_move(self, event=None):
        """Follow the cursor while held."""
        if not self.dragging:
            return
        try:
            new_x = float(int(event.x_root) - self._drag_offset[0])
            new_y = float(int(event.y_root) - self._drag_offset[1])
        except (AttributeError, TypeError):
            return
        if abs(new_x - self.x) > 2.0:
            facing_left = new_x < self.x
            if facing_left != self.facing_left:
                self.facing_left = facing_left
                self._set_image("left" if facing_left else "right")
        self._drag_moved = True
        self.x, self.y = new_x, new_y
        self._place(self.x, self.y)

    def _on_drag_end(self, _event=None):
        """Release the pet; it resumes its behavior from the drop point."""
        if not self.dragging:
            return
        self.dragging = False
        if self._drag_moved:
            play = getattr(self.app, "play_sfx", None)
            if callable(play):
                play(bomp_file_path)
        self.away_since = None
        self.idle_until = 0.0
        if self.state == PET_STATE_LEAVE:
            self.target = self.app._pet_exit_point_for(self)

    def _on_right_click(self, event=None):
        """Offer a small 'Send away' button next to the pet."""
        if self.dismiss_popup is not None:
            try:
                if self.dismiss_popup.winfo_exists():
                    self.dismiss_popup.destroy()
            except tk.TclError:
                pass
            self.dismiss_popup = None
        popup = Toplevel(self.window or self.app.root)
        popup.wm_overrideredirect(True)
        popup.wm_attributes("-topmost", True)
        detach_toplevel_owner(popup)
        button = tk.Button(
            popup,
            text="Send away",
            command=self._send_away_clicked,
            padx=8,
            pady=2,
        )
        button.pack()
        popup.update_idletasks()
        pw, ph = self._pet_draw_size()
        pop_w = max(popup.winfo_reqwidth(), 1)
        pop_h = max(popup.winfo_reqheight(), 1)
        pop_x = self.x + pw / 2 - pop_w / 2
        rect = self.app._pet_work_rect(self.x, self.y)
        if rect is not None and self.y - pop_h - 6 >= rect[1]:
            pop_y = self.y - pop_h - 6  # above the sprite
        else:
            pop_y = self.y + ph + 6  # below when there's no room on top
        pop_x, pop_y = self.app._pet_clamp_point(pop_x, pop_y)
        popup.geometry(f"+{int(pop_x)}+{int(pop_y)}")
        self.dismiss_popup = popup
        self.app.root.after(4000, self._close_dismiss_popup)

    def _close_dismiss_popup(self):
        popup = self.dismiss_popup
        self.dismiss_popup = None
        if popup is None:
            return
        try:
            if popup.winfo_exists():
                popup.destroy()
        except tk.TclError:
            pass

    def _send_away_clicked(self):
        self._close_dismiss_popup()
        self.app.dismiss_pet(self)

    def destroy(self) -> None:
        """Tear down the pet window immediately."""
        self.destroyed = True
        self._close_dismiss_popup()
        window = self.window
        self.window = None
        self.label = None
        if window is None:
            return
        try:
            if window.winfo_exists():
                window.destroy()
        except tk.TclError:
            pass

    # -- per-tick behavior ------------------------------------------------

    def _set_image(self, key: str, *, mirror: bool = False) -> None:
        if self.label is None:
            return
        photo = self.photos.get(key)
        if photo is None and key == "sleep":
            photo = self.photos.get("left" if self.facing_left else "right")
        if photo is None:
            return
        try:
            self.label.config(image=photo)
        except tk.TclError:
            pass

    def _place(self, draw_x: float, draw_y: float) -> None:
        if self.window is None:
            return
        try:
            self.window.geometry(f"+{int(draw_x)}+{int(draw_y)}")
        except tk.TclError:
            pass

    def tick(self, now: float) -> None:
        """Advance the pet's state machine; called every PET_TICK_MS."""
        app = self.app
        if self.destroyed or self.window is None:
            return
        try:
            if not self.window.winfo_exists():
                self.destroyed = True
                return
        except tk.TclError:
            self.destroyed = True
            return

        if self.dragging and self.state != PET_STATE_HOPOUT:
            return

        if self.state == PET_STATE_HOPOUT:
            if now >= self.hop_until:
                self.destroy()
                return
            self.hop_phase += 0.5
            hop = abs(math.sin(self.hop_phase)) * 12.0
            self._place(self.x, self.y - hop)
            return

        if self.state == PET_STATE_LEAVE:
            # Direction stays fixed once chosen — recomputing every tick makes
            # the pet ping-pong at monitor seams. Drags retarget on release.
            if self.target is None:
                self.target = app._pet_exit_point_for(self)
            self._move_toward(now, speed=app.PET_LEAVE_SPEED_PX)
            if self._leave_target_reached():
                self.destroy()
            return

        anchor = app._pet_anchor_for(self)
        dist = math.hypot(anchor[0] - self.x, anchor[1] - self.y)

        if getattr(app, "paused", False):
            self.state = PET_STATE_SLEEP
            self.target = app._pet_sleep_spot_for(self)
            if not self._target_reached(0.5):
                self.sleeping = False
                self._set_image("left" if self.facing_left else "right")
                if (
                    now >= self.hurry_until
                    and random.random() < app.PET_HURRY_CHANCE
                ):
                    self.hurry_until = now + random.uniform(
                        *app.PET_HURRY_SECONDS
                    )
                self._move_toward(now, speed=app.PET_SPEED_PX)
            if self._target_reached(0.5):
                self.x, self.y = self.target
                self.sleeping = True
                self._set_image("sleep")
                self._place(self.x, self.y)
            return

        if self.state == PET_STATE_SLEEP:
            self.sleeping = False
            self.state = PET_STATE_FOLLOW
            self._set_image("left" if self.facing_left else "right")

        # Return rule: long time away -> head back to Kinito. Wander targets
        # may lie anywhere on the desktop, so distance alone never recalls.
        if dist > app.PET_NEAR_RADIUS:
            if self.away_since is None:
                self.away_since = now
            if now - self.away_since > app.PET_RETURN_AFTER_SECONDS:
                self.state = PET_STATE_FOLLOW
                self.target = None
                self.social = None
        else:
            self.away_since = None

        if self.social is not None:
            prev_state = self.state
            if self._social_step(now):
                return
            self.social = None
            if self.state == prev_state:
                # The interaction may have moved the pet into its own end
                # state (e.g. resting at a shared destination); only reset
                # to following when it didn't.
                self.state = PET_STATE_FOLLOW
                self.target = None
                self.idle_until = now + random.uniform(
                    *app.PET_DECIDE_INTERVAL_SECONDS
                )

        if self.state == PET_STATE_DANCE:
            if now < self.dance_until and app._is_pet_music_playing():
                self._dance_step(now)
                return
            self.state = PET_STATE_FOLLOW

        if app._is_pet_music_playing() and random.random() < app.PET_DANCE_CHANCE:
            self.state = PET_STATE_DANCE
            self.dance_until = now + random.uniform(*app.PET_DANCE_SECONDS)
            self._dance_step(now)
            return

        if self.state == PET_STATE_FOLLOW:
            if dist > app.PET_NEAR_RADIUS * 0.4:
                self.target = anchor
                if (
                    now >= self.hurry_until
                    and dist > app.PET_NEAR_RADIUS
                    and random.random() < app.PET_HURRY_CHANCE
                ):
                    self.hurry_until = now + random.uniform(*app.PET_HURRY_SECONDS)
                self._move_toward(now)
            else:
                self.target = None
                self._stand_still(now)
                if now >= self.idle_until:
                    roll = random.random()
                    if roll < app.PET_WANDER_CHANCE:
                        self.state = PET_STATE_WANDER
                        self.rest_after_wander = True
                        self.target = app._pet_random_screen_point(self)
                    elif roll < app.PET_WANDER_CHANCE + app.PET_CIRCLE_CHANCE:
                        # Stroll to another spot on Kinito's orbit ring, no rest.
                        self.state = PET_STATE_WANDER
                        self.rest_after_wander = False
                        self.orbit_angle = random.uniform(0, math.tau)
                        self.target = app._pet_anchor_for(self)
                    elif roll < (
                        app.PET_WANDER_CHANCE
                        + app.PET_CIRCLE_CHANCE
                        + app.PET_MOUSE_CHANCE
                    ):
                        cursor = app._pet_cursor_point()
                        if cursor is not None:
                            self.state = PET_STATE_MOUSE
                            self.mouse_until = now + app.PET_MOUSE_FOLLOW_SECONDS
                            self.target = cursor
                    elif roll < (
                        app.PET_WANDER_CHANCE
                        + app.PET_CIRCLE_CHANCE
                        + app.PET_MOUSE_CHANCE
                        + app.PET_IDLE_HOP_CHANCE
                    ):
                        self.idle_hop_until = now + random.uniform(
                            *app.PET_IDLE_HOP_SECONDS
                        )
                    elif roll < (
                        app.PET_WANDER_CHANCE
                        + app.PET_CIRCLE_CHANCE
                        + app.PET_MOUSE_CHANCE
                        + app.PET_IDLE_HOP_CHANCE
                        + app.PET_SOCIAL_CHANCE
                    ):
                        app._pet_try_social(self)
                    self.idle_until = now + random.uniform(
                        *app.PET_DECIDE_INTERVAL_SECONDS
                    )
        elif self.state == PET_STATE_WANDER:
            if self.target is None:
                self.state = PET_STATE_FOLLOW
                return
            if now >= self.hurry_until and random.random() < app.PET_HURRY_CHANCE:
                self.hurry_until = now + random.uniform(*app.PET_HURRY_SECONDS)
            self._move_toward(now)
            if self._target_reached(app.PET_ARRIVE_RADIUS):
                self.target = None
                if self.rest_after_wander:
                    self.state = PET_STATE_REST
                    self.rest_until = now + random.uniform(*app.PET_REST_SECONDS)
                else:
                    self.state = PET_STATE_FOLLOW
                    self.idle_until = now + random.uniform(
                        *app.PET_DECIDE_INTERVAL_SECONDS
                    )
        elif self.state == PET_STATE_REST:
            if now >= self.rest_until:
                self.state = PET_STATE_FOLLOW
                self.idle_until = now + random.uniform(
                    *app.PET_DECIDE_INTERVAL_SECONDS
                )
                return
            self._stand_still()
        elif self.state == PET_STATE_MOUSE:
            if now >= self.mouse_until:
                self.state = PET_STATE_FOLLOW
                self.target = None
                return
            cursor = app._pet_cursor_point()
            if cursor is None:
                self.state = PET_STATE_FOLLOW
                self.target = None
                return
            # Rest on a ring around the cursor on the side the pet approached
            # from — pets coming from the left stay left, from below stay below.
            pw, ph = self._pet_draw_size()
            dx = (self.x + pw / 2) - cursor[0]
            dy = (self.y + ph / 2) - cursor[1]
            dist = math.hypot(dx, dy)
            offset = app.PET_MOUSE_REST_OFFSET
            if dist > 0.5:
                tx = cursor[0] + dx / dist * offset - pw / 2
                ty = cursor[1] + dy / dist * offset - ph / 2
            else:
                tx, ty = cursor
            self.target = app._pet_clamp_point(tx, ty)
            self._move_toward(now, speed=app.PET_SPEED_PX * 1.3)
            if self._target_reached(app.PET_ARRIVE_RADIUS * 1.5):
                self._stand_still(now)

    def _social_step(self, now: float) -> bool:
        """Run one tick of a pet-to-pet interaction; True while engaged."""
        s = self.social
        app = self.app
        partner = s.get("partner")
        if partner is not None and (partner.destroyed or partner.dragging):
            return False
        kind = s["kind"]
        if now >= s.get("until", now):
            return False

        if kind == "chase":
            if now < s.get("start_at", 0):
                self.target = None
                self._stand_still(now)
                return True
            angle = s.get("angle", 0.0)
            self.target = (
                partner.x + math.cos(angle) * 60.0,
                partner.y + math.sin(angle) * 60.0,
            )
            self._move_toward(now, speed=app.PET_SPEED_PX * 1.6)
            return True
        if kind == "flee":
            chasers = [
                c for c in s.get("chasers", [partner])
                if c is not None and not c.destroyed and not c.dragging
            ]
            if not chasers:
                return False
            threat = min(
                chasers, key=lambda c: math.hypot(c.x - self.x, c.y - self.y)
            )
            dx, dy = self.x - threat.x, self.y - threat.y
            dist = math.hypot(dx, dy) or 1.0
            if dist > 100.0 and self.target is None:
                self._stand_still(now)
                return True
            if self.target is None or self._target_reached(
                app.PET_ARRIVE_RADIUS * 2
            ):
                self.target = app._pet_clamp_point(
                    self.x + dx / dist * 150 + random.uniform(-40, 40),
                    self.y + dy / dist * 150 + random.uniform(-40, 40),
                )
            self._move_toward(now, speed=app.PET_SPEED_PX * 1.4)
            return True
        if kind == "circle":
            s["angle"] += 0.09
            radius = 55.0
            self.target = (
                partner.x + math.cos(s["angle"]) * radius,
                partner.y + math.sin(s["angle"]) * radius,
            )
            self._move_toward(now, speed=app.PET_SPEED_PX * 1.3)
            return True
        if kind == "orbit":
            s["angle"] += 0.07
            radius = 100.0
            self.target = (
                s["point"][0] + math.cos(s["angle"]) * radius,
                s["point"][1] + math.sin(s["angle"]) * radius + 30.0,
            )
            self._move_toward(now, speed=app.PET_SPEED_PX * 1.4)
            return True
        if kind == "leapfrog_post":
            leaper = s.get("leaper")
            if (
                leaper is None
                or leaper.destroyed
                or leaper.dragging
                or not leaper.social
                or leaper.social.get("kind") != "leapfrog"
            ):
                return False
            self.target = s.get("point")
            if self.target and not self._target_reached(app.PET_ARRIVE_RADIUS):
                self._move_toward(now)
                return True
            self.target = None
            self._stand_still(now)
            return True
        if kind == "leapfrog":
            posts = [
                p
                for p in s.get("posts", [])
                if not p.destroyed and not p.dragging
            ]
            if not posts:
                return False
            s["posts"] = posts
            for post in posts:
                slot = post.social.get("point") if post.social else None
                if slot and math.hypot(post.x - slot[0], post.y - slot[1]) > 40:
                    self.target = None
                    self._stand_still(now)
                    return True
            direction = s.get("dir", 1.0)
            index = s.get("index", -1)
            if index < 0:
                first = posts[0]
                self.target = (first.x - direction * 70.0, first.y)
                if not self._target_reached(app.PET_ARRIVE_RADIUS):
                    self._move_toward(now, speed=app.PET_SPEED_PX * 1.3)
                    return True
                s["index"] = 0
                return True
            if index >= len(posts):
                return False
            if now < s.get("pause_until", 0):
                self.target = None
                self._stand_still(now)
                return True
            post = posts[index]
            goal = post.x + direction * 60.0
            if (self.x - goal) * direction >= -2.0:
                s["index"] = index + 1
                s["pause_until"] = now + 0.4
                self.target = None
                return True
            self.hurry_until = now + 0.6
            self.target = (goal, post.y)
            self._move_toward(now, speed=app.PET_SPEED_PX * 1.2)
            return True
        if kind == "pounce":
            ax, ay = app._pet_clamp_point(*app._pet_anchor_point())
            dx, dy = ax - self.x, ay - self.y
            dist = math.hypot(dx, dy) or 1.0
            if not s.get("jumped"):
                if dist > 55.0:
                    self.target = (ax, ay)
                    self._move_toward(now, speed=app.PET_SPEED_PX * 1.4)
                    return True
                s["jumped"] = True
                s["jump_t0"] = now
            if now - s.get("jump_t0", now) < 0.9:
                # Big hop right at Kinito.
                self._face_x(ax)
                self.hop_phase += 0.6
                hop = abs(math.sin(self.hop_phase)) * 14.0
                self.x += dx / dist * 1.5
                self._place(self.x, self.y - hop)
                return True
            return False
        if kind == "piggy_throw":
            piggy = s.get("piggy")
            if (
                piggy is None
                or piggy.destroyed
                or piggy.dragging
                or not piggy.social
                or piggy.social.get("kind") not in ("piggy_mid", "piggy_fly")
            ):
                return False
            piggy_s = piggy.social
            if (
                piggy_s["kind"] == "piggy_fly"
                or piggy_s.get("active") is not self
                or not piggy_s.get("ready")
            ):
                # Take the standoff position first — a thrower that is
                # already next to the middle pet must still step back to
                # its post, otherwise the shoves become instant ping-pong.
                post = s.get("post")
                if post:
                    self.target = post
                    if not self._target_reached(app.PET_ARRIVE_RADIUS):
                        self._move_toward(now)
                        return True
                self.target = None
                self._face_x(piggy.x)
                self._stand_still(now)
                return True
            other = next(
                (
                    t
                    for t in piggy_s.get("throwers", [])
                    if t is not self and not t.destroyed and not t.dragging
                ),
                None,
            )
            if other is None:
                return False
            dist = math.hypot(piggy.x - self.x, piggy.y - self.y) or 1.0
            if dist > 48.0:
                self.target = (piggy.x, piggy.y)
                self._move_toward(now, speed=app.PET_SPEED_PX * 1.3)
                return True
            tx, ty = other.x - self.x, other.y - self.y
            td = math.hypot(tx, ty) or 1.0
            goal = app._pet_clamp_point(
                other.x - tx / td * 55.0,
                other.y - ty / td * 55.0,
            )
            flight_dist = math.hypot(goal[0] - piggy.x, goal[1] - piggy.y)
            piggy.social = {
                "kind": "piggy_fly",
                "throwers": piggy_s.get("throwers", []),
                "active": other,
                "from_pos": (piggy.x, piggy.y),
                "target": goal,
                "t0": now,
                "dur": max(
                    0.5,
                    flight_dist
                    / (app.PET_SPEED_PX * 1.15)
                    * (app.PET_TICK_MS / 1000.0),
                ),
                "until": s["until"],
            }
            self.target = None
            self._face_x(piggy.x)
            self._stand_still(now)
            return True
        if kind == "piggy_mid":
            throwers = [
                t
                for t in s.get("throwers", [])
                if not t.destroyed and not t.dragging
            ]
            if not throwers:
                return False
            s["throwers"] = throwers
            active = s.get("active")
            if active is None or active.destroyed or active.dragging:
                s["active"] = throwers[0]
            if not s.get("ready") and all(
                (t.social or {}).get("post") is None
                or math.hypot(
                    t.x - t.social["post"][0], t.y - t.social["post"][1]
                )
                < 60.0
                for t in throwers
            ):
                s["ready"] = True
                # Now the actual game clock starts for everyone.
                end = now + s.get("duration", 10.0)
                s["until"] = end
                for t in throwers:
                    if t.social:
                        t.social["until"] = end
            self.target = None
            self._stand_still(now)
            return True
        if kind == "piggy_fly":
            # Parabolic lob between the throwers, not a ground-level hop.
            x0, y0 = s.get("from_pos", (self.x, self.y))
            x1, y1 = s["target"]
            dur = max(0.1, s.get("dur", 1.0))
            progress = min(1.0, (now - s.get("t0", now)) / dur)
            self.x = x0 + (x1 - x0) * progress
            self.y = y0 + (y1 - y0) * progress
            self._face_x(x1)
            arc = math.sin(math.pi * progress) * 55.0
            self._place(self.x, self.y - arc)
            if progress >= 1.0:
                self.social = {
                    "kind": "piggy_mid",
                    "throwers": s.get("throwers", []),
                    "active": s.get("active"),
                    "ready": True,
                    "until": s.get("until", now),
                }
                self.target = None
                self._stand_still(now)
                return True
            return True
        if kind in ("visit", "push"):
            stop = 55.0 if kind == "visit" else 45.0
            dx, dy = self.x - partner.x, self.y - partner.y
            dist = math.hypot(dx, dy) or 1.0
            self.target = (
                partner.x + dx / dist * stop,
                partner.y + dy / dist * stop,
            )
            if not self._target_reached(app.PET_ARRIVE_RADIUS):
                self._move_toward(now, speed=app.PET_SPEED_PX * 1.2)
                return True
            if kind == "visit":
                self.idle_hop_until = now + 0.6
                self._stand_still(now)
            else:
                partner.social = {
                    "kind": "shoved",
                    "dir": (-dx / dist, -dy / dist),
                    "until": now + 0.45,
                }
            return False
        if kind == "shoved":
            dx, dy = s["dir"]
            self.x, self.y = app._pet_clamp_point(
                self.x + dx * 4.0, self.y + dy * 4.0
            )
            self.hop_phase += 0.6
            hop = abs(math.sin(self.hop_phase)) * 8.0
            self._place(self.x, self.y - hop)
            return True
        if kind == "together":
            self.target = s["point"]
            if self._target_reached(app.PET_ARRIVE_RADIUS):
                # Stay at the shared destination instead of heading straight
                # back — travel time does not count as time spent there.
                self.state = PET_STATE_REST
                self.target = None
                self.rest_until = now + random.uniform(20.0, 50.0)
                self._stand_still(now)
                return False
            self._move_toward(now)
            return True
        return False

    def _pet_draw_size(self) -> tuple[float, float]:
        """Largest sprite photo size, for center-based positioning."""
        try:
            return (
                max(photo.width() for photo in self.photos.values()),
                max(photo.height() for photo in self.photos.values()),
            )
        except (ValueError, TypeError, tk.TclError):
            return 60.0, 50.0

    def _leave_target_reached(self) -> bool:
        if self.target is None:
            return True
        return math.hypot(self.target[0] - self.x, self.target[1] - self.y) < 4.0

    def _target_reached(self, radius: float) -> bool:
        if self.target is None:
            return True
        return (
            math.hypot(self.target[0] - self.x, self.target[1] - self.y) <= radius
        )

    def _stand_still(self, now: float | None = None) -> None:
        hop = 0.0
        if now is not None and now < self.idle_hop_until:
            self.hop_phase += 0.5
            hop = abs(math.sin(self.hop_phase)) * 6.0
        self._set_image("left" if self.facing_left else "right")
        self._place(self.x, self.y - hop)

    def _face_x(self, x: float) -> None:
        """Turn the sprite to face the given screen x."""
        facing_left = x < self.x
        if facing_left != self.facing_left:
            self.facing_left = facing_left
            self._set_image("left" if facing_left else "right")

    def _dance_step(self, now: float) -> None:
        self.dance_phase += 0.45
        bounce = abs(math.sin(self.dance_phase)) * 10.0
        if random.random() < 0.06:
            self.facing_left = not self.facing_left
            self._set_image("left" if self.facing_left else "right")
        self._place(self.x, self.y - bounce)

    def _move_toward(self, now: float, *, speed: float | None = None) -> None:
        if self.target is None:
            self._stand_still()
            return
        speed = speed if speed is not None else self.app.PET_SPEED_PX
        hop_height = 5.0
        if now < self.hurry_until:
            speed *= self.app.PET_HURRY_SPEED_MULT
            hop_height *= self.app.PET_HURRY_HOP_MULT
        dx = self.target[0] - self.x
        dy = self.target[1] - self.y
        dist = math.hypot(dx, dy)
        if dist < 0.5:
            self._stand_still()
            return
        step = min(speed, dist)
        self.x += dx / dist * step
        self.y += dy / dist * step
        if abs(dx) > 2.0:
            facing_left = dx < 0
            if facing_left != self.facing_left:
                self.facing_left = facing_left
                self._set_image("left" if facing_left else "right")
        self.hop_phase += 0.5
        hop = abs(math.sin(self.hop_phase)) * hop_height
        self._place(self.x, self.y - hop)


class PetsMixin:
    """Spawn, manage, and dismiss small desktop pets around Kinito."""

    PET_TICK_MS = 50
    PET_SPEED_PX = 3.0
    PET_LEAVE_SPEED_PX = 7.0
    PET_ARRIVE_RADIUS = 18.0
    PET_NEAR_RADIUS = 220.0
    PET_RETURN_AFTER_SECONDS = 120.0
    PET_REST_SECONDS = (30.0, 90.0)
    PET_HURRY_CHANCE = 0.02
    PET_HURRY_SECONDS = (1.0, 2.5)
    PET_HURRY_SPEED_MULT = 2.2
    PET_HURRY_HOP_MULT = 2.0
    PET_HOPOUT_SECONDS = (0.9, 1.6)
    PET_MOUSE_FOLLOW_SECONDS = 15.0
    PET_MOUSE_REST_OFFSET = 30.0
    PET_WANDER_CHANCE = 0.03
    PET_CIRCLE_CHANCE = 0.05
    PET_MOUSE_CHANCE = 0.01
    PET_IDLE_HOP_CHANCE = 0.04
    PET_IDLE_HOP_SECONDS = (0.4, 0.9)
    PET_SOCIAL_CHANCE = 0.04
    PET_DECIDE_INTERVAL_SECONDS = (4.0, 9.0)
    PET_DANCE_CHANCE = 0.02
    PET_DANCE_SECONDS = (2.0, 5.0)
    PET_SPAWN_CHANCE = 1 / 500
    PET_SPAWN_COOLDOWN_SECONDS = 240
    PET_DISMISS_CHANCE = 1 / 600
    PET_DISMISS_COOLDOWN_SECONDS = 300
    PET_SUMMON_LINE_CHANCE = 0.5
    PET_MAX_HARD = 3
    PET_ORBIT_RADIUS_X = 130.0
    PET_ORBIT_RADIUS_Y = 75.0
    PET_RENDER_SCALE = 0.5
    PET_SETTINGS_WIDTH = 360
    PET_SETTINGS_HEIGHT = 370

    # -- sprite catalog / settings ---------------------------------------

    def _mini_sprite_catalog(self) -> list[dict]:
        catalog = getattr(self, "_pet_sprite_catalog", None)
        if catalog is None:
            from kinito.assets import list_mini_sprites

            catalog = list_mini_sprites()
            self._pet_sprite_catalog = catalog
        return catalog

    def _pet_max_count(self) -> int:
        from kinito.settings_store import clamp_pets_max_count

        return clamp_pets_max_count(getattr(self, "_pets_max_count", 1))

    def _enabled_pet_sprite_ids(self) -> set[str]:
        enabled = getattr(self, "_pet_enabled_sprites", None)
        ids = {entry["id"] for entry in self._mini_sprite_catalog()}
        if enabled is None:
            return ids
        return {str(sprite_id) for sprite_id in enabled} & ids

    def _pick_pet_sprite(self, sprite_id: str | None = None) -> dict | None:
        enabled = self._enabled_pet_sprite_ids()
        catalog = [
            entry for entry in self._mini_sprite_catalog() if entry["id"] in enabled
        ]
        if sprite_id is not None:
            for entry in catalog:
                if entry["id"] == sprite_id:
                    return entry
            return None
        if not catalog:
            return None
        return random.choice(catalog)

    # -- spawn / dismiss ---------------------------------------------------

    def toggle_pets(self) -> None:
        """Turn pet visits on/off (Settings → Turn on/off)."""
        self._pets_enabled = not getattr(self, "_pets_enabled", True)
        if self._pets_enabled:
            self.speak(dlg.pick_line(dlg.PETS_ON_LINES), skip_ai=True)
        else:
            self.speak(dlg.pick_line(dlg.PETS_OFF_LINES), skip_ai=True)
            self.dismiss_all_pets()
        if hasattr(self, "_persist_settings"):
            self._persist_settings()

    def spawn_pet(self, *, by_kinito: bool = False, sprite_id: str | None = None) -> bool:
        """Create a pet near Kinito; returns False when blocked."""
        if not getattr(self, "_running", True):
            return False
        if not getattr(self, "_pets_enabled", True):
            self.speak(dlg.PET_DISABLED_LINE, skip_ai=True)
            return False
        if len(getattr(self, "_pets", [])) >= self._pet_max_count():
            return False
        sprite = self._pick_pet_sprite(sprite_id)
        if sprite is None:
            self.speak(dlg.PET_NO_SPRITES_LINE, skip_ai=True)
            return False
        photos = _load_pet_photos(
            sprite,
            float(getattr(self, "_sprite_draw_scale", 1.0)) * self.PET_RENDER_SCALE,
        )
        if not photos:
            return False
        anchor = self._pet_anchor_point()
        pet = MiniPet(self, sprite, photos)
        pw, ph = pet._pet_draw_size()
        spawn_x, spawn_y = anchor[0], anchor[1]
        for _ in range(8):
            spawn_x = anchor[0] + random.uniform(-90, 90)
            spawn_y = anchor[1] + random.uniform(0, 50)
            spawn_x, spawn_y = self._pet_clamp_point(spawn_x, spawn_y)
            if not self._pet_box_overlaps(spawn_x, spawn_y, pw, ph):
                break
        pet.create_window(spawn_x, spawn_y)
        self._pets.append(pet)
        self._ensure_pet_tick()
        if random.random() < self.PET_SUMMON_LINE_CHANCE and not getattr(
            self, "_is_busy_with_speech", lambda: False
        )():
            self.speak(dlg.pick_line(dlg.PET_SUMMON_LINES), skip_ai=True)
        return True

    def dismiss_pet(self, pet: MiniPet, *, animate: bool = True) -> None:
        """Send a pet off-screen (or destroy instantly with *animate* False)."""
        pets = getattr(self, "_pets", [])
        if pet not in pets:
            return
        if not animate:
            pets.remove(pet)
            pet.destroy()
            return
        pet.target = self._pet_exit_point_for(pet)
        pet.state = PET_STATE_LEAVE
        pet.social = None
        self._ensure_pet_tick()

    def dismiss_all_pets(self, *, destroy: bool = False) -> None:
        """Remove every pet, animated or instantly on shutdown."""
        pets = list(getattr(self, "_pets", []))
        for pet in pets:
            if destroy:
                pet.destroy()
                if pet in self._pets:
                    self._pets.remove(pet)
            else:
                self.dismiss_pet(pet)

    def _pet_exit_point_for(self, pet: MiniPet) -> tuple[float, float]:
        """Exit just beyond the nearest edge of the pet's current monitor.

        The pet despawns shortly after crossing its own screen edge instead
        of trekking all the way to the outermost virtual-desktop boundary.
        """
        rect = self._pet_screen_rect(pet.x, pet.y)
        if rect is None:
            return (pet.x + 600.0, pet.y)
        mx, my, mw, mh = rect
        direction = min(
            (
                ("left", pet.x - mx),
                ("right", mx + mw - pet.x),
                ("top", pet.y - my),
                ("bottom", my + mh - pet.y),
            ),
            key=lambda item: item[1],
        )[0]
        if direction == "left":
            return (mx - 80.0, pet.y)
        if direction == "right":
            return (mx + mw + 80.0, pet.y)
        if direction == "top":
            return (pet.x, my - 80.0)
        return (pet.x, my + mh + 80.0)

    # -- idle-loop triggers ------------------------------------------------

    def maybe_trigger_pet(self) -> bool:
        """Roll for Kinito summoning a pet on his own."""
        if not getattr(self, "_running", True):
            return False
        if not getattr(self, "_startup_complete", True):
            return False
        if not getattr(self, "_pets_enabled", True):
            return False
        if getattr(self, "_focus_mode", False):
            return False
        if getattr(self, "_is_game_active", lambda: False)():
            return False
        if len(getattr(self, "_pets", [])) >= self._pet_max_count():
            return False
        if not self._enabled_pet_sprite_ids():
            return False
        last_at = getattr(self, "_last_pet_spawn_at", 0.0)
        if last_at > 0 and time.monotonic() - last_at < self.PET_SPAWN_COOLDOWN_SECONDS:
            return False
        chance = self.PET_SPAWN_CHANCE * getattr(
            self, "_activity_chance_mult", lambda _id: 1.0
        )("pets")
        if random.random() >= chance:
            return False
        self._last_pet_spawn_at = time.monotonic()
        self.root.after(0, self._start_random_pet_spawn)
        return True

    def _spawn_startup_pets(self) -> None:
        """Spawn up to the configured pet count right after startup."""
        if not getattr(self, "_running", True):
            return
        if not getattr(self, "_pets_enabled", True):
            return
        if not getattr(self, "_pets_spawn_at_startup", False):
            return
        enabled = self._enabled_pet_sprite_ids()
        stored = getattr(self, "_pet_startup_sprites", None) or []
        sprite_ids = [sprite_id for sprite_id in stored if sprite_id in enabled]
        if not sprite_ids:
            sprite_ids = [
                entry["id"]
                for entry in self._mini_sprite_catalog()
                if entry["id"] in enabled
            ]
        for sprite_id in sprite_ids[: self._pet_max_count()]:
            if not self.spawn_pet(sprite_id=sprite_id):
                break

    def _start_random_pet_spawn(self) -> None:
        if not getattr(self, "_running", True):
            return
        self.spawn_pet(by_kinito=True)

    def maybe_dismiss_pet(self) -> bool:
        """Roll for Kinito sending one of his pets home, with a farewell line."""
        if not getattr(self, "_running", True):
            return False
        pets = [p for p in getattr(self, "_pets", []) if p.state != PET_STATE_LEAVE]
        if not pets:
            return False
        if getattr(self, "_is_busy_with_speech", lambda: False)():
            return False
        last_at = getattr(self, "_last_pet_dismiss_at", 0.0)
        if last_at > 0 and time.monotonic() - last_at < self.PET_DISMISS_COOLDOWN_SECONDS:
            return False
        chance = self.PET_DISMISS_CHANCE * getattr(
            self, "_activity_chance_mult", lambda _id: 1.0
        )("pets")
        if random.random() >= chance:
            return False
        self._last_pet_dismiss_at = time.monotonic()
        self.root.after(0, self._kinito_dismiss_pet)
        return True

    def _kinito_dismiss_pet(self) -> None:
        if not getattr(self, "_running", True):
            return
        pets = [p for p in getattr(self, "_pets", []) if p.state != PET_STATE_LEAVE]
        if not pets:
            return
        self.speak(dlg.pick_line(dlg.PET_SEND_AWAY_LINES), skip_ai=True)
        self.dismiss_pet(random.choice(pets))

    # -- geometry helpers ---------------------------------------------------

    def _pet_anchor_point(self) -> tuple[float, float]:
        getter = getattr(self, "_buddy_center", None)
        if callable(getter):
            return getter()
        return float(getattr(self, "x", 0)), float(getattr(self, "y", 0))

    def _pet_anchor_for(self, pet: MiniPet) -> tuple[float, float]:
        cx, cy = self._pet_anchor_point()
        x = cx + math.cos(pet.orbit_angle) * self.PET_ORBIT_RADIUS_X
        y = cy + math.sin(pet.orbit_angle) * self.PET_ORBIT_RADIUS_Y + 30.0
        # Clamp into the work area — an anchor under the taskbar would trap the
        # pet in a walk-down/get-pushed-up loop.
        return self._pet_clamp_point(x, y)

    def _pet_sleep_spot_for(self, pet: MiniPet) -> tuple[float, float]:
        pets = [
            p for p in getattr(self, "_pets", [])
            if not p.destroyed and p.state != PET_STATE_LEAVE
        ]
        if pet not in pets:
            pets.append(pet)
        sizes = [
            (
                max(photo.width() for photo in p.photos.values()),
                max(photo.height() for photo in p.photos.values()),
            )
            for p in pets
        ]
        cx, cy = self._pet_anchor_point()
        get_size = getattr(self, "_window_screen_size", None)
        if callable(get_size):
            buddy_w, buddy_h = get_size()
        else:
            buddy_w = max(int(self.root.winfo_width()), 1)
            buddy_h = max(int(self.root.winfo_height()), 1)
        rect = self._pet_work_rect(cx, cy)
        gap = 10.0
        index = pets.index(pet)
        fallback = None
        for columns in range(len(pets), 0, -1):
            rows = [sizes[i:i + columns] for i in range(0, len(pets), columns)]
            widths = [sum(w for w, _ in row) + gap * (len(row) - 1) for row in rows]
            heights = [max(h for _, h in row) for row in rows]
            width = max(max(widths), buddy_w if columns == len(pets) else 0)
            height = sum(heights) + gap * (len(rows) - 1)
            offsets = []
            row_y = 0.0
            for row, row_width, row_height in zip(rows, widths, heights, strict=True):
                spacing = gap
                if len(row) > 1:
                    spacing += (width - row_width) / (len(row) - 1)
                row_x = (width - row[0][0]) / 2 if len(row) == 1 else 0.0
                for w, h in row:
                    offsets.append((row_x, row_y + row_height - h))
                    row_x += w + spacing
                row_y += row_height + gap
            candidates = [
                (cx - width / 2, cy + buddy_h / 2 + gap),
                (cx - width / 2, cy - buddy_h / 2 - gap - height),
                (cx + buddy_w / 2 + gap, cy - height / 2),
                (cx - buddy_w / 2 - gap - width, cy - height / 2),
            ]
            if fallback is None:
                fallback = (candidates[0], offsets)
            for side, (x, y) in enumerate(candidates):
                if rect is not None:
                    mx, my, mw, mh = rect
                    if width > mw or height > mh:
                        continue
                    if side < 2:
                        x = max(mx, min(mx + mw - width, x))
                    else:
                        y = max(my, min(my + mh - height, y))
                    if not (mx <= x <= mx + mw - width and my <= y <= my + mh - height):
                        continue
                dx, dy = offsets[index]
                return x + dx, y + dy
        (x, y), offsets = fallback
        dx, dy = offsets[index]
        return x + dx, y + dy

    def _pet_cursor_point(self) -> tuple[float, float] | None:
        getter = getattr(self, "_cursor_screen_pos", None)
        if callable(getter):
            return getter()
        try:
            return (
                float(self.root.winfo_pointerx()),
                float(self.root.winfo_pointery()),
            )
        except tk.TclError:
            return None

    def _pet_work_rect(
        self, x: float = 0.0, y: float = 0.0
    ) -> tuple[int, int, int, int] | None:
        """Usable screen area (taskbar excluded) containing (*x*, *y*)."""
        try:
            from kinito.window_targets import work_area_rect_for_point

            return work_area_rect_for_point(float(x), float(y))
        except Exception:
            return self._pet_screen_rect(x, y)

    def _pet_screen_rect(
        self, x: float = 0.0, y: float = 0.0
    ) -> tuple[int, int, int, int] | None:
        """Return the monitor rect containing (*x*, *y*) — not the whole desktop.

        With multiple monitors the virtual-desktop rect often makes top/bottom
        the nearest "edge", so pets would always despawn vertically.
        """
        try:
            from kinito.window_targets import monitor_rect_for_point

            return monitor_rect_for_point(float(x), float(y))
        except Exception:
            pass
        query = getattr(self, "_query_virtual_screen_rect", None)
        if callable(query):
            return query()
        try:
            self.root.update_idletasks()
            return (
                int(self.root.winfo_vrootx()),
                int(self.root.winfo_vrooty()),
                int(self.root.winfo_vrootwidth()),
                int(self.root.winfo_vrootheight()),
            )
        except tk.TclError:
            return None

    def _pet_virtual_rect(self) -> tuple[int, int, int, int] | None:
        """Return the whole virtual-desktop rect (all monitors combined)."""
        query = getattr(self, "_query_virtual_screen_rect", None)
        if callable(query):
            try:
                return query()
            except Exception:
                pass
        try:
            self.root.update_idletasks()
            return (
                int(self.root.winfo_vrootx()),
                int(self.root.winfo_vrooty()),
                int(self.root.winfo_vrootwidth()),
                int(self.root.winfo_vrootheight()),
            )
        except tk.TclError:
            return None

    def _pet_clamp_point(self, x: float, y: float) -> tuple[float, float]:
        rect = self._pet_work_rect(x, y)
        if rect is None:
            return x, y
        x0, y0, w, h = rect
        margin = 20
        return (
            max(x0 + margin, min(x0 + w - margin - 60, x)),
            max(y0 + margin, min(y0 + h - margin - 60, y)),
        )

    def _pet_settled(self, pet: MiniPet) -> bool:
        """Whether *pet* currently rests somewhere (not mid-transit)."""
        if pet.dragging or pet.sleeping:
            return False
        return pet.target is None or pet._target_reached(self.PET_ARRIVE_RADIUS)

    def _pet_box_overlaps(
        self, x: float, y: float, w: float, h: float, *, skip: MiniPet | None = None
    ) -> bool:
        for other in getattr(self, "_pets", []):
            if other is skip or other.destroyed:
                continue
            ow, oh = other._pet_draw_size()
            if not (
                x + w <= other.x or other.x + ow <= x
                or y + h <= other.y or other.y + oh <= y
            ):
                return True
        return False

    def _pet_separation_pass(self) -> None:
        """Push settled overlapping pets apart; movers may still pass over."""
        pets = [
            p for p in getattr(self, "_pets", [])
            if not p.destroyed
            and not p.dragging
            and p.social is None
            and p.state not in (PET_STATE_LEAVE, PET_STATE_HOPOUT)
        ]
        gap = 6.0
        for i in range(len(pets)):
            for j in range(i + 1, len(pets)):
                a, b = pets[i], pets[j]
                if not (self._pet_settled(a) and self._pet_settled(b)):
                    continue
                aw, ah = a._pet_draw_size()
                bw, bh = b._pet_draw_size()
                if (
                    a.x + aw <= b.x or b.x + bw <= a.x
                    or a.y + ah <= b.y or b.y + bh <= a.y
                ):
                    continue
                anchor_a = self._pet_anchor_for(a)
                anchor_b = self._pet_anchor_for(b)
                dist_a = math.hypot(anchor_a[0] - a.x, anchor_a[1] - a.y)
                dist_b = math.hypot(anchor_b[0] - b.x, anchor_b[1] - b.y)
                if (
                    dist_a < self.PET_ARRIVE_RADIUS
                    and dist_b < self.PET_ARRIVE_RADIUS
                ):
                    continue  # both home — overlapping anchors are tolerated
                # Move the pet farther from its own anchor — the one already
                # home must not be shoved or it walks back into the loop.
                mover, stay = (b, a) if dist_b >= dist_a else (a, b)
                mw, mh = mover._pet_draw_size()
                sw, sh = stay._pet_draw_size()
                right = stay.x + sw + gap
                left = stay.x - mw - gap
                # Prefer the nearer escape; but only take a side whose spot is
                # actually free — otherwise pets ping-pong between neighbors.
                if (stay.x + sw) - mover.x <= (mover.x + mw) - stay.x:
                    candidates = (right, left)
                else:
                    candidates = (left, right)
                for cand_x in candidates:
                    new_x, _ = self._pet_clamp_point(cand_x, mover.y)
                    if new_x == mover.x:
                        continue
                    if self._pet_box_overlaps(
                        new_x, mover.y, mw, mh, skip=mover
                    ):
                        continue
                    mover.x = new_x
                    # Rest at the new spot — otherwise the pet walks straight
                    # back onto the anchor it was shoved away from and the
                    # separation pass loops forever.
                    mover.state = PET_STATE_REST
                    mover.target = None
                    mover.rest_until = time.monotonic() + random.uniform(
                        *self.PET_REST_SECONDS
                    )
                    mover._place(mover.x, mover.y)
                    break

    def _pet_try_social(self, pet: MiniPet) -> bool:
        """Start a pet-to-pet interaction involving *pet*; False if nobody free."""
        others = [
            p for p in getattr(self, "_pets", [])
            if p is not pet
            and not p.destroyed
            and p.social is None
            and p.state in (PET_STATE_FOLLOW, PET_STATE_WANDER, PET_STATE_REST)
        ]
        if not others:
            return False
        partner = random.choice(others)
        now = time.monotonic()
        kinds = ["chase", "circle", "visit", "push", "together", "orbit", "leapfrog", "pounce"]
        if len(others) >= 2:
            kinds.append("piggy")
        kind = random.choice(kinds)
        if kind == "chase":
            until = now + random.uniform(5.0, 30.0)
            chasers = [pet, *(o for o in others if o is not partner)]
            partner.social = {
                "kind": "flee",
                "partner": pet,
                "chasers": chasers,
                "until": until,
            }
            # Everyone else free joins the hunt — all three can play tag.
            for i, chaser in enumerate(chasers):
                # Each chaser approaches a different side — they surround the
                # fleer instead of stacking on the exact same point.
                chaser.social = {
                    "kind": "chase",
                    "partner": partner,
                    "angle": math.tau * i / len(chasers),
                    # Brief head start so the fleer gets away before the
                    # chase begins — otherwise the faster chasers catch it
                    # instantly and just trail behind it forever.
                    "start_at": now + 1.2,
                    "until": until,
                }
        elif kind == "circle":
            pet.social = {
                "kind": "circle",
                "partner": partner,
                "until": now + random.uniform(4.0, 10.0),
                "angle": math.atan2(pet.y - partner.y, pet.x - partner.x),
            }
        elif kind == "visit":
            pet.social = {
                "kind": "visit",
                "partner": partner,
                "until": now + 12.0,
            }
        elif kind == "push":
            pet.social = {
                "kind": "push",
                "partner": partner,
                "until": now + 12.0,
            }
        elif kind == "leapfrog":
            until = now + random.uniform(15.0, 25.0)
            posts = [partner, *(o for o in others if o is not partner)][:2]
            direction = random.choice((-1.0, 1.0))
            slot_y = partner.y
            for i, post in enumerate(posts):
                px = self._pet_clamp_point(
                    partner.x + direction * 80.0 * i, slot_y
                )[0]
                post.social = {
                    "kind": "leapfrog_post",
                    "point": (px, slot_y),
                    "leaper": pet,
                    "until": until,
                }
            pet.social = {
                "kind": "leapfrog",
                "posts": posts,
                "dir": direction,
                "index": -1,
                "until": until,
            }
        elif kind == "pounce":
            pet.social = {"kind": "pounce", "until": now + 15.0}
        elif kind == "piggy":
            # The real game duration only starts once both throwers reached
            # their posts — traveling there gets its own generous budget so
            # far-away pets don't burn the whole timer walking into place.
            duration = random.uniform(8.0, 16.0)
            until = now + 30.0
            throwers = [pet, *(o for o in others if o is not partner)][:2]
            partner.social = {
                "kind": "piggy_mid",
                "throwers": throwers,
                "active": pet,
                "duration": duration,
                "until": until,
            }
            # Standoff spots left and right of the middle pet, so it can
            # actually be tossed back and forth instead of everyone stacking.
            for side, thrower in zip((-1.0, 1.0), throwers, strict=False):
                post = self._pet_clamp_point(
                    partner.x + side * 170.0, partner.y
                )
                thrower.social = {
                    "kind": "piggy_throw",
                    "piggy": partner,
                    "post": post,
                    "until": until,
                }
        elif kind == "orbit":
            point = self._pet_anchor_point()
            members = [pet, *others]
            until = now + random.uniform(6.0, 12.0)
            for i, member in enumerate(members):
                # Stagger the starting angles so they spread around the ring.
                member.social = {
                    "kind": "orbit",
                    "point": point,
                    "angle": math.tau * i / len(members),
                    "until": until,
                }
        else:
            dest = self._pet_random_screen_point(pet)
            # Every free pet joins — all three can head somewhere together.
            # Give each pet its own spaced slot around the destination so
            # they arrive side by side instead of stacking on one point.
            members = [pet, *others]
            spacing = 90.0
            for i, member in enumerate(members):
                offset = (i - (len(members) - 1) / 2) * spacing
                member.social = {
                    "kind": "together",
                    "point": self._pet_clamp_point(
                        dest[0] + offset + random.uniform(-15, 15),
                        dest[1] + random.uniform(-15, 15),
                    ),
                    "until": now + 40.0,
                }
        return True

    def _pet_random_screen_point(self, pet: MiniPet) -> tuple[float, float]:
        rect = self._pet_virtual_rect() or self._pet_screen_rect(pet.x, pet.y)
        if rect is None:
            return (pet.x + random.uniform(-300, 300), pet.y)
        x0, y0, w, h = rect
        margin = 40
        x = random.uniform(x0 + margin, x0 + w - margin - 60)
        y = random.uniform(y0 + margin, y0 + h - margin - 60)
        # Keep the destination off the taskbar even on the primary monitor.
        return self._pet_clamp_point(x, y)

    def _is_pet_music_playing(self) -> bool:
        check = getattr(self, "_is_background_music_playing", None)
        return bool(check and check())

    # -- shared tick ---------------------------------------------------------

    def _ensure_pet_tick(self) -> None:
        if getattr(self, "_pet_tick_timer", None) is not None:
            return
        if not getattr(self, "_pets", []):
            return
        schedule_after(
            self.root,
            self,
            "_pet_tick_timer",
            self.PET_TICK_MS,
            self._pets_tick,
        )

    def _pets_tick(self) -> None:
        self._pet_tick_timer = None
        pets = list(getattr(self, "_pets", []))
        now = time.monotonic()
        for pet in pets:
            pet.tick(now)
            if pet.destroyed and pet in self._pets:
                self._pets.remove(pet)
            elif pet.state not in (PET_STATE_LEAVE, PET_STATE_HOPOUT) and (
                self._pet_settled(pet)
            ):
                # Clamp only resting pets — clamping mid-walk traps them sliding
                # along a monitor edge instead of crossing to another screen.
                cx, cy = self._pet_clamp_point(pet.x, pet.y)
                if (cx, cy) != (pet.x, pet.y):
                    pet.x, pet.y = cx, cy
                    pet._place(cx, cy)
        self._pet_separation_pass()
        if self._pets:
            if all(p.state == PET_STATE_HOPOUT for p in self._pets):
                # During shutdown _running is False and schedule_after refuses;
                # the hop-out animation still needs the tick to keep firing.
                try:
                    self._pet_tick_timer = self.root.after(
                        self.PET_TICK_MS, self._pets_tick
                    )
                except tk.TclError:
                    self._pet_tick_timer = None
            else:
                schedule_after(
                    self.root,
                    self,
                    "_pet_tick_timer",
                    self.PET_TICK_MS,
                    self._pets_tick,
                )

    def _stop_pets(self) -> None:
        """Hop each pet briefly, then remove it as Kinito shuts down."""
        pets = [p for p in getattr(self, "_pets", []) if not p.destroyed]
        if not getattr(self, "_pet_lineup_saved", False):
            # Persisted once per shutdown — the second call (root destroy) would
            # otherwise overwrite the lineup with the post-hopout empty list.
            self._pet_lineup_saved = True
            self._pet_startup_sprites = [
                p.sprite_id
                for p in pets
                if p.state != PET_STATE_LEAVE
            ][: self._pet_max_count()]
            store = getattr(self, "_settings", None)
            if store is not None and hasattr(store, "set_pet_startup_sprites"):
                try:
                    store.set_pet_startup_sprites(self._pet_startup_sprites)
                except Exception:
                    pass
        if not pets:
            cancel_after(self.root, self, "_pet_tick_timer")
            return
        now = time.monotonic()
        for pet in pets:
            pet.state = PET_STATE_HOPOUT
            pet.target = None
            pet.sleeping = False
            pet._set_image("left" if pet.facing_left else "right")
            pet.hop_until = now + random.uniform(*self.PET_HOPOUT_SECONDS)
        cancel_after(self.root, self, "_pet_tick_timer")
        self._pets_tick()

    # -- settings window ------------------------------------------------------

    def open_pet_settings(self) -> None:
        """Show a small panel for pet count and sprite selection."""
        # Close the menu bubble first — speak() would otherwise only swap its
        # title while the settings buttons stay open (unlike e.g. Memories).
        if hasattr(self, "close_speech_bubble"):
            try:
                self.close_speech_bubble()
            except Exception:
                pass
        if hasattr(self, "speak"):
            try:
                self.speak(dlg.pick_line(dlg.PETS_SETTINGS_OPEN_LINES), skip_ai=True)
            except Exception:
                pass

        existing = getattr(self, "_pet_settings_window", None)
        if existing is not None:
            try:
                if existing.winfo_exists():
                    existing.lift()
                    existing.focus_force()
                    return
            except tk.TclError:
                pass

        catalog = self._mini_sprite_catalog()
        enabled_ids = self._enabled_pet_sprite_ids()

        width, height = self.PET_SETTINGS_WIDTH, self.PET_SETTINGS_HEIGHT
        window = Toplevel(self.root)
        self._pet_settings_window = window
        window.title("Pets")
        apply_window_icon(window)
        window.wm_attributes("-topmost", True)
        window.configure(bg=_UI_BG)
        window.minsize(300, 240)
        center = getattr(self, "_centered_origin_on_primary", None)
        if callable(center):
            x, y = center(width, height)
        else:
            x, y = 100, 100
        window.geometry(f"{width}x{height}+{int(x)}+{int(y)}")

        Label(
            window,
            text="How many little friends may visit, and which ones? Saves automatically.",
            wraplength=width - 40,
            justify="left",
            padx=12,
            pady=8,
            bg=_UI_BG,
        ).pack(fill="x")

        count_row = Frame(window, bg=_UI_BG)
        count_row.pack(fill="x", padx=12, pady=4)
        Label(count_row, text="Max pets:", bg=_UI_BG).pack(side="left")
        count_var = IntVar(value=self._pet_max_count())
        count_label = Label(count_row, text=str(count_var.get()), width=3, bg=_UI_BG)
        count_label.pack(side="right")

        def _on_count_change(_raw=None):
            count_label.configure(text=str(count_var.get()))

        def _on_count_release(_event=None):
            count_label.configure(text=str(count_var.get()))
            self._pets_max_count = count_var.get()
            self._persist_pet_settings()
            # Excess pets wander off politely.
            for pet in list(getattr(self, "_pets", []))[self._pet_max_count() :]:
                self.dismiss_pet(pet)

        slider = Scale(
            count_row,
            from_=1,
            to=self.PET_MAX_HARD,
            orient="horizontal",
            variable=count_var,
            showvalue=False,
            length=140,
            command=_on_count_change,
            bg=_UI_BG,
            highlightthickness=0,
            bd=0,
        )
        slider.bind("<ButtonRelease-1>", _on_count_release)
        slider.pack(side="right", fill="x", expand=True, padx=8)

        startup_var = IntVar(
            value=1 if getattr(self, "_pets_spawn_at_startup", False) else 0
        )

        def _on_startup_toggle():
            self._pets_spawn_at_startup = bool(startup_var.get())
            self._persist_pet_settings()

        tk.Checkbutton(
            window,
            text="Have them here right at startup",
            variable=startup_var,
            command=_on_startup_toggle,
            bg=_UI_BG,
            activebackground=_UI_BG,
            anchor="w",
        ).pack(fill="x", padx=12, pady=2)

        sprite_vars: dict[str, IntVar] = {}
        summon_buttons: dict[str, tk.Button] = {}
        if not catalog:
            Label(
                window,
                text="No pet sprites found in gameAssets/minis.",
                bg=_UI_BG,
                padx=12,
            ).pack(fill="x")
        preview_refs: list = []
        save_sprites = self._pet_sprites_toggled(
            sprite_vars, catalog, summon_buttons=summon_buttons
        )
        for entry in catalog:
            row = Frame(window, bg=_UI_BG)
            row.pack(fill="x", padx=12, pady=2)
            var = IntVar(value=1 if entry["id"] in enabled_ids else 0)
            sprite_vars[entry["id"]] = var
            try:
                preview_img = Image.open(entry["path"]).convert("RGBA")
                preview_img.thumbnail((36, 36), Image.LANCZOS)
                preview = ImageTk.PhotoImage(preview_img)
                preview_refs.append(preview)
            except OSError:
                preview = None
            check = tk.Checkbutton(
                row,
                text=entry["name"],
                variable=var,
                image=preview,
                compound="left",
                bg=_UI_BG,
                activebackground=_UI_BG,
                command=save_sprites,
            )
            check.image = preview
            check.pack(side="left")
            summon_button = tk.Button(
                row,
                text=f"Summon {entry['name']}",
                bg=_UI_BG,
                state="normal" if var.get() else "disabled",
                command=(
                    lambda sprite_id=entry["id"]: self.spawn_pet(
                        sprite_id=sprite_id
                    )
                ),
            )
            summon_button.pack(side="right")
            summon_buttons[entry["id"]] = summon_button
        window._pet_preview_refs = preview_refs

        buttons = Frame(window, bg=_UI_BG)
        buttons.pack(fill="x", side="bottom", padx=12, pady=8)
        tk.Button(
            buttons, text="Close", bg=_UI_BG, command=self._close_pet_settings
        ).pack(side="right")
        tk.Button(
            buttons,
            text="Send all home",
            bg=_UI_BG,
            command=lambda: self.dismiss_all_pets(),
        ).pack(side="right", padx=6)
        tk.Button(
            buttons,
            text="Summon pet",
            bg=_UI_BG,
            command=lambda: self.spawn_pet(),
        ).pack(side="right")

        window.protocol("WM_DELETE_WINDOW", self._close_pet_settings)

    def _pet_sprites_toggled(self, sprite_vars, catalog, *, summon_buttons=None):
        def _save():
            enabled = {
                sprite_id for sprite_id, var in sprite_vars.items() if var.get()
            }
            all_ids = {entry["id"] for entry in catalog}
            self._pet_enabled_sprites = None if enabled == all_ids else enabled
            self._persist_pet_settings()
            if summon_buttons:
                for sprite_id, button in summon_buttons.items():
                    try:
                        button.configure(
                            state="normal" if sprite_id in enabled else "disabled"
                        )
                    except tk.TclError:
                        pass

        return _save

    def _persist_pet_settings(self) -> None:
        store = getattr(self, "_settings", None)
        if store is not None:
            try:
                store.update(
                    pets_max_count=int(self._pet_max_count()),
                    pets_spawn_at_startup=bool(
                        getattr(self, "_pets_spawn_at_startup", False)
                    ),
                )
            except Exception:
                pass
            enabled = getattr(self, "_pet_enabled_sprites", None)
            try:
                if hasattr(store, "set_pet_enabled_sprites"):
                    store.set_pet_enabled_sprites(enabled)
            except Exception:
                pass

    def _close_pet_settings(self) -> None:
        window = getattr(self, "_pet_settings_window", None)
        self._pet_settings_window = None
        if window is None:
            return
        try:
            window.destroy()
        except tk.TclError:
            pass
