"""Ambient hand overlay that grabs and moves other desktop windows."""

from __future__ import annotations

import random
import sys
import time
import tkinter as tk
from tkinter import Label, Toplevel

from content.window_grab_lines import pick_window_grab_line
from kinito.window_targets import (
    SIDE_LEFT,
    WindowRect,
    choose_drag_end,
    choose_grab_side,
    clamp_window_origin,
    collect_own_hwnds,
    get_window_rect,
    hand_sprite_for_side,
    hand_tuck_geometry,
    list_movable_windows,
    minimize_window,
    place_window_behind,
    position_diverged,
    probe_window_movable,
    restore_window,
    set_window_pos,
    virtual_screen_rect_windows,
)


class WindowGrabMixin:
    """Occasionally reach out with a hand sprite and rearrange a window."""

    WINDOW_GRAB_CHANCE = 1 / 250
    WINDOW_GRAB_COOLDOWN_SECONDS = 300
    WINDOW_GRAB_MINIMIZE_CHANCE = 0.2
    WINDOW_GRAB_DRAG_DISTANCE = (80, 1400)
    WINDOW_GRAB_MAX_TARGET_DISTANCE = 1400
    WINDOW_GRAB_FLY_FRAMES = 22
    WINDOW_GRAB_FLY_FRAME_MS = 100
    WINDOW_GRAB_DRAG_STEPS = 20
    WINDOW_GRAB_DRAG_FRAME_MS = 100
    WINDOW_GRAB_SPEAK_CHANCE = 0.45
    WINDOW_GRAB_MIN_DRAG_PX = 80

    def toggle_window_grab(self):
        """Enable or disable ambient window grabbing."""
        from content import dialogue as dlg

        self._window_grab_enabled = not getattr(self, "_window_grab_enabled", True)
        if hasattr(self, "_persist_settings"):
            self._persist_settings()
        lines = (
            dlg.WINDOW_PLAY_ON_LINES
            if self._window_grab_enabled
            else dlg.WINDOW_PLAY_OFF_LINES
        )
        self.speak(dlg.pick_line(lines), skip_ai=True)

    def maybe_trigger_window_grab(self) -> bool:
        """Roll for an ambient window grab; schedule on the Tk main thread if it hits."""
        if sys.platform != "win32":
            return False
        if not getattr(self, "_window_grab_enabled", True):
            return False
        if getattr(self, "_focus_mode", False):
            return False
        if getattr(self, "_is_game_active", lambda: False)():
            return False
        if getattr(self, "_window_grab_active", False):
            return False
        if (
            self.paused
            or getattr(self, "_is_position_locked_by_user", lambda: self.is_dragging)()
            or getattr(self, "_camera_active", False)
            or getattr(self, "_browser_active", False)
        ):
            return False
        if getattr(self, "_is_busy_with_speech", lambda: False)():
            return False
        last_at = getattr(self, "_last_window_grab_at", 0.0)
        if time.monotonic() - last_at < self.WINDOW_GRAB_COOLDOWN_SECONDS:
            return False
        grab_chance = self.WINDOW_GRAB_CHANCE
        if hasattr(self, "mood_window_grab_mult"):
            grab_chance *= max(0.05, float(self.mood_window_grab_mult()))
        if random.random() >= grab_chance:
            return False
        self._last_window_grab_at = time.monotonic()
        # Reserve immediately so roam/surf cannot start in parallel.
        self._window_grab_active = True
        self.root.after(0, self._run_window_grab)
        return True

    def _window_grab_virtual_rect(self) -> tuple[int, int, int, int]:
        """Return the virtual desktop rect used for clamping moved windows."""
        rect = virtual_screen_rect_windows()
        if rect is not None:
            return rect
        query = getattr(self, "_query_virtual_screen_rect", None)
        if callable(query):
            return query()
        self.root.update_idletasks()
        return (
            int(self.root.winfo_vrootx()),
            int(self.root.winfo_vrooty()),
            int(self.root.winfo_vrootwidth()),
            int(self.root.winfo_vrootheight()),
        )

    def _window_grab_exclude_hwnds(self) -> set[int]:
        """HWNDs owned by Kinito that must never be grabbed."""
        windows = [
            getattr(self, "root", None),
            getattr(self, "_hand_window", None),
            getattr(self, "_camera_window", None),
            getattr(self, "_game_window", None),
            getattr(self, "_glitch_window", None),
            getattr(self, "_crash_window", None),
        ]
        bubble = getattr(self, "speech_bubble", None)
        if bubble is not None:
            windows.append(bubble)
        return collect_own_hwnds(*windows)

    def _pick_window_grab_target(self) -> tuple[WindowRect, str] | None:
        """Choose a visible, actually movable window and which edge to grab."""
        windows = list_movable_windows(exclude_hwnds=self._window_grab_exclude_hwnds())
        if not windows:
            return None
        self.root.update_idletasks()
        kx = self.root.winfo_rootx() + self.root.winfo_width() / 2

        # Prefer nearer windows, but shuffle so we can skip immovable ones.
        def edge_distance(win: WindowRect) -> float:
            side = choose_grab_side(kx, win.left, win.right)
            edge_x = win.left if side == SIDE_LEFT else win.right
            return abs(kx - edge_x)

        ordered = sorted(windows, key=edge_distance)
        near = [
            w
            for w in ordered
            if edge_distance(w) <= self.WINDOW_GRAB_MAX_TARGET_DISTANCE
        ]
        pool = near or ordered
        random.shuffle(pool)

        for candidate in pool[:8]:
            if not probe_window_movable(candidate.hwnd):
                continue
            # Rect may have changed after restore/probe — refresh.
            fresh = get_window_rect(candidate.hwnd) or candidate
            side = choose_grab_side(kx, fresh.left, fresh.right)
            return fresh, side
        return None

    def _hand_photo_for_side(self, side: str):
        """Return the PhotoImage for the grab side."""
        stem = hand_sprite_for_side(side)
        if stem == "HandToRight":
            return getattr(self, "tk_img_hand_right", None)
        return getattr(self, "tk_img_hand_left", None)

    def _kinito_hand_start_pos(self, side: str, hand_w: int, hand_h: int) -> tuple[int, int]:
        """Spawn the hand near Kinito, biased toward the target side."""
        self.root.update_idletasks()
        kx = self.root.winfo_rootx()
        ky = self.root.winfo_rooty()
        kw = self.root.winfo_width()
        kh = self.root.winfo_height()
        if side == SIDE_LEFT:
            x = kx + max(0, kw // 4) - hand_w // 2
        else:
            x = kx + (3 * kw) // 4 - hand_w // 2
        y = ky + kh // 2 - hand_h // 2
        return int(x), int(y)

    def _create_hand_overlay(self, side: str, x: int, y: int):
        """Create the borderless hand Toplevel at (*x*, *y*)."""
        photo = self._hand_photo_for_side(side)
        if photo is None:
            return None
        hand = Toplevel(self.root)
        hand.overrideredirect(True)
        hand.configure(bg="white")
        try:
            hand.attributes("-transparentcolor", "white")
        except tk.TclError:
            pass
        # Visible during flight; tucked behind the target after grab.
        try:
            hand.wm_attributes("-topmost", True)
        except tk.TclError:
            pass
        label = Label(hand, image=photo, bg="white", bd=0, highlightthickness=0)
        label.pack()
        hand.update_idletasks()
        hw = max(hand.winfo_reqwidth(), 1)
        hh = max(hand.winfo_reqheight(), 1)
        hand.geometry(f"{hw}x{hh}+{x}+{y}")
        self._hand_window = hand
        self._hand_photo_ref = photo
        return hand

    def _hand_size(self) -> tuple[int, int]:
        hand = getattr(self, "_hand_window", None)
        if hand is None:
            return 40, 30
        try:
            hand.update_idletasks()
            return max(hand.winfo_width(), 1), max(hand.winfo_height(), 1)
        except tk.TclError:
            return 40, 30

    def _place_hand(self, x: int, y: int) -> None:
        hand = getattr(self, "_hand_window", None)
        if hand is None:
            return
        try:
            hw, hh = self._hand_size()
            hand.geometry(f"{hw}x{hh}+{int(x)}+{int(y)}")
        except tk.TclError:
            pass

    def _destroy_hand_overlay(self) -> None:
        hand = getattr(self, "_hand_window", None)
        self._hand_window = None
        self._hand_photo_ref = None
        if hand is None:
            return
        try:
            hand.destroy()
        except tk.TclError:
            pass

    def _finish_window_grab(self) -> None:
        """Tear down grab state and the hand overlay."""
        timer = getattr(self, "_window_grab_timer", None)
        if timer is not None:
            try:
                self.root.after_cancel(timer)
            except (tk.TclError, ValueError):
                pass
            self._window_grab_timer = None
        self._destroy_hand_overlay()
        self._window_grab_active = False
        self._window_grab_state = None

    def _schedule_window_grab_step(self, delay_ms: int, callback) -> None:
        self._window_grab_timer = self.root.after(delay_ms, callback)

    def _run_window_grab(self) -> None:
        """Start one grab sequence on the Tk main thread."""
        if not self._running or not getattr(self, "_window_grab_enabled", True):
            self._window_grab_active = False
            return
        if sys.platform != "win32":
            self._window_grab_active = False
            return

        picked = self._pick_window_grab_target()
        if picked is None:
            self._window_grab_active = False
            return
        target, side = picked
        photo = self._hand_photo_for_side(side)
        if photo is None:
            self._window_grab_active = False
            return

        # Estimate hand size from the PhotoImage before creating the overlay.
        try:
            hand_w = int(photo.width())
            hand_h = int(photo.height())
        except (tk.TclError, AttributeError, TypeError, ValueError):
            hand_w, hand_h = 48, 36

        start_x, start_y = self._kinito_hand_start_pos(side, hand_w, hand_h)
        hand = self._create_hand_overlay(side, start_x, start_y)
        if hand is None:
            self._window_grab_active = False
            return

        hand_w, hand_h = self._hand_size()
        tuck_x, tuck_y = hand_tuck_geometry(side, target, hand_w, hand_h)

        self._window_grab_active = True
        do_minimize = random.random() < self.WINDOW_GRAB_MINIMIZE_CHANCE
        self._window_grab_state = {
            "hwnd": target.hwnd,
            "side": side,
            "frame": 0,
            "start": (start_x, start_y),
            "tuck": (tuck_x, tuck_y),
            "minimize": do_minimize,
            "last_set": target.origin,
            "drag_index": 0,
            "drag_path": [],
            "was_maximized": bool(target.maximized),
        }

        if random.random() < self.WINDOW_GRAB_SPEAK_CHANCE and hasattr(self, "speak"):
            try:
                self.speak(pick_window_grab_line(), skip_ai=True)
            except Exception:
                pass

        self._schedule_window_grab_step(self.WINDOW_GRAB_FLY_FRAME_MS, self._window_grab_fly_tick)

    def _window_grab_fly_tick(self) -> None:
        state = getattr(self, "_window_grab_state", None)
        if not state or not getattr(self, "_window_grab_active", False):
            return
        if getattr(self, "_is_position_locked_by_user", lambda: False)():
            self._finish_window_grab()
            return

        frame = int(state["frame"]) + 1
        state["frame"] = frame
        total = max(1, self.WINDOW_GRAB_FLY_FRAMES)
        t = min(1.0, frame / total)
        # Ease-out so the hand settles into the tuck.
        ease = 1.0 - (1.0 - t) ** 2
        sx, sy = state["start"]
        tx, ty = state["tuck"]
        x = int(sx + (tx - sx) * ease)
        y = int(sy + (ty - sy) * ease)
        self._place_hand(x, y)

        if frame < total:
            self._schedule_window_grab_step(
                self.WINDOW_GRAB_FLY_FRAME_MS, self._window_grab_fly_tick
            )
            return

        # After flight: tuck behind the target and act.
        rect = get_window_rect(state["hwnd"])
        if rect is None:
            self._finish_window_grab()
            return
        hand_w, hand_h = self._hand_size()
        tuck = hand_tuck_geometry(state["side"], rect, hand_w, hand_h)
        state["tuck"] = tuck
        self._place_hand(*tuck)
        hand = getattr(self, "_hand_window", None)
        if hand is not None:
            try:
                hand.wm_attributes("-topmost", False)
            except tk.TclError:
                pass
            hwnds = collect_own_hwnds(hand)
            if hwnds:
                place_window_behind(next(iter(hwnds)), state["hwnd"])

        if state["minimize"]:
            minimize_window(state["hwnd"])
            self._schedule_window_grab_step(280, self._finish_window_grab)
            return

        # Maximized / zoomed: restore first so the window can actually slide.
        if state.get("was_maximized") or rect.maximized:
            restored = restore_window(state["hwnd"])
            if restored is None:
                self._finish_window_grab()
                return
            rect = restored
            hand_w, hand_h = self._hand_size()
            tuck = hand_tuck_geometry(state["side"], rect, hand_w, hand_h)
            state["tuck"] = tuck
            state["last_set"] = rect.origin
            self._place_hand(*tuck)

        if not self._prepare_window_grab_drag_path(state, rect):
            # No room to slide — fall back to minimize.
            minimize_window(state["hwnd"])
            self._schedule_window_grab_step(280, self._finish_window_grab)
            return

        self._schedule_window_grab_step(
            self.WINDOW_GRAB_DRAG_FRAME_MS, self._window_grab_drag_tick
        )

    def _prepare_window_grab_drag_path(self, state: dict, rect: WindowRect) -> bool:
        """Build a clamped 2D drag path. Return False if no visible move is possible."""
        virtual = self._window_grab_virtual_rect()
        end = choose_drag_end(
            rect.left,
            rect.top,
            rect.width,
            rect.height,
            virtual,
            distance_range=self.WINDOW_GRAB_DRAG_DISTANCE,
            min_move_px=self.WINDOW_GRAB_MIN_DRAG_PX,
        )
        if end is None:
            return False
        end_x, end_y = end
        steps = max(2, self.WINDOW_GRAB_DRAG_STEPS)
        path: list[tuple[int, int]] = []
        for i in range(1, steps + 1):
            t = i / steps
            x = int(rect.left + (end_x - rect.left) * t)
            y = int(rect.top + (end_y - rect.top) * t)
            x, y = clamp_window_origin(x, y, rect.width, rect.height, virtual)
            path.append((x, y))
        state["drag_path"] = path
        state["drag_index"] = 0
        state["last_set"] = rect.origin
        state["win_w"] = rect.width
        state["win_h"] = rect.height
        return True

    def _window_grab_drag_tick(self) -> None:
        state = getattr(self, "_window_grab_state", None)
        if not state or not getattr(self, "_window_grab_active", False):
            return
        if getattr(self, "_is_position_locked_by_user", lambda: False)():
            self._finish_window_grab()
            return

        hwnd = state["hwnd"]
        current = get_window_rect(hwnd)
        if current is None:
            self._finish_window_grab()
            return

        previous = current.origin
        # User took over before this step: left our last known spot.
        if position_diverged(state["last_set"], previous):
            self._finish_window_grab()
            return

        path = state["drag_path"]
        index = int(state["drag_index"])
        if index >= len(path):
            self._finish_window_grab()
            return

        next_x, next_y = path[index]
        if not set_window_pos(hwnd, next_x, next_y):
            # Immovable after all — minimize so the grab still does something visible.
            minimize_window(hwnd)
            self._finish_window_grab()
            return

        moved = get_window_rect(hwnd)
        if moved is None:
            self._finish_window_grab()
            return
        actual = moved.origin

        # User takeover: window left *previous* but did not arrive near our target.
        if position_diverged(previous, actual) and position_diverged(
            (next_x, next_y), actual
        ):
            self._finish_window_grab()
            return

        # Silent refusal: still at previous — minimize instead of empty grab.
        if not position_diverged(previous, actual) and position_diverged(
            (next_x, next_y), actual
        ):
            minimize_window(hwnd)
            self._finish_window_grab()
            return

        state["last_set"] = actual
        state["drag_index"] = index + 1

        hand_w, hand_h = self._hand_size()
        tuck = hand_tuck_geometry(state["side"], moved, hand_w, hand_h)
        self._place_hand(*tuck)
        hand = getattr(self, "_hand_window", None)
        hwnds = collect_own_hwnds(hand) if hand is not None else set()
        if hwnds:
            place_window_behind(next(iter(hwnds)), hwnd)

        self._schedule_window_grab_step(
            self.WINDOW_GRAB_DRAG_FRAME_MS, self._window_grab_drag_tick
        )
