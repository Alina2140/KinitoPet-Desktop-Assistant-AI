"""Occasional silent screen glances with spoken commentary."""

from __future__ import annotations

import io
import random
import threading
import time

from content import dialogue as dlg
from content import llm_prompts
from content.screen_comment_lines import pick_screen_comment_fallback
from kinito.llm.ollama_client import OllamaUnavailableError


class ScreenCommentsMixin:
    """Grab the screen ephemerally and speak a short comment (bubble + TTS)."""

    SCREEN_COMMENT_CHANCE = 1
    SCREEN_COMMENT_COOLDOWN_SECONDS = 5
    SCREEN_COMMENT_MAX_EDGE = 896
    SCREEN_COMMENT_JPEG_QUALITY = 70

    def maybe_trigger_screen_comment(self) -> bool:
        """Roll for a silent screen glance; schedule work if it hits."""
        if not getattr(self, "_screen_comments_enabled", True):
            return False
        if getattr(self, "_focus_mode", False):
            return False
        if getattr(self, "_is_game_active", lambda: False)():
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
        last_at = getattr(self, "_last_screen_comment_at", 0.0)
        if time.monotonic() - last_at < self.SCREEN_COMMENT_COOLDOWN_SECONDS:
            return False
        if random.random() >= self.SCREEN_COMMENT_CHANCE:
            return False
        self._last_screen_comment_at = time.monotonic()
        self.root.after(0, self._start_screen_comment)
        return True

    def toggle_screen_comments(self):
        """Enable or disable spontaneous screen commentary."""
        self._screen_comments_enabled = not getattr(self, "_screen_comments_enabled", True)
        if hasattr(self, "_persist_settings"):
            self._persist_settings()
        lines = (
            dlg.SCREEN_COMMENTS_ON_LINES
            if self._screen_comments_enabled
            else dlg.SCREEN_COMMENTS_OFF_LINES
        )
        self.speak(dlg.pick_line(lines), skip_ai=True)

    def _start_screen_comment(self):
        """Kick off grab + vision work off the UI thread."""
        if not getattr(self, "_running", True):
            return
        if not getattr(self, "_screen_comments_enabled", True):
            return
        threading.Thread(target=self._screen_comment_worker, daemon=True).start()

    def _screen_comment_worker(self):
        """Capture, optionally ask vision, drop pixels, then speak."""
        line = pick_screen_comment_fallback()
        image_bytes = None
        try:
            image_bytes = self._capture_screen_jpeg_bytes()
            if image_bytes:
                vision_line = self._vision_screen_comment(image_bytes)
                if vision_line:
                    line = vision_line
        except Exception:
            pass
        finally:
            image_bytes = None

        if not getattr(self, "_running", True):
            return
        if not getattr(self, "_screen_comments_enabled", True):
            return
        self.root.after(0, lambda spoken=line: self._speak_screen_comment(spoken))

    def _speak_screen_comment(self, line: str):
        """Deliver the comment with the normal speech bubble."""
        if getattr(self, "_is_busy_with_speech", lambda: False)():
            return
        self.speak(line, skip_ai=True)

    def _capture_screen_jpeg_bytes(self) -> bytes | None:
        """Grab the screen into JPEG bytes in RAM only — never write to disk."""
        try:
            from PIL import ImageGrab
        except ImportError:
            return None
        image = None
        buffer = None
        try:
            image = ImageGrab.grab()
            if image is None:
                return None
            image = image.convert("RGB")
            max_edge = self.SCREEN_COMMENT_MAX_EDGE
            width, height = image.size
            scale = min(1.0, max_edge / max(width, height))
            if scale < 1.0:
                image = image.resize(
                    (max(1, int(width * scale)), max(1, int(height * scale))),
                )
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=self.SCREEN_COMMENT_JPEG_QUALITY)
            return buffer.getvalue()
        except Exception:
            return None
        finally:
            if buffer is not None:
                buffer.close()
            image = None

    def _vision_screen_comment(self, image_bytes: bytes) -> str | None:
        """Ask local Ollama vision for a short comment; never store the image."""
        client = getattr(self, "_ollama_client", None)
        if client is None or not client.is_available():
            return None
        try:
            reply = client.chat_with_image(
                llm_prompts.SCREEN_COMMENT_VISION_PROMPT,
                image_bytes,
                system=llm_prompts.SCREEN_COMMENT_VISION_SYSTEM,
                max_tokens=80,
            )
        except OllamaUnavailableError:
            return None
        cleaned = (reply or "").strip()
        if not cleaned:
            return None
        # Keep spoken lines short.
        if len(cleaned) > 280:
            cleaned = cleaned[:277].rstrip() + "…"
        return cleaned
