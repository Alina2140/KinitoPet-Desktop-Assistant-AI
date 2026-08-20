"""Tests for friendship / first-met relationship milestones."""

from datetime import date
from unittest.mock import MagicMock

import pytest

from content import dialogue as dlg
from content.friendship import (
    days_together,
    ensure_first_met,
    format_friendship_duration,
    friendship_years,
    is_met_anniversary_today,
    parse_first_met,
    pick_friendship_duration_line,
    pick_met_anniversary_line,
)
from content.memory_keys import (
    ALLOWED_FACT_KEYS,
    EXTRA_FACT_KEYS,
    FRIENDSHIP_DURATION_COOLDOWN_DAYS,
    FRIENDSHIP_DURATION_TOPIC,
    PROTECTED_FACT_KEYS,
)
from kinito.features.content import ContentMixin
from kinito.memory.store import MemoryStore


def test_first_met_is_allowed_and_protected():
    assert "first_met" in EXTRA_FACT_KEYS
    assert "first_met" in ALLOWED_FACT_KEYS
    assert "first_met" in PROTECTED_FACT_KEYS


def test_parse_first_met():
    assert parse_first_met("2024-08-06") == date(2024, 8, 6)
    assert parse_first_met("bad") is None
    assert parse_first_met(None) is None


def test_ensure_first_met_sets_once(tmp_path):
    store = MemoryStore(directory=str(tmp_path))
    first = ensure_first_met(store, today=date(2026, 8, 6))
    assert first == "2026-08-06"
    second = ensure_first_met(store, today=date(2026, 12, 1))
    assert second == "2026-08-06"


def test_format_friendship_duration():
    assert format_friendship_duration("2026-08-06", today=date(2026, 8, 6)) == "today"
    assert format_friendship_duration("2026-08-05", today=date(2026, 8, 6)) == "1 day"
    assert format_friendship_duration("2026-07-30", today=date(2026, 8, 6)) == "7 days"
    assert format_friendship_duration("2026-07-01", today=date(2026, 8, 6)).endswith("weeks")
    assert format_friendship_duration("2025-08-06", today=date(2026, 8, 6)) == "1 year"


def test_is_met_anniversary_requires_full_year():
    assert is_met_anniversary_today("2026-08-06", today=date(2026, 8, 6)) is False
    assert is_met_anniversary_today("2025-08-06", today=date(2026, 8, 6)) is True
    assert friendship_years("2025-08-06", today=date(2026, 8, 6)) == 1
    assert days_together("2025-08-06", today=date(2026, 8, 6)) == 365


def test_pick_lines_format_placeholders():
    duration_line = pick_friendship_duration_line(
        ("We've known each other for {duration}.",),
        duration="3 weeks",
    )
    assert "3 weeks" in duration_line
    anniversary = pick_met_anniversary_line(
        dlg.MET_ANNIVERSARY_LINES,
        years=2,
        name="Alex",
        duration="2 years",
    )
    assert "2 years" in anniversary


class _FriendshipStub(ContentMixin):
    pass


@pytest.fixture
def friendship_app(tmp_path):
    app = _FriendshipStub()
    app._memory = MemoryStore(directory=str(tmp_path))
    app._can_initiate_spontaneous_speech = MagicMock(return_value=True)
    app.speak = MagicMock()
    app.chat_user_label = MagicMock(return_value="Alex")
    return app


def test_maybe_mention_friendship_duration_speaks_and_cools_down(friendship_app):
    friendship_app._memory.set_fact("first_met", "2026-07-01")
    assert friendship_app.maybe_mention_friendship_duration() is True
    friendship_app.speak.assert_called_once()
    assert friendship_app._memory.is_topic_on_cooldown(
        FRIENDSHIP_DURATION_TOPIC, days=FRIENDSHIP_DURATION_COOLDOWN_DAYS
    )
    friendship_app.speak.reset_mock()
    assert friendship_app.maybe_mention_friendship_duration() is False
    friendship_app.speak.assert_not_called()


def test_say_known_since_speaks_duration(friendship_app):
    friendship_app._memory.set_fact("first_met", "2026-07-01")
    friendship_app.say_known_since()
    friendship_app.speak.assert_called_once()
    spoken = friendship_app.speak.call_args[0][0]
    assert any(
        word in spoken
        for word in ("day", "days", "week", "weeks", "month", "months", "year", "years", "today")
    )


def test_say_known_since_works_without_cooldown(friendship_app):
    friendship_app._memory.set_fact("first_met", "2026-07-01")
    friendship_app.say_known_since()
    friendship_app.speak.reset_mock()
    friendship_app.say_known_since()
    friendship_app.speak.assert_called_once()


def test_maybe_announce_met_anniversary(friendship_app):
    friendship_app._memory.set_fact("first_met", "2025-08-06")
    # Freeze "today" by patching helpers via stored date matching system date —
    # use set_fact with a date that is anniversary of whatever today is.
    today = date.today()
    met = date(today.year - 2, today.month, today.day)
    friendship_app._memory.set_fact("first_met", met.isoformat())
    assert friendship_app.maybe_announce_met_anniversary() is True
    friendship_app.speak.assert_called_once()


def test_set_fact_rejects_invalid_first_met(tmp_path):
    store = MemoryStore(directory=str(tmp_path))
    store.set_fact("first_met", "not-a-date")
    assert store.get_fact("first_met") is None
    store.set_fact("first_met", "2024-01-15")
    assert store.get_fact("first_met") == "2024-01-15"
