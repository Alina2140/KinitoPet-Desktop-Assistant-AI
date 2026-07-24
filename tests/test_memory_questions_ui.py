"""Tests for interactive memory question UI and persistence."""

from unittest.mock import MagicMock

import pytest

from content import dialogue as dlg
from kinito.features.memory import MemoryMixin
from kinito.memory.questions import MemoryQuestion
from kinito.memory.store import MemoryStore
from kinito.speech import SpeechMixin


class MemorySpeechStub(MemoryMixin, SpeechMixin):
    pass


@pytest.fixture
def memory_dir(tmp_path):
    return str(tmp_path / "user_media")


@pytest.fixture
def app(memory_dir):
    stub = MemorySpeechStub()
    stub.root = MagicMock()
    stub.root.after = lambda _delay, fn, *args: fn(*args)
    stub._init_memory()
    stub._memory = MemoryStore(directory=memory_dir)
    stub._pending_memory_question = None
    stub.speak = MagicMock()
    stub.interrupt_speech = MagicMock()
    stub.close_speech_bubble = MagicMock()
    stub.show_response_textbox = MagicMock()
    stub.show_response_buttons = MagicMock()
    return stub


def test_ask_memory_question_sets_pending_and_speaks(app):
    spec = MemoryQuestion("Do you like tea?", "textbox", "likes_tea")
    app.ask_memory_question(spec)
    assert app._pending_memory_question == spec
    app.speak.assert_called_once_with("Do you like tea?", 45, True, skip_ai=True)


def test_handle_memory_question_response_saves_note(app):
    spec = MemoryQuestion("Do you cook?", "yes_no", "cooks_food")
    app._pending_memory_question = spec
    app._handle_memory_question_response(dlg.BUTTON_YES)
    assert app._pending_memory_question is None
    notes = app._memory.snapshot()["notes"]
    assert len(notes) == 1
    assert "cooks_food: yes" in notes[0]["text"]
    assert app._memory.is_topic_asked("cooks_food")
    app.speak.assert_called_once()


def test_handle_memory_question_response_saves_fact(app):
    spec = MemoryQuestion("Favorite snack?", "textbox", "snack_followup", save_as="favorite_snack")
    app._pending_memory_question = spec
    app._handle_memory_question_response("chips")
    assert app._memory.get_fact("favorite_snack") == "chips"


def test_verify_yes_keeps_fact(app):
    from kinito.memory.questions import save_as_verify

    app._memory.set_fact("favorite_color", "black")
    spec = MemoryQuestion(
        "Is your favorite color still black?",
        "yes_no",
        "verify_favorite_color",
        save_as=save_as_verify("favorite_color"),
    )
    app._pending_memory_question = spec
    app._handle_memory_question_response(dlg.BUTTON_YES)
    assert app._memory.get_fact("favorite_color") == "black"
    assert app._memory.is_topic_asked("verify_favorite_color")
    assert app._pending_memory_question is None


def test_verify_no_asks_for_updated_value(app):
    from kinito.memory.questions import save_as_verify

    app._memory.set_fact("favorite_color", "black")
    spec = MemoryQuestion(
        "Is your favorite color still black?",
        "yes_no",
        "verify_favorite_color",
        save_as=save_as_verify("favorite_color"),
    )
    app._pending_memory_question = spec
    app._handle_memory_question_response(dlg.BUTTON_NO)

    assert app._memory.get_fact("favorite_color") == "black"
    assert app._pending_memory_question is not None
    assert app._pending_memory_question.save_as == "favorite_color"
    assert "favorite color" in app._pending_memory_question.question.lower()

    app._handle_memory_question_response("blue")
    assert app._memory.get_fact("favorite_color") == "blue"
    assert app._pending_memory_question is None


def test_verify_no_updates_likes_fact_in_place(app):
    from kinito.memory.questions import save_as_verify

    app._memory.set_fact("likes_programming", "yes")
    spec = MemoryQuestion(
        "Do you still like programming?",
        "yes_no",
        "verify_likes_programming",
        save_as=save_as_verify("likes_programming"),
    )
    app._pending_memory_question = spec
    app._handle_memory_question_response(dlg.BUTTON_NO)

    assert app._memory.get_fact("likes_programming") == "no"
    assert "likes_programming" in app._memory.facts_dict()
    assert app._pending_memory_question is None


def test_show_speech_bubble_attaches_memory_question_ui(app):
    spec = MemoryQuestion("Weekend plans?", "textbox", "weekend_plans")
    app._pending_memory_question = spec
    app.play_sfx = MagicMock()
    app._new_speech_bubble_toplevel = MagicMock(return_value=MagicMock())
    app._create_bubble_shell = MagicMock(return_value=MagicMock())
    app.create_wrapped_label = MagicMock(return_value=MagicMock())
    app._fit_speech_bubble_to_content = MagicMock()
    app._schedule_speech_bubble_position = MagicMock()
    app._schedule_response_timeout = MagicMock()
    app._has_active_speech_bubble = MagicMock(return_value=False)
    app._cancel_bubble_close_timer = MagicMock()
    app.BUBBLE_BG = "white"
    app.BUBBLE_PAD_X = 1
    app.BUBBLE_PAD_Y = 1

    app.show_speech_bubble("Weekend plans?", evergoaway=False, force=True)

    app.show_response_textbox.assert_called_once_with("Weekend plans?")
    assert app._awaiting_response is True


def test_handle_response_routes_pending_memory_question(app):
    spec = MemoryQuestion("Still into jazz?", "yes_no", "jazz_followup")
    app._pending_memory_question = spec
    app._close_speech_bubble_impl = MagicMock()
    app.handle_response(dlg.BUTTON_NO)
    assert app._memory.is_topic_asked("jazz_followup")
    app.interrupt_speech.assert_called_once()
    app._close_speech_bubble_impl.assert_called_once_with(stop_tts=False, clear_pending=False)
    app.speak.assert_called_once()
