"""Tests for chat memory extraction parsing and application."""

import json
from unittest.mock import MagicMock

import pytest

from kinito.memory.extractor import MemoryExtractor, normalize_extraction, parse_extraction_response
from kinito.memory.store import MemoryStore


@pytest.fixture
def memory_dir(tmp_path):
    return str(tmp_path / "user_media")


@pytest.fixture
def store(memory_dir):
    return MemoryStore(directory=memory_dir)


def test_parse_extraction_response_accepts_json_block():
    raw = 'Here you go:\n{"add_notes": ["Enjoys drinking tea"], "remove_notes": [], "update_facts": {}}'
    parsed = parse_extraction_response(raw)
    assert parsed["add_notes"] == ["Enjoys drinking tea"]


def test_normalize_extraction_rejects_unknown_fact_keys():
    payload = {
        "add_notes": ["Enjoys playing chess on weekends"],
        "remove_notes": [],
        "update_facts": {"secret_password": "nope", "hobby": "chess"},
    }
    normalized = normalize_extraction(payload)
    assert normalized["update_facts"] == {"hobby": "chess"}


def test_normalize_extraction_filters_junk_notes():
    payload = {
        "add_notes": [
            "Movie nights with Sarah",
            "smily with a hand next to its mouth",
        ],
        "remove_notes": [],
        "update_facts": {},
    }
    normalized = normalize_extraction(payload)
    assert normalized["add_notes"] == ["Movie nights with Sarah"]


def test_normalize_extraction_limits_new_notes_per_turn():
    payload = {
        "add_notes": [f"Plans with friend number {index}" for index in range(5)],
        "remove_notes": [],
        "update_facts": {},
    }
    normalized = normalize_extraction(payload)
    assert len(normalized["add_notes"]) == 1


def test_extractor_applies_ollama_result(store, memory_dir):
    client = MagicMock()
    client.generate.return_value = json.dumps(
        {
            "add_notes": ["Has a cat named Luna"],
            "remove_notes": [],
            "update_facts": {"pet": "cat named Luna"},
        }
    )
    extractor = MemoryExtractor(client, store)
    extractor.extract_from_turn("I have a cat named Luna", "That sounds lovely!")

    snapshot = store.snapshot()
    assert snapshot["facts"]["pet"] == "cat named Luna"
    assert snapshot["notes"][0]["text"] == "Has a cat named Luna"
    client.generate.assert_called_once()


def test_extractor_ignores_invalid_json(store):
    client = MagicMock()
    client.generate.return_value = "not json at all"
    extractor = MemoryExtractor(client, store)
    extractor.extract_from_turn("hello", "hi")
    assert store.snapshot()["notes"] == []
