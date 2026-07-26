"""Tests for live app context in LLM prompts."""

from unittest.mock import MagicMock

from content import llm_prompts as prompts
from kinito.app_context import AppSnapshot
from kinito.features.llm import LLMMixin


class LLMStub(LLMMixin):
    def __init__(self):
        self._memory = MagicMock()
        self._memory.as_prompt_block.return_value = ""
        self._app_snapshot = None

    def get_app_snapshot(self):
        return self._app_snapshot

    def memory_prompt_block(self) -> str:
        return self._memory.as_prompt_block()


def test_app_context_block_empty_for_missing_snapshot():
    assert prompts.app_context_block(None) == ""
    assert prompts.app_context_block(AppSnapshot(None, ())) == ""


def test_app_context_block_lists_active_and_open():
    snap = AppSnapshot(active="Chrome", open_apps=("Chrome", "Discord"))
    block = prompts.app_context_block(snap)
    assert "Active app right now: Chrome." in block
    assert "Open apps (names only): Chrome, Discord." in block
    assert "window titles" in block.lower() or "Do not invent" in block


def test_append_app_context_only_when_present():
    bare = prompts.append_app_context("Hello.", None)
    assert bare == "Hello."
    with_apps = prompts.append_app_context(
        "Hello.",
        AppSnapshot("Chrome", ("Chrome",)),
    )
    assert "Active app right now: Chrome." in with_apps


def test_build_generation_prompt_includes_app_context():
    app = LLMStub()
    app._app_snapshot = AppSnapshot("Cursor", ("Cursor", "Chrome"))
    prompt = app._build_generation_prompt("Hey there!", None)
    assert "Active app right now: Cursor." in prompt


def test_build_generation_prompt_skips_app_context_when_disabled():
    app = LLMStub()
    app._app_snapshot = None
    prompt = app._build_generation_prompt("Hey there!", None)
    assert "Active app right now" not in prompt


def test_system_prompt_includes_transient_app_context():
    app = LLMStub()
    app._app_snapshot = AppSnapshot("Discord", ("Discord",))
    system = app._system_prompt()
    assert "Active app right now: Discord." in system
    assert "Open apps (names only): Discord." in system


def test_memory_extract_prompt_forbids_storing_apps():
    assert "which apps or windows are open or active" in prompts.MEMORY_EXTRACT_PROMPT
