"""Tests for Ollama memory question planning."""

import json
from unittest.mock import MagicMock

import pytest

from content.memory_keys import ALLOWED_FACT_KEYS
from kinito.memory.question_planner import (
    MemoryQuestionPlanner,
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
    memory.set_fact("user_name", "Alex")
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
            "save_as": "user_name",
        }
    )
    assert spec is not None
    assert spec.save_as == "note"


def test_apply_extraction_does_not_overwrite_protected_user_name(store):
    store.set_fact("user_name", "Ben")
    store.apply_extraction(
        update_facts={"user_name": "Metal"},
        allowed_fact_keys=ALLOWED_FACT_KEYS,
    )
    assert store.get_fact("user_name") == "Ben"


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


def test_planner_returns_none_for_duplicate_topic(store):
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
    assert planner.plan() is None
