"""Tests for chat memory extraction parsing and application."""

import json
from unittest.mock import MagicMock

import pytest

from kinito.memory.extractor import (
    MemoryExtractor,
    normalize_extraction,
    parse_extraction_response,
    should_block_fact_updates,
    value_mentioned_in_text,
)
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
        "update_facts": {"secret_password": "nope", "hobbies": "chess"},
    }
    normalized = normalize_extraction(payload, user_text="I enjoy chess on weekends")
    assert normalized["update_facts"] == {"hobbies": {"value": "chess", "intent": "add"}}


def test_normalize_extraction_allows_preference_flip():
    payload = {
        "add_notes": [],
        "remove_notes": [],
        "update_facts": {
            "likes_programming": {"value": "no", "intent": "replace"},
            "favorite_colors": {"value": "blue", "intent": "add"},
        },
    }
    normalized = normalize_extraction(
        payload,
        user_text="I don't like programming anymore and my favorite color is blue",
    )
    assert normalized["update_facts"]["likes_programming"]["value"] == "no"
    assert normalized["update_facts"]["favorite_colors"]["value"] == "blue"


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


def test_normalize_extraction_rejects_assistant_spam_notes():
    payload = {
        "add_notes": ["I'm a bit invested in our little hangman sessions."],
        "remove_notes": [],
        "update_facts": {},
    }
    normalized = normalize_extraction(payload)
    assert normalized["add_notes"] == []


def test_normalize_rejects_bare_word_food_without_preference_question():
    payload = {
        "update_facts": {"favorite_food": {"value": "Oranges", "intent": "replace"}},
        "add_notes": [],
        "remove_notes": [],
    }
    messages = [{"role": "user", "content": "oranges"}]
    normalized = normalize_extraction(payload, user_text="oranges", messages=messages)
    assert normalized["update_facts"] == {}


def test_normalize_allows_bare_answer_after_preference_question():
    payload = {
        "update_facts": {"favorite_food": {"value": "Pizza", "intent": "replace"}},
        "add_notes": [],
        "remove_notes": [],
    }
    messages = [
        {"role": "assistant", "content": "What's your favorite food?"},
        {"role": "user", "content": "Pizza"},
    ]
    normalized = normalize_extraction(payload, user_text="Pizza", messages=messages)
    assert normalized["update_facts"]["favorite_food"]["value"] == "Pizza"


def test_normalize_rejects_rainbow_color_list_not_in_user_text():
    payload = {
        "update_facts": {
            "favorite_colors": {
                "value": ["Red", "Orange", "Yellow", "Green", "Blue", "Indigo", "Violet"],
                "intent": "replace",
            }
        },
        "add_notes": [],
        "remove_notes": [],
    }
    normalized = normalize_extraction(
        payload,
        user_text="We were chatting about rainbows earlier",
    )
    assert "favorite_colors" not in normalized["update_facts"]


def test_normalize_accepts_english_snack_list_replace():
    payload = {
        "update_facts": {
            "favorite_snacks": {
                "value": ["oranges", "chips", "ice cream"],
                "intent": "replace",
            }
        },
        "add_notes": [],
        "remove_notes": [],
    }
    normalized = normalize_extraction(
        payload,
        user_text="My favorite snacks are oranges, chips, ice cream",
    )
    assert normalized["update_facts"]["favorite_snacks"]["intent"] == "replace"
    assert normalized["update_facts"]["favorite_snacks"]["value"] == [
        "oranges",
        "chips",
        "ice cream",
    ]


def test_normalize_legacy_hobby_string_defaults_to_add():
    payload = {"update_facts": {"hobbies": "Crochet"}, "add_notes": [], "remove_notes": []}
    normalized = normalize_extraction(payload, user_text="I also crochet")
    assert normalized["update_facts"]["hobbies"] == {"value": "Crochet", "intent": "add"}


def test_extractor_applies_ollama_result(store, memory_dir):
    client = MagicMock()
    client.generate.return_value = json.dumps(
        {
            "add_notes": ["Has a cat named Luna"],
            "remove_notes": [],
            "update_facts": {"pets": {"value": "Luna", "intent": "add"}},
        }
    )
    extractor = MemoryExtractor(client, store)
    extractor.extract_from_turn("I have a cat named Luna", "That sounds lovely!")

    snapshot = store.snapshot()
    assert snapshot["facts"]["pets"] == "Luna"
    assert snapshot["notes"][0]["text"] == "Has a cat named Luna"
    client.generate.assert_called_once()
    assert client.generate.call_args.kwargs["max_tokens"] >= 400


def test_normalize_extraction_accepts_hobby_list():
    payload = {
        "add_notes": [],
        "remove_notes": [],
        "update_facts": {"hobbies": ["Drawing", "Reading"]},
    }
    normalized = normalize_extraction(
        payload,
        user_text="My hobbies are Drawing and Reading",
    )
    assert normalized["update_facts"]["hobbies"]["intent"] == "replace"
    assert normalized["update_facts"]["hobbies"]["value"] == ["Drawing", "Reading"]


def test_extractor_merges_new_hobby_string(store):
    store.set_fact("hobbies", "Drawing")
    client = MagicMock()
    client.generate.return_value = json.dumps(
        {
            "add_notes": [],
            "remove_notes": [],
            "update_facts": {"hobbies": "Crochet"},
        }
    )
    extractor = MemoryExtractor(client, store)
    extractor.extract_from_turn("I also crochet", "Nice!")

    assert store.get_fact_values("hobbies") == ["Drawing", "Crochet"]


def test_extractor_replace_and_remove_intents(store):
    store.set_fact("favorite_snacks", "Chips, Candy")
    client = MagicMock()
    client.generate.return_value = json.dumps(
        {
            "add_notes": [],
            "remove_notes": [],
            "update_facts": {
                "favorite_snacks": {
                    "value": ["oranges", "chips", "ice cream"],
                    "intent": "replace",
                }
            },
        }
    )
    extractor = MemoryExtractor(client, store)
    extractor.extract_from_turn(
        "My favorite snacks are oranges, chips, ice cream",
        "Yum!",
    )
    assert store.get_fact_values("favorite_snacks") == ["oranges", "chips", "ice cream"]

    client.generate.return_value = json.dumps(
        {
            "update_facts": {
                "favorite_snacks": {"value": ["chips"], "intent": "remove"},
            },
            "add_notes": [],
            "remove_notes": [],
        }
    )
    extractor.extract_from_turn("I don't like chips anymore", "Okay")
    assert store.get_fact_values("favorite_snacks") == ["oranges", "ice cream"]


def test_extractor_ignores_invalid_json(store):
    client = MagicMock()
    client.generate.return_value = "not json at all"
    extractor = MemoryExtractor(client, store)
    extractor.extract_from_turn("hello", "hi")
    assert store.snapshot()["notes"] == []


def test_extractor_uses_multi_turn_messages(store):
    client = MagicMock()
    client.generate.return_value = json.dumps(
        {
            "update_facts": {"favorite_food": {"value": "Pizza", "intent": "replace"}},
            "add_notes": [],
            "remove_notes": [],
        }
    )
    extractor = MemoryExtractor(client, store)
    extractor.extract_from_messages(
        [
            {"role": "assistant", "content": "What's your favorite food?"},
            {"role": "user", "content": "Pizza"},
            {"role": "assistant", "content": "Nice choice!"},
        ]
    )
    assert store.get_fact("favorite_food") == "Pizza"
    prompt = client.generate.call_args.args[0]
    assert "What's your favorite food?" in prompt
    assert "Pizza" in prompt


def test_should_block_game_chat_and_value_mention():
    assert should_block_fact_updates("hangman", [{"role": "user", "content": "hangman"}])
    assert value_mentioned_in_text("oranges", "My snacks are oranges and chips")
    assert not value_mentioned_in_text("Violet", "we talked about rainbows")


def test_normalize_rejects_casual_book_mention_as_favorite_but_allows_one_note():
    payload = {
        "update_facts": {"favorite_book": {"value": "Dracula", "intent": "replace"}},
        "add_notes": ["User is rereading Dracula"],
        "remove_notes": [],
    }
    user = "Sure! I've recently started reading Dracula again! I started it once but didn't finish it."
    normalized = normalize_extraction(payload, user_text=user)
    assert "favorite_book" not in normalized["update_facts"]
    assert normalized["add_notes"] == ["User is rereading Dracula"]


def test_normalize_rejects_note_near_duplicate_of_existing():
    payload = {
        "update_facts": {},
        "add_notes": ["Movie nights with Sarah on weekends"],
        "remove_notes": [],
    }
    existing = [{"text": "Movie night with Sarah every weekend", "source": "chat"}]
    normalized = normalize_extraction(payload, existing_notes=existing)
    assert normalized["add_notes"] == []


def test_normalize_allows_richer_upgrade_of_existing_note():
    payload = {
        "update_facts": {},
        "add_notes": ["User is reading Dracula again and finds it a little boring"],
        "remove_notes": [],
    }
    existing = [{"text": "User is reading Dracula again", "source": "chat"}]
    normalized = normalize_extraction(payload, existing_notes=existing)
    assert normalized["add_notes"] == [
        "User is reading Dracula again and finds it a little boring"
    ]


def test_normalize_accepts_explicit_favorite_book():
    payload = {
        "update_facts": {"favorite_book": {"value": "Dracula", "intent": "replace"}},
        "add_notes": [],
        "remove_notes": [],
    }
    normalized = normalize_extraction(
        payload,
        user_text="My favorite book is Dracula",
    )
    assert normalized["update_facts"]["favorite_book"]["value"] == "Dracula"
