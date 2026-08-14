"""Tests for memory editor actions and forget confirmation."""

from unittest.mock import MagicMock, patch

import pytest

from content import dialogue as dlg
from content.dialog_registry import find_dialog_spec, handle_dialog_response
from kinito.features.memory import MemoryMixin
from kinito.memory.store import MemoryStore


class MemoryEditorStub(MemoryMixin):
    pass


@pytest.fixture
def memory_app(tmp_path):
    stub = MemoryEditorStub()
    stub.root = MagicMock()
    stub.speak = MagicMock()
    stub._memory = MemoryStore(directory=str(tmp_path / "user_media"))
    stub._pending_memory_question = None
    stub._chat_session_user_label = None
    stub._memory_editor_window = None
    stub._memory_editor_widgets = {}
    return stub


def test_settings_memories_opens_editor(mock_app):
    spec = find_dialog_spec(dlg.SETTINGS_MENU_QUESTION)
    handle_dialog_response(mock_app, spec, dlg.BUTTON_REMEMBER)
    mock_app.open_memory_editor.assert_called_once()


def test_forget_memory_cancel_keeps_facts(memory_app):
    memory_app._memory.set_fact("favorite_drink", "Cherry Coke")
    memory_app._memory.add_note("Likes jazz nights")
    with patch("kinito.features.memory.messagebox.askyesno", return_value=False):
        memory_app.forget_memory()
    assert memory_app._memory.get_fact("favorite_drink") == "Cherry Coke"
    assert len(memory_app._memory.notes_list()) == 1
    memory_app.speak.assert_not_called()


def test_forget_memory_confirm_clears_and_speaks(memory_app):
    memory_app._memory.set_fact("favorite_drink", "Cherry Coke")
    memory_app._memory.add_note("Likes jazz nights")
    with patch("kinito.features.memory.messagebox.askyesno", return_value=True):
        memory_app.forget_memory()
    assert memory_app._memory.get_fact("favorite_drink") is None
    assert memory_app._memory.notes_list() == []
    assert memory_app._memory.get_fact("first_met") is not None
    memory_app.speak.assert_called_once_with(dlg.MEMORY_FORGOTTEN_LINE, skip_ai=True)


def test_show_memory_summary_aliases_editor(memory_app):
    memory_app.open_memory_editor = MagicMock()
    memory_app.show_memory_summary()
    memory_app.open_memory_editor.assert_called_once()


def test_save_memory_editor_applies_row_edits(memory_app):
    memory_app._memory.set_fact("favorite_drink", "Cherry Coke")
    memory_app._memory.set_fact("job", "Student")
    memory_app._memory.add_note("Old note text here")

    drink_entry = MagicMock()
    drink_entry.get.return_value = "Water"
    job_entry = MagicMock()
    job_entry.get.return_value = "Student"
    note_entry = MagicMock()
    note_entry.get.return_value = "Updated note text here"

    memory_app._memory_editor_widgets = {
        "fact_rows": [
            {"key": "favorite_drink", "entry": drink_entry},
            {"key": "job", "entry": job_entry},
        ],
        "note_rows": [{"entry": note_entry}],
        "rows_host": None,
    }
    memory_app._reload_memory_editor_rows = MagicMock()

    memory_app._save_memory_editor()

    assert memory_app._memory.get_fact("favorite_drink") == "Water"
    assert memory_app._memory.get_fact("job") == "Student"
    assert [note["text"] for note in memory_app._memory.notes_list()] == [
        "Updated note text here"
    ]
    memory_app.speak.assert_called_once_with(dlg.MEMORY_SAVED_LINE, skip_ai=True)


def test_save_memory_editor_deletes_removed_fact_rows(memory_app):
    memory_app._memory.set_fact("favorite_drink", "Cherry Coke")
    memory_app._memory.set_fact("job", "Student")
    drink_entry = MagicMock()
    drink_entry.get.return_value = "Cherry Coke"
    memory_app._memory_editor_widgets = {
        "fact_rows": [{"key": "favorite_drink", "entry": drink_entry}],
        "note_rows": [],
        "rows_host": None,
    }
    memory_app._reload_memory_editor_rows = MagicMock()

    memory_app._save_memory_editor()

    assert memory_app._memory.get_fact("favorite_drink") == "Cherry Coke"
    assert memory_app._memory.get_fact("job") is None
