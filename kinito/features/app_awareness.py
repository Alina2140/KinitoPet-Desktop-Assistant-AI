"""Optional awareness of open/active desktop apps (process names only)."""

from __future__ import annotations

from kinito.app_context import AppContextCache, AppSnapshot


class AppAwarenessMixin:
    """Settings-gated access to a live RAM-only open/active app snapshot."""

    def _init_app_awareness(self, enabled: bool = True) -> None:
        """Initialize toggle state and snapshot cache (call from app __init__)."""
        self._app_awareness_enabled = bool(enabled)
        self._app_context_cache = AppContextCache()

    def toggle_app_awareness(self):
        """Enable or disable open/active app awareness."""
        from content import dialogue as dlg

        self._app_awareness_enabled = not getattr(self, "_app_awareness_enabled", True)
        if not self._app_awareness_enabled:
            cache = getattr(self, "_app_context_cache", None)
            if cache is not None:
                cache.clear()
        if hasattr(self, "_persist_settings"):
            self._persist_settings()
        lines = (
            dlg.APP_AWARENESS_ON_LINES
            if self._app_awareness_enabled
            else dlg.APP_AWARENESS_OFF_LINES
        )
        self.speak(dlg.pick_line(lines), skip_ai=True)

    def get_app_snapshot(self, *, force: bool = False) -> AppSnapshot | None:
        """Return a live snapshot when awareness is on; otherwise None."""
        if not getattr(self, "_app_awareness_enabled", True):
            return None
        cache = getattr(self, "_app_context_cache", None)
        if cache is None:
            cache = AppContextCache()
            self._app_context_cache = cache
        snapshot = cache.get(force=force)
        if not snapshot.has_apps:
            return None
        return snapshot
