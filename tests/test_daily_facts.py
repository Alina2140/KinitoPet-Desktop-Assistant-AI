"""Tests for dated daily memory facts."""

from datetime import date, timedelta

from kinito.memory.daily_facts import (
    format_daily_fact,
    is_fresh_daily_fact,
    parse_daily_fact,
)


def test_format_and_parse_roundtrip():
    raw = format_daily_fact("low", today=date(2026, 9, 3))
    assert raw == "2026-09-03|low"
    parsed = parse_daily_fact(raw)
    assert parsed == ("low", date(2026, 9, 3))


def test_parse_rejects_undated_and_empty():
    assert parse_daily_fact("low") is None
    assert parse_daily_fact("2026-09-03|") is None
    assert parse_daily_fact("not-a-date|low") is None
    assert parse_daily_fact(None) is None


def test_plans_may_contain_pipe():
    raw = format_daily_fact("dinner|then movies")
    assert parse_daily_fact(raw) == ("dinner|then movies", date.today())


def test_is_fresh_daily_fact():
    today = date.today()
    assert is_fresh_daily_fact(format_daily_fact("high", today=today), today=today)
    assert not is_fresh_daily_fact(
        format_daily_fact("high", today=today - timedelta(days=1)), today=today
    )
    assert not is_fresh_daily_fact("high", today=today)
