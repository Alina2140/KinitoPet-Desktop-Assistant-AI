"""Tests for memory note validation heuristics."""

import pytest

from kinito.memory.validation import is_storable_note


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
        "Prefers speaking Deutsch with Kinito",
        "Kinito noticed user often works late on Fridays",
        "Ben loves Kinito",
        "Ben is an enthusiastic user",
        "Ben enjoys chatting with the assistant when feeling bored",
        "She often expresses excitement when discussing Kinito's updates",
    ],
)
def test_accepts_meaningful_memories(text):
    assert is_storable_note(text, source="chat") is True


def test_notes_are_near_duplicate():
    from kinito.memory.validation import notes_are_near_duplicate

    assert notes_are_near_duplicate("Ben loves Kinito", "Ben has a strong affection for Kinito")
    assert notes_are_near_duplicate(
        "Ben often expresses enthusiasm for Kinito",
        "Ben is known to express love for Kinito.",
    )
    assert not notes_are_near_duplicate("Movie nights with Sarah", "Works as a nurse in Berlin")


def test_question_source_always_allowed():
    assert is_storable_note("smily face", source="question") is True
