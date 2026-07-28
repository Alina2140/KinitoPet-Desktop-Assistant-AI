"""Tests for open/active app awareness helpers."""

from unittest.mock import MagicMock, patch

import pytest

from content import dialogue as dlg
from content.app_lines import (
    format_app_aware_line,
    maybe_pick_app_aware_nudge_line,
    pick_app_aware_idle_line,
)
from kinito.app_context import (
    AppContextCache,
    AppSnapshot,
    build_snapshot_from_process_map,
    friendly_app_name,
    is_noise_process,
)
from kinito.features.app_awareness import AppAwarenessMixin


def test_friendly_app_name_known_and_fallback():
    assert friendly_app_name(r"C:\Program Files\Google\Chrome\chrome.exe") == "Chrome"
    assert friendly_app_name("Code.exe") == "VS Code"
    assert friendly_app_name("weirdtool.exe") == "Weirdtool"


def test_is_noise_process_filters_shell_hosts():
    assert is_noise_process("explorer.exe") is True
    assert is_noise_process(r"C:\Windows\explorer.exe") is True
    assert is_noise_process("chrome.exe") is False
    assert is_noise_process("WindowsTerminal.exe") is True
    assert is_noise_process("powershell.exe") is True
    assert is_noise_process("cmd.exe") is True


def test_friendly_app_name_uses_description_when_available():
    with patch(
        "kinito.app_context.file_description_name",
        return_value="My Cool App, Version 1",
    ):
        assert friendly_app_name(r"C:\Apps\coolapp.exe") == "My Cool App"


def test_build_snapshot_from_process_map_dedupes_and_filters():
    snapshot = build_snapshot_from_process_map(
        {
            10: r"C:\Apps\chrome.exe",
            11: r"C:\Apps\chrome.exe",
            12: r"C:\Windows\explorer.exe",
            13: r"C:\Apps\Discord\Discord.exe",
            99: r"C:\Python\python.exe",
        },
        foreground_pid=13,
        own_pid=99,
    )
    assert snapshot.active == "Discord"
    assert snapshot.open_apps == ("Chrome", "Discord")
    assert "Explorer" not in snapshot.open_apps


def test_format_app_aware_line_placeholders():
    snapshot = AppSnapshot(active="Chrome", open_apps=("Chrome", "Discord"))
    text = format_app_aware_line(
        "Active={active_app}; Open={open_apps}",
        snapshot,
    )
    assert text == "Active=Chrome; Open=Chrome, Discord"


def test_maybe_pick_app_aware_nudge_line_respects_chance():
    snapshot = AppSnapshot(active="Chrome", open_apps=("Chrome",))
    with patch("content.app_lines.random.random", return_value=0.99):
        assert maybe_pick_app_aware_nudge_line(snapshot, chance=0.35) is None
    with patch("content.app_lines.random.random", return_value=0.0):
        line = maybe_pick_app_aware_nudge_line(snapshot, chance=0.35)
    assert line is not None
    assert "Chrome" in line


def test_pick_app_aware_idle_line_includes_active():
    snapshot = AppSnapshot(active="Cursor", open_apps=("Cursor", "Chrome"))
    line = pick_app_aware_idle_line(snapshot)
    assert "Cursor" in line or "Chrome" in line


class AwarenessStub(AppAwarenessMixin):
    pass


@pytest.fixture
def awareness():
    stub = AwarenessStub()
    stub._init_app_awareness()
    stub.speak = MagicMock()
    return stub


def test_toggle_app_awareness_disables_and_clears_cache(awareness):
    awareness._app_context_cache._snapshot = AppSnapshot("Chrome", ("Chrome",))
    awareness._app_context_cache._fetched_at = 1.0
    awareness.toggle_app_awareness()
    assert awareness._app_awareness_enabled is False
    assert awareness._app_context_cache._snapshot is None
    assert awareness.speak.call_args[0][0] in dlg.APP_AWARENESS_OFF_LINES
    assert awareness.get_app_snapshot() is None


def test_toggle_app_awareness_enables(awareness):
    awareness._app_awareness_enabled = False
    awareness.toggle_app_awareness()
    assert awareness._app_awareness_enabled is True
    assert awareness.speak.call_args[0][0] in dlg.APP_AWARENESS_ON_LINES


def test_get_app_snapshot_returns_none_when_empty(awareness):
    with patch(
        "kinito.features.app_awareness.AppContextCache.get",
        return_value=AppSnapshot(None, ()),
    ):
        assert awareness.get_app_snapshot() is None


def test_get_app_snapshot_returns_live_snapshot(awareness):
    snap = AppSnapshot("Chrome", ("Chrome", "Discord"))
    with patch.object(AppContextCache, "get", return_value=snap):
        assert awareness.get_app_snapshot() == snap
