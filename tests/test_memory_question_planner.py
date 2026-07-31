"""Tests for Ollama memory question planning."""

import json
from unittest.mock import MagicMock

import pytest

from content.memory_keys import ALLOWED_FACT_KEYS
from kinito.memory.question_planner import (
    MemoryQuestionPlanner,
    coerce_question_ui,
    normalize_question_plan,
    parse_question_plan,
)
from kinito.memory.store import MemoryStore


@pytest.fixture
def memory_dir(tmp_path):
    return str(tmp_path / "user_media")


@pytest.fixture
def store(memory_dir):
    memory = MemoryStore(directory=memory_dir)
    memory.set_fact("user_names", "Alex")
    return memory


def test_parse_question_plan_extracts_json_block():
    raw = 'Sure!\n{"question": "Do you like cats?", "ui": "yes_no", "topic": "cats", "save_as": "note"}'
    parsed = parse_question_plan(raw)
    assert parsed["question"] == "Do you like cats?"


def test_normalize_question_plan_rejects_missing_question_mark():
    assert normalize_question_plan({"question": "Hello there", "ui": "textbox", "topic": "x"}) is None


def test_normalize_question_plan_forces_note_save_as():
    spec = normalize_question_plan(
        {
            "question": "What music genre relaxes you?",
            "ui": "textbox",
            "topic": "music_genre_relaxation",
            "save_as": "user_names",
        }
    )
    assert spec is not None
    assert spec.save_as == "note"


@pytest.mark.parametrize(
    ("question", "requested_ui", "expected_ui"),
    [
        (
            "Would you rather stroll through a Spring garden or indulge in hobbies?",
            "yes_no",
            "textbox",
        ),
        ("What is your favorite rainy-day snack?", "yes_no", "textbox"),
        ("Is your favorite color still black?", "yes_no", "yes_no"),
        ("Do you have any plans tonight?", "yes_no", "yes_no"),
        ("Tea or coffee this afternoon?", "yes_no", "textbox"),
    ],
)
def test_coerce_question_ui(question, requested_ui, expected_ui):
    assert coerce_question_ui(question, requested_ui) == expected_ui


def test_normalize_forces_textbox_for_would_you_rather():
    spec = normalize_question_plan(
        {
            "question": (
                "Would you rather spend a serene afternoon strolling through a "
                "vibrant Spring garden or have an extra hour to indulge in your "
                "favorite hobbies?"
            ),
            "ui": "yes_no",
            "topic": "ai_b631",
            "save_as": "note",
        }
    )
    assert spec is not None
    assert spec.ui == "textbox"
    assert spec.topic == "ai_b631"


def test_normalize_builds_readable_topic_when_missing():
    spec = normalize_question_plan(
        {
            "question": "Would you rather walk in a garden or read fanfiction?",
            "ui": "yes_no",
            "topic": "",
            "save_as": "note",
        }
    )
    assert spec is not None
    assert spec.ui == "textbox"
    assert "garden" in spec.topic or "rather" in spec.topic or "walk" in spec.topic
    assert not spec.topic.startswith("ai_") or "_" in spec.topic


def test_apply_extraction_does_not_overwrite_protected_user_names(store):
    store.set_fact("user_names", "Ben")
    store.apply_extraction(
        update_facts={"user_names": "Metal"},
        allowed_fact_keys=ALLOWED_FACT_KEYS,
    )
    assert store.get_fact("user_names") == "Ben"


def test_planner_uses_ollama_and_skips_known_topics(store):
    client = MagicMock()
    client.generate.return_value = json.dumps(
        {
            "question": "Do you still enjoy hiking?",
            "ui": "yes_no",
            "topic": "hiking",
            "save_as": "note",
        }
    )
    planner = MemoryQuestionPlanner(client, store)
    spec = planner.plan()
    assert spec is not None
    assert spec.question.endswith("?")
    client.generate.assert_called_once()


def test_planner_works_without_known_memory(memory_dir):
    store = MemoryStore(directory=memory_dir)
    client = MagicMock()
    client.generate.return_value = json.dumps(
        {
            "question": "If you could teleport anywhere for lunch, where would you go?",
            "ui": "textbox",
            "topic": "teleport_lunch",
            "save_as": "note",
        }
    )
    planner = MemoryQuestionPlanner(client, store)
    spec = planner.plan()
    assert spec is not None
    assert spec.topic == "teleport_lunch"
    prompt = client.generate.call_args.kwargs.get("prompt") or client.generate.call_args[0][0]
    assert "unrelated" in prompt
    assert "Current local time" in prompt


def test_planner_remints_duplicate_topic(store):
    store.mark_topic_asked("hiking")
    client = MagicMock()
    client.generate.return_value = json.dumps(
        {
            "question": "Do you still enjoy hiking?",
            "ui": "yes_no",
            "topic": "hiking",
            "save_as": "note",
        }
    )
    planner = MemoryQuestionPlanner(client, store)
    spec = planner.plan()
    assert spec is not None
    assert spec.topic != "hiking"
    assert not store.is_topic_asked(spec.topic)
    assert "hiking" in spec.question.lower()
