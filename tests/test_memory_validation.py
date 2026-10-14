"""Tests for memory note validation heuristics."""

import pytest

from kinito.memory.validation import (
    dedupe_note_entries,
    is_assistant_spam_note,
    is_ephemeral_note,
    is_meaningfully_richer_note,
    is_storable_note,
    notes_are_near_duplicate,
    should_skip_note_against_existing,
)


@pytest.mark.parametrize(
    "text",
    [
        "smily with a hand next to its mouth",
        "emoji with raised eyebrow",
        "no change needed",
        "Kinito described the sprite's facial expression",
        "short",
        "Had a good day today",
        "Nice weather outside",
        "thanks",
        "I'm a bit invested in our little hangman sessions.",
        "You like rain, don't you?",
        "Youthful energy! I like it.",
        "I leave work early today",
        "User was talking about books in this chat",
    ],
)
def test_rejects_junk_notes(text):
    assert is_storable_note(text, source="chat") is False


@pytest.mark.parametrize(
    "text",
    [
        "Movie nights with Anna on weekends",
        "Works as a software developer in Berlin",
        "Has a cat named Luna",
        "Plans to visit grandma next month",
        "weekend_plans: Movie nights with Anna (Hey Ben, got any plans?)",
        "User prefers German words in chat",
        "Prefers speaking English with Kinito",
        "User often works late on Fridays",
        "Ben loves jazz music",
        "Ben enjoys hiking on weekends",
        "User is reading Dracula again",
        "User is rereading classic books, currently reading Dracula",
    ],
)
def test_accepts_meaningful_memories(text):
    assert is_storable_note(text, source="chat") is True


@pytest.mark.parametrize(
    "text",
    [
        "You often get creative with Hangman",
        "I'm not the best hangman",
        "relax and enjoy the raindrops on the roof",
    ],
)
def test_assistant_spam_detector(text):
    assert is_assistant_spam_note(text) is True


def test_ephemeral_only_blocks_chat_meta():
    assert is_ephemeral_note("User was talking about books in this chat") is True
    assert is_ephemeral_note("User is reading Dracula again") is False


def test_notes_are_near_duplicate():
    assert notes_are_near_duplicate("Ben loves Kinito", "Ben has a strong affection for Kinito")
    assert notes_are_near_duplicate(
        "User is reading Dracula again",
        "User is rereading Dracula again",
    )
    assert notes_are_near_duplicate(
        "User finds Dracula a little boring",
        "User is reading Dracula, but finds it a little boring",
    )
    assert not notes_are_near_duplicate("Movie nights with Sarah", "Works as a nurse in Berlin")


def test_should_skip_near_duplicate_but_allow_richer_upgrade():
    existing = [{"text": "User is reading Dracula again"}]
    assert should_skip_note_against_existing("User is rereading Dracula", existing) is True
    richer = "User is reading Dracula again and finds it a little boring"
    assert is_meaningfully_richer_note(richer, existing[0]["text"]) is True
    assert should_skip_note_against_existing(richer, existing) is False


def test_dedupe_note_entries_keeps_richest():
    notes = [
        {"text": "User is reading Dracula again", "source": "chat"},
        {"text": "User is reading Dracula, but finds it a little boring", "source": "chat"},
        {"text": "Movie nights with Sarah", "source": "chat"},
    ]
    deduped = dedupe_note_entries(notes)
    texts = [note["text"] for note in deduped]
    assert "Movie nights with Sarah" in texts
    assert len([t for t in texts if "Dracula" in t]) == 1
    assert "User is reading Dracula, but finds it a little boring" in texts


def test_question_source_always_allowed():
    assert is_storable_note("smily face", source="question") is True
