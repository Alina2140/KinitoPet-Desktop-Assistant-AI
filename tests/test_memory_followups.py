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
