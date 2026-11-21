"""Cursor style picker: swap the system arrow for Kinito-themed cursors."""

from __future__ import annotations

from kinito.cursors import (
    CURSOR_STYLE_SYSTEM,
    apply_cursor_style,
    restore_system_cursors,
)


class CursorSettingsMixin:
    """Open a cursor picker and apply/persist the chosen cursor style."""

    def offer_cursor_picker(self) -> None:
        """Ask which cursor to use (Settings -> Cursor)."""
        from content import dialogue as dlg

        self.speak(
            dlg.CURSOR_MENU_QUESTION.format(style=self.current_cursor_style()),
            45,
            True,
            skip_ai=True,
        )

    def current_cursor_style(self) -> str:
        return getattr(self, "_cursor_style", CURSOR_STYLE_SYSTEM)

    def set_cursor_style(self, style: str) -> None:
        """Apply and persist *style* ('system', 'pointer', 'hand', 'squid')."""
        from content import dialogue as dlg

        if style == CURSOR_STYLE_SYSTEM:
            apply_cursor_style(style)
            self._cursor_style = CURSOR_STYLE_SYSTEM
        elif apply_cursor_style(style):
            self._cursor_style = style
        else:
            self.speak(dlg.pick_line(dlg.CURSOR_UNAVAILABLE_LINES), skip_ai=True)
            return
        store = getattr(self, "_settings", None)
        if store is not None and hasattr(store, "set_cursor_style"):
            store.set_cursor_style(self._cursor_style)
        self.speak(
            dlg.pick_line(dlg.CURSOR_SET_LINES).format(style=self._cursor_style),
            skip_ai=True,
        )

    def _apply_saved_cursor_style(self) -> None:
        """Re-apply the persisted cursor style at startup."""
        style = self.current_cursor_style()
        if style != CURSOR_STYLE_SYSTEM:
            apply_cursor_style(style)

    def _restore_cursor_on_exit(self) -> None:
        """Give back the normal system cursor when Kinito shuts down."""
        restore_system_cursors()
