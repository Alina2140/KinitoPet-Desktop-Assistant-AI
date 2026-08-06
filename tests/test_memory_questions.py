"""Tests for memory-aware question filtering and dialog persistence."""

from unittest.mock import MagicMock

import pytest

from content import dialogue as dlg
from content.dialog_registry import find_dialog_spec, handle_dialog_response
from content.memory_keys import ASK_ONCE_MARKERS, MARKER_TO_FACT_KEY
from content.questions import QUESTIONS
from kinito.features.content import ContentMixin
from kinito.features.memory import MemoryMixin
from kinito.memory.questions import MemoryQuestion
from kinito.memory.store import MemoryStore


class ContentStub(ContentMixin):
    pass


@pytest.fixture
def memory_dir(tmp_path):
    return str(tmp_path / "user_media")


@pytest.fixture
def content(memory_dir):
    stub = ContentStub()
    stub._memory = MemoryStore(directory=memory_dir)
    return stub


def test_ask_once_markers_cover_personal_questions():
    assert dlg.NAME_QUESTION in ASK_ONCE_MARKERS
    assert dlg.DAY_QUESTION not in ASK_ONCE_MARKERS
    assert dlg.ENERGY_QUESTION not in ASK_ONCE_MARKERS
    assert dlg.JOB_QUESTION in ASK_ONCE_MARKERS
    assert dlg.FAVORITE_GAME_QUESTION in ASK_ONCE_MARKERS
    assert dlg.BEDTIME_QUESTION in ASK_ONCE_MARKERS
    assert dlg.SHOW_QUESTION in ASK_ONCE_MARKERS
    assert dlg.PRONOUNS_QUESTION in ASK_ONCE_MARKERS
    assert MARKER_TO_FACT_KEY[dlg.NAME_QUESTION] == "user_names"
    assert MARKER_TO_FACT_KEY[dlg.JOB_QUESTION] == "job"
    assert MARKER_TO_FACT_KEY[dlg.FAVORITE_GAME_QUESTION] == "favorite_game"
    assert MARKER_TO_FACT_KEY[dlg.BEDTIME_QUESTION] == "bedtime"
    assert MARKER_TO_FACT_KEY[dlg.SHOW_QUESTION] == "favorite_show"
    assert MARKER_TO_FACT_KEY[dlg.CITY_QUESTION] == "home_city"
    assert MARKER_TO_FACT_KEY[dlg.RAIN_QUESTION] == "likes_rain"


def test_available_questions_skip_answered_markers(content):
    content._memory.mark_answered(dlg.NAME_QUESTION)
    pool = content._available_spontaneous_questions()
    assert all(dlg.NAME_QUESTION not in q for q in pool)
    assert any(dlg.DAY_QUESTION in q for q in pool)


def test_mood_checkin_persists_and_cools_down(content):
    from content.memory_keys import (
        ALLOWED_FACT_KEYS,
        MOOD_TODAY_COOLDOWN_DAYS,
        MOOD_TODAY_TOPIC,
    )

    assert "mood_today" in ALLOWED_FACT_KEYS
    assert "energy_today" in ALLOWED_FACT_KEYS
    assert "plans_tonight" in ALLOWED_FACT_KEYS
    app = MagicMock()
    app._memory = content._memory
    app.speak = MagicMock()
    spec = find_dialog_spec(dlg.DAY_QUESTION)
    handle_dialog_response(app, spec, dlg.BUTTON_GOOD)
    assert content._memory.get_fact("mood_today") == "good"
    assert content._memory.is_topic_on_cooldown(
        MOOD_TODAY_TOPIC, days=MOOD_TODAY_COOLDOWN_DAYS
    )
    pool = content._available_spontaneous_questions()
    assert all(dlg.DAY_QUESTION not in q for q in pool)


def test_energy_and_plans_daily_checkins(content):
    app = MagicMock()
    app._memory = content._memory
    app.speak = MagicMock()

    energy_spec = find_dialog_spec(dlg.ENERGY_QUESTION)
    handle_dialog_response(app, energy_spec, dlg.BUTTON_TIRED)
    assert content._memory.get_fact("energy_today") == "low"

    plans_spec = find_dialog_spec(dlg.PLANS_TONIGHT_QUESTION)
    handle_dialog_response(app, plans_spec, "movie night")
    assert content._memory.get_fact("plans_tonight") == "movie night"

    pool = content._available_spontaneous_questions()
    assert all(dlg.ENERGY_QUESTION not in q for q in pool)
    assert all(dlg.PLANS_TONIGHT_QUESTION not in q for q in pool)


def test_expanded_fact_keys_persist(memory_dir):
    app = MagicMock()
    app._memory = MemoryStore(directory=memory_dir)
    app.speak = MagicMock()

    show_spec = find_dialog_spec(dlg.SHOW_QUESTION)
    handle_dialog_response(app, show_spec, "The Office")
    assert app._memory.get_fact("favorite_show") == "The Office"

    rain_spec = find_dialog_spec(dlg.RAIN_QUESTION)
    handle_dialog_response(app, rain_spec, dlg.BUTTON_YES)
    assert app._memory.get_fact("likes_rain") == "yes"

    pronouns_spec = find_dialog_spec(dlg.PRONOUNS_QUESTION)
    handle_dialog_response(app, pronouns_spec, "they/them")
    assert app._memory.get_fact("pronouns") == "they/them"


def test_job_dialog_persists_answer(memory_dir):
    app = MagicMock()
    app._memory = MemoryStore(directory=memory_dir)
    app.speak = MagicMock()

    spec = find_dialog_spec(dlg.JOB_QUESTION)
    handle_dialog_response(app, spec, "software engineer")

    assert app._memory.get_fact("job") == "software engineer"
    assert app._memory.is_answered(dlg.JOB_QUESTION)
    app.speak.assert_called_once()


def test_name_dialog_persists_answer(memory_dir):
    app = MagicMock()
    app._memory = MemoryStore(directory=memory_dir)
    app.speak = MagicMock()

    spec = find_dialog_spec(dlg.NAME_QUESTION)
    handle_dialog_response(app, spec, "Alex")

    assert app._memory.get_fact("user_names") == "Alex"
    assert app._memory.is_answered(dlg.NAME_QUESTION)
    app.speak.assert_called_once()


def test_programming_dialog_persists_yes_no(memory_dir):
    app = MagicMock()
    app._memory = MemoryStore(directory=memory_dir)
    app.speak = MagicMock()

    spec = find_dialog_spec(dlg.PROGRAMMING_QUESTION)
    handle_dialog_response(app, spec, dlg.BUTTON_YES)

    assert app._memory.get_fact("likes_programming") == "yes"
    assert app._memory.is_answered(dlg.PROGRAMMING_QUESTION)


def test_answered_name_question_not_in_full_pool(content):
    content._memory.set_fact("user_names", "Alex")
    content._memory.mark_answered(dlg.NAME_QUESTION)
    pool = content._available_spontaneous_questions()
    name_questions = [q for q in QUESTIONS if dlg.NAME_QUESTION in q]
    assert name_questions
    assert not any(q in pool for q in name_questions)


class MemoryStub(MemoryMixin):
    pass


def test_memory_question_does_not_overwrite_user_names(memory_dir):
    stub = MemoryStub()
    stub._memory = MemoryStore(directory=memory_dir)
    stub._chat_session_user_label = None
    stub._memory.set_fact("user_names", "Ben")
    stub._memory.mark_answered(dlg.NAME_QUESTION)
    stub.speak = MagicMock()

    spec = MemoryQuestion(
        question="What music genre do you like?",
        ui="textbox",
        topic="music_genre_relaxation",
        save_as="user_names",
    )
    stub._pending_memory_question = spec
    stub._handle_memory_question_response("Metal")

    assert stub._memory.get_fact("user_names") == "Ben"
    assert any("music_genre_relaxation" in note["text"] for note in stub._memory.snapshot()["notes"])


def test_chat_user_label_stays_pinned_until_cleared(memory_dir):
    stub = MemoryStub()
    stub._init_memory = MemoryMixin._init_memory.__get__(stub, MemoryStub)
    stub._memory = MemoryStore(directory=memory_dir)
    stub._chat_session_user_label = None
    stub._memory.replace_fact_values("user_names", ["Alex", "Brian", "Sam"])

    pinned = stub._pin_chat_user_label()
    assert pinned in {"Alex", "Brian", "Sam"}
    assert stub.chat_user_label() == pinned
    assert stub.chat_user_label() == pinned

    stub._clear_chat_session_user_label()
    assert stub._chat_session_user_label is None
