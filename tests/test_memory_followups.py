"""Tests for scripted memory follow-up templates."""

import pytest

from content.memory_followups import pick_template_followup
from kinito.memory.store import MemoryStore


@pytest.fixture
def memory_dir(tmp_path):
    return str(tmp_path / "user_media")


@pytest.fixture
def store(memory_dir):
    return MemoryStore(directory=memory_dir)


def test_pick_template_followup_requires_fact(store):
    store.set_fact("user_name", "Alex")
    spec = pick_template_followup(store)
    assert spec is not None
    assert "Alex" in spec.question
    assert spec.topic == "weekend_plans"


def test_pick_template_followup_skips_asked_topics(store):
    store.set_fact("favorite_food", "Pizza")
    store.mark_topic_asked("cooks_favorite_food")
    spec = pick_template_followup(store)
    assert spec is None or spec.topic != "cooks_favorite_food"


def test_pick_template_followup_returns_none_without_facts(store):
    assert pick_template_followup(store) is None


def test_pick_template_followup_can_verify_favorite_color(store):
    store.set_fact("favorite_color", "black")
    # Exhaust non-verify topics that also require favorite_color / others first is random;
    # mark exploratory topics so only verify remains likely, then force by marking all else.
    for topic in (
        "weekend_plans",
        "cooks_favorite_food",
        "hobby_duration",
        "pet_company",
        "color_everywhere",
        "book_reread",
        "verify_favorite_food",
        "verify_hobby",
        "verify_favorite_drink",
        "verify_favorite_movie",
        "verify_favorite_snack",
        "verify_favorite_season",
        "verify_pet",
        "verify_likes_programming",
        "verify_likes_music",
        "verify_likes_coffee",
    ):
        store.mark_topic_asked(topic)

    spec = pick_template_followup(store)
    assert spec is not None
    assert spec.topic == "verify_favorite_color"
    assert "black" in spec.question
    assert spec.ui == "yes_no"
    assert spec.save_as == "verify:favorite_color"


def test_pick_template_followup_skips_likes_already_no(store):
    store.set_fact("likes_programming", "no")
    for topic in (
        "weekend_plans",
        "cooks_favorite_food",
        "hobby_duration",
        "pet_company",
        "color_everywhere",
        "book_reread",
        "verify_favorite_color",
        "verify_favorite_food",
        "verify_hobby",
        "verify_favorite_drink",
        "verify_favorite_movie",
        "verify_favorite_snack",
        "verify_favorite_season",
        "verify_pet",
        "verify_likes_music",
        "verify_likes_coffee",
    ):
        store.mark_topic_asked(topic)

    assert pick_template_followup(store) is None
