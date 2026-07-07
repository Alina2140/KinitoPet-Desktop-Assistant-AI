"""Tests for time-aware Ollama prompt helpers."""

from datetime import datetime

from content import dialogue as dlg
from content import llm_prompts as prompts
from kinito.features.llm import LLMMixin


class LLMStub(LLMMixin):
    pass


def test_scripted_line_needs_time_context_for_sleep_question():
    assert prompts.scripted_line_needs_time_context(dlg.SLEEP_QUESTION) is True


def test_scripted_line_needs_time_context_for_idle_prompt():
    assert prompts.scripted_line_needs_time_context("", prompts.IDLE_PROMPT) is True


def test_scripted_line_needs_time_context_skips_unrelated_joke():
    assert prompts.scripted_line_needs_time_context("Why did the chicken cross the road?") is False


def test_local_time_context_describes_midday():
    context = prompts.local_time_context(datetime(2026, 7, 7, 12, 30))
    assert "12:30" in context
    assert "midday" in context
    assert "Mittag" in context


def test_local_time_context_describes_night():
    context = prompts.local_time_context(datetime(2026, 7, 7, 23, 15))
    assert "23:15" in context
    assert "night" in context
    assert "Nacht" in context


def test_append_time_context_only_when_needed():
    without = prompts.append_time_context_if_needed("Tell a joke.", "Why did the frog hop?")
    with_time = prompts.append_time_context_if_needed(
        "Ask about sleep.",
        dlg.SLEEP_QUESTION,
    )
    assert "Current local time" not in without
    assert "Current local time" in with_time


def test_build_generation_prompt_includes_time_for_day_question():
    app = LLMStub()
    prompt = app._build_generation_prompt(dlg.DAY_QUESTIONS[0], None)
    assert "Current local time" in prompt
    assert dlg.DAY_QUESTIONS[0] in prompt


def test_build_generation_prompt_skips_time_for_poem_hint():
    app = LLMStub()
    prompt = app._build_generation_prompt("Roses are red.", prompts.POEM_PROMPT)
    assert "Current local time" not in prompt
