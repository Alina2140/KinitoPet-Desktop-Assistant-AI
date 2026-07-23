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
    assert MARKER_TO_FACT_KEY[dlg.NAME_QUESTION] == "user_name"


def test_available_questions_skip_answered_markers(content):
    content._memory.mark_answered(dlg.NAME_QUESTION)
    pool = content._available_spontaneous_questions()
    assert all(dlg.NAME_QUESTION not in q for q in pool)
    assert any(dlg.DAY_QUESTION in q for q in pool)


def test_name_dialog_persists_answer(memory_dir):
    app = MagicMock()
    app._memory = MemoryStore(directory=memory_dir)
    app.speak = MagicMock()

    spec = find_dialog_spec(dlg.NAME_QUESTION)
    handle_dialog_response(app, spec, "Alex")

    assert app._memory.get_fact("user_name") == "Alex"
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
    content._memory.set_fact("user_name", "Alex")
    content._memory.mark_answered(dlg.NAME_QUESTION)
    pool = content._available_spontaneous_questions()
    name_questions = [q for q in QUESTIONS if dlg.NAME_QUESTION in q]
    assert name_questions
    assert not any(q in pool for q in name_questions)


class MemoryStub(MemoryMixin):
    pass


def test_memory_question_does_not_overwrite_user_name(memory_dir):
    stub = MemoryStub()
    stub._memory = MemoryStore(directory=memory_dir)
    stub._memory.set_fact("user_name", "Ben")
    stub._memory.mark_answered(dlg.NAME_QUESTION)
    stub.speak = MagicMock()

    spec = MemoryQuestion(
        question="What music genre do you like?",
        ui="textbox",
        topic="music_genre_relaxation",
        save_as="user_name",
    )
    stub._pending_memory_question = spec
    stub._handle_memory_question_response("Metal")

    assert stub._memory.get_fact("user_name") == "Ben"
    assert any("music_genre_relaxation" in note["text"] for note in stub._memory.snapshot()["notes"])
