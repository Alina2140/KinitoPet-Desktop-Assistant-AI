"""Tests for the file-backed memory store."""

import json
import os
from datetime import date

import pytest

from kinito.memory.store import (
    MAX_NOTES_IN_PROMPT,
    MAX_NOTES_STORED,
    MAX_PROMPT_BLOCK_CHARS,
    MemoryStore,
)


@pytest.fixture
def memory_dir(tmp_path):
    return str(tmp_path / "user_media")


@pytest.fixture
def store(memory_dir):
    return MemoryStore(directory=memory_dir)


def test_empty_store_has_no_prompt_block(store):
    assert store.as_prompt_block() == ""
    assert store.user_display_name() == "You"


def test_set_fact_and_load_roundtrip(store, memory_dir):
    store.set_fact("user_names", "Alex")
    store.mark_answered("What should I call you?")

    reloaded = MemoryStore(directory=memory_dir)
    assert reloaded.get_fact("user_names") == "Alex"
    assert reloaded.is_answered("What should I call you?")


def test_is_question_answered_matches_marker_in_text(store):
    store.mark_answered(dlg_marker := "What's your favorite color?")
    assert store.is_question_answered(f"Hey! {dlg_marker} I love colors.")
    assert not store.is_question_answered("How is your day?")


def test_add_note_deduplicates(store):
    assert store.add_note("Likes jazz") is True
    assert store.add_note("Likes jazz") is False
    assert len(store.snapshot()["notes"]) == 1


def test_add_note_rejects_near_duplicates(store):
    assert store.add_note("Movie nights with Sarah on weekends") is True
    assert store.add_note("Sarah movie nights on weekends") is False
    assert len(store.snapshot()["notes"]) == 1


def test_notes_fifo_when_over_limit(store):
    for index in range(MAX_NOTES_STORED + 3):
        store.add_note(f"Plans with friend number {index}")
    notes = store.snapshot()["notes"]
    assert len(notes) == MAX_NOTES_STORED
    assert notes[0]["text"] == "Plans with friend number 3"
    assert notes[-1]["text"] == f"Plans with friend number {MAX_NOTES_STORED + 2}"


def test_as_prompt_block_includes_facts_and_recent_notes(store):
    store.set_fact("user_names", "Alex")
    store.add_note("Often works late on the PC")
    block = store.as_prompt_block()
    assert "user names: Alex" in block
    assert "works late" in block


def test_as_prompt_block_limits_note_count(store):
    for index in range(MAX_NOTES_IN_PROMPT + 5):
        store.add_note(f"Movie nights with friend {index}")
    block = store.as_prompt_block()
    assert "friend 4" not in block
    assert f"friend {MAX_NOTES_IN_PROMPT + 4}" in block


def test_as_prompt_block_truncates_long_output(store):
    store.set_fact("user_names", "A" * 200)
    block = store.as_prompt_block()
    assert len(block) <= MAX_PROMPT_BLOCK_CHARS


def test_apply_extraction_updates_facts_and_notes(store):
    store.apply_extraction(
        add_notes=["Enjoys hiking on weekends"],
        update_facts={"hobbies": "hiking"},
        allowed_fact_keys=frozenset({"hobbies"}),
    )
    snapshot = store.snapshot()
    assert snapshot["facts"]["hobbies"] == "hiking"
    assert snapshot["notes"][0]["text"] == "Enjoys hiking on weekends"


def test_reset_removes_files(store, memory_dir):
    store.set_fact("user_names", "Alex")
    store.add_note("Test note")
    path = os.path.join(memory_dir, "memory.json")
    notes_path = os.path.join(memory_dir, "notes.txt")
    assert os.path.isfile(path)
    assert os.path.isfile(notes_path)

    store.reset()
    assert not os.path.isfile(path)
    assert not os.path.isfile(notes_path)
    assert store.snapshot()["facts"] == {}


def test_load_recovers_from_corrupt_json(memory_dir):
    os.makedirs(memory_dir, exist_ok=True)
    path = os.path.join(memory_dir, "memory.json")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("{not valid json")

    store = MemoryStore(directory=memory_dir)
    assert store.snapshot()["facts"] == {}


def test_save_writes_valid_json(memory_dir, store):
    store.set_fact("user_names", "Sam")
    path = os.path.join(memory_dir, "memory.json")
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    assert data["facts"]["user_names"] == "Sam"


def test_as_facts_prompt_block_omits_notes(store):
    store.set_fact("user_names", "Alex")
    store.add_note("Enjoys hiking on weekends")
    facts_block = store.as_facts_prompt_block()
    assert "user names: Alex" in facts_block
    assert "hiking" not in facts_block
    full_block = store.as_prompt_block()
    assert "hiking" in full_block


def test_mark_topic_asked_and_fifo(memory_dir, store):
    store.mark_topic_asked("topic_a")
    assert store.is_topic_asked("topic_a")
    reloaded = MemoryStore(directory=memory_dir)
    assert reloaded.is_topic_asked("topic_a")
    assert reloaded.is_topic_on_cooldown("topic_a", days=7)


def test_mark_topic_asked_updates_date_when_already_listed(store):
    store.mark_topic_asked("verify_hobby", today=date(2026, 1, 1))
    store.mark_topic_asked("verify_hobby", today=date(2026, 7, 28))
    assert store._data["topic_asked_at"]["verify_hobby"] == "2026-07-28"


def test_multi_value_hobby_set_fact_splits_and_roundtrips(store, memory_dir):
    store.set_fact("hobbies", "Drawing, Reading, Crochet")
    assert store.get_fact_values("hobbies") == ["Drawing", "Reading", "Crochet"]
    assert store.get_fact("hobbies") == "Drawing, Reading, and Crochet"
    assert store.snapshot()["facts"]["hobbies"] == ["Drawing", "Reading", "Crochet"]

    reloaded = MemoryStore(directory=memory_dir)
    assert reloaded.get_fact_values("hobbies") == ["Drawing", "Reading", "Crochet"]
    assert reloaded.facts_dict()["hobbies"] == "Drawing, Reading, and Crochet"


def test_multi_value_legacy_string_hobby_still_loads(memory_dir):
    os.makedirs(memory_dir, exist_ok=True)
    path = os.path.join(memory_dir, "memory.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "version": 1,
                "facts": {"hobby": "Drawing"},
                "answered_markers": [],
                "asked_topics": [],
                "notes": [],
            },
            handle,
        )

    store = MemoryStore(directory=memory_dir)
    assert "hobby" not in store.snapshot()["facts"]
    assert store.get_fact("hobbies") == "Drawing"
    assert store.get_fact_values("hobbies") == ["Drawing"]


def test_user_names_list_picks_random_display_name(store):
    store.replace_fact_values("user_names", ["Alex", "Sad", "Sam"])
    assert store.get_fact_values("user_names") == ["Alex", "Sad", "Sam"]
    assert store.user_display_name() in {"Alex", "Sad", "Sam"}
    assert store.pick_user_name() in {"Alex", "Sad", "Sam"}


def test_loads_plural_multi_value_lists_from_disk(memory_dir):
    os.makedirs(memory_dir, exist_ok=True)
    path = os.path.join(memory_dir, "memory.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "version": 1,
                "facts": {
                    "user_names": ["Alex", "Sad"],
                    "hobbies": ["Drawing", "Crochet"],
                    "favorite_colors": ["Black", "Purple"],
                    "pets": ["Lola", "Mae"],
                },
                "answered_markers": [],
                "asked_topics": [],
                "notes": [],
            },
            handle,
        )

    store = MemoryStore(directory=memory_dir)
    assert store.get_fact_values("user_names") == ["Alex", "Sad"]
    assert store.get_fact_values("hobbies") == ["Drawing", "Crochet"]
    assert store.get_fact_values("favorite_colors") == ["Black", "Purple"]
    assert store.get_fact_values("pets") == ["Lola", "Mae"]


def test_apply_extraction_merges_hobby_string_and_replaces_list(store):
    store.set_fact("hobbies", "Drawing")
    store.apply_extraction(
        update_facts={"hobbies": "Reading"},
        allowed_fact_keys=frozenset({"hobbies"}),
    )
    assert store.get_fact_values("hobbies") == ["Drawing", "Reading"]

    store.apply_extraction(
        update_facts={"hobbies": ["Crochet"]},
        allowed_fact_keys=frozenset({"hobbies"}),
    )
    assert store.get_fact_values("hobbies") == ["Crochet"]


def test_pet_and_split_on_set_fact(store):
    store.set_fact("pets", "Lola and Mae")
    assert store.get_fact_values("pets") == ["Lola", "Mae"]
    assert store.get_fact("pets") == "Lola and Mae"


def test_remove_fact_value_keeps_remaining_items(store):
    store.set_fact("hobbies", "Drawing, Reading, Crochet")
    assert store.remove_fact_value("hobbies", "Drawing") is True
    assert store.get_fact_values("hobbies") == ["Reading", "Crochet"]
    assert store.remove_fact_value("hobbies", "missing") is False


def test_set_fact_rejects_placeholder_for_favorite_drink(store):
    store.set_fact("favorite_drink", "Tea")
    store.set_fact("favorite_drink", "no")
    assert store.get_fact("favorite_drink") == "Tea"


def test_apply_extraction_rejects_placeholder_favorite_drink(store):
    store.set_fact("favorite_drink", "Tea")
    store.apply_extraction(
        update_facts={"favorite_drink": "no"},
        allowed_fact_keys=frozenset({"favorite_drink"}),
    )
    assert store.get_fact("favorite_drink") == "Tea"
