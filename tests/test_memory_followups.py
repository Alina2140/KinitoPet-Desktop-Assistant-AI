"""Tests for scripted memory follow-up templates."""

from datetime import date, timedelta

import pytest

from content.memory_followups import VERIFY_TOPIC_COOLDOWN_DAYS, pick_template_followup
from kinito.memory.store import MemoryStore


@pytest.fixture
def memory_dir(tmp_path):
    return str(tmp_path / "user_media")


@pytest.fixture
def store(memory_dir):
    return MemoryStore(directory=memory_dir)


def test_pick_template_followup_requires_fact(store):
    store.set_fact("user_names", "Alex")
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
    store.set_fact("favorite_colors", "black")
    for topic in (
        "weekend_plans",
        "cooks_favorite_food",
        "hobby_duration",
        "pet_company",
        "color_everywhere",
        "book_reread",
    ):
        store.mark_topic_asked(topic)

    spec = pick_template_followup(store)
    assert spec is not None
    assert spec.topic == "verify_favorite_color"
    assert "black" in spec.question
    assert spec.ui == "yes_no"
    assert spec.save_as == "verify:favorite_colors"
    assert spec.context_value == "black"


def test_verify_followup_can_repeat_after_cooldown(store):
    store.set_fact("favorite_colors", "black")
    for topic in (
        "weekend_plans",
        "cooks_favorite_food",
        "hobby_duration",
        "pet_company",
        "color_everywhere",
        "book_reread",
    ):
        store.mark_topic_asked(topic)

    today = date.today()
    store.mark_topic_asked("verify_favorite_color", today=today)
    assert store.is_topic_on_cooldown(
        "verify_favorite_color", days=VERIFY_TOPIC_COOLDOWN_DAYS, today=today
    )
    assert pick_template_followup(store) is None

    store.mark_topic_asked(
        "verify_favorite_color",
        today=today - timedelta(days=VERIFY_TOPIC_COOLDOWN_DAYS),
    )
    spec = pick_template_followup(store)
    assert spec is not None
    assert spec.topic == "verify_favorite_color"


def test_verify_followup_without_ask_date_is_eligible_again(store):
    """Legacy asked verify topics (no topic_asked_at) may be asked again."""
    store.set_fact("favorite_colors", "purple")
    for topic in (
        "weekend_plans",
        "cooks_favorite_food",
        "hobby_duration",
        "pet_company",
        "color_everywhere",
        "book_reread",
        "verify_favorite_color",
    ):
        store._data["asked_topics"].append(topic)
    store.save()

    assert store.is_topic_asked("verify_favorite_color")
    assert not store.is_topic_on_cooldown(
        "verify_favorite_color", days=VERIFY_TOPIC_COOLDOWN_DAYS
    )
    spec = pick_template_followup(store)
    assert spec is not None
    assert spec.topic == "verify_favorite_color"


def test_pick_template_followup_skips_likes_already_no(store):
    store.set_fact("likes_programming", "no")
    for topic in (
        "weekend_plans",
        "cooks_favorite_food",
        "hobby_duration",
        "pet_company",
        "color_everywhere",
        "book_reread",
    ):
        store.mark_topic_asked(topic)

    assert pick_template_followup(store) is None


def test_pick_template_followup_uses_single_hobby_item(store):
    store.set_fact("hobbies", "Drawing, Reading, Crochet")
    for topic in (
        "weekend_plans",
        "cooks_favorite_food",
        "pet_company",
        "color_everywhere",
        "book_reread",
    ):
        store.mark_topic_asked(topic)
    store.mark_topic_asked("verify_hobby", today=date.today())

    spec = pick_template_followup(store)
    assert spec is not None
    assert spec.topic == "hobby_duration"
    mentioned = [name for name in ("Drawing", "Reading", "Crochet") if name in spec.question]
    assert len(mentioned) == 1
