"""Tests for birthday parsing, consent dialog, and congratulations."""

from datetime import date
from unittest.mock import MagicMock

import pytest

from content import dialogue as dlg
from content.birthday import (
    BIRTHDAY_DECLINED,
    birthday_age,
    birthday_month_day,
    birthday_year,
    format_birthday_display,
    is_birthday_today,
    parse_birthday,
    pick_birthday_congrats_line,
)
from content.dialog_registry import find_dialog_spec, handle_dialog_response
from content.memory_keys import ALLOWED_FACT_KEYS, ASK_ONCE_MARKERS
from kinito.memory.store import MemoryStore


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("March 15", "03-15"),
        ("15 March", "03-15"),
        ("Mar 15", "03-15"),
        ("03-15", "03-15"),
        ("3/15", "03-15"),
        ("15.03", "03-15"),
        ("15.03.1990", "1990-03-15"),
        ("1990-03-15", "1990-03-15"),
        ("March 15 1990", "1990-03-15"),
        ("March 15, 1990", "1990-03-15"),
        ("15 March 1990", "1990-03-15"),
        ("3/15/1990", "1990-03-15"),
        ("15/3/1990", "1990-03-15"),
        ("02-29", "02-29"),
        ("not a date", None),
        ("", None),
    ],
)
def test_parse_birthday(raw, expected):
    assert parse_birthday(raw) == expected


def test_birthday_month_day_and_declined():
    assert birthday_month_day("03-15") == (3, 15)
    assert birthday_month_day("1990-03-15") == (3, 15)
    assert birthday_month_day(BIRTHDAY_DECLINED) is None
    assert birthday_month_day("no") is None


def test_birthday_year_and_age():
    assert birthday_year("03-15") is None
    assert birthday_year("1990-03-15") == 1990
    assert birthday_age("1990-03-15", date(2026, 3, 15)) == 36
    assert birthday_age("1990-03-15", date(2026, 3, 14)) == 35
    assert birthday_age("03-15", date(2026, 3, 15)) is None


def test_format_birthday_display():
    assert format_birthday_display("03-15") == "March 15"
    assert format_birthday_display("1990-03-15") == "March 15, 1990"


def test_is_birthday_today_matches_month_day():
    assert is_birthday_today("07-28", date(2026, 7, 28)) is True
    assert is_birthday_today("1990-07-28", date(2026, 7, 28)) is True
    assert is_birthday_today("07-28", date(2026, 7, 29)) is False


def test_is_birthday_today_leap_day_on_feb_28_non_leap():
    assert is_birthday_today("02-29", date(2026, 2, 28)) is True
    assert is_birthday_today("02-29", date(2026, 2, 27)) is False


def test_pick_birthday_congrats_line_includes_name():
    line = pick_birthday_congrats_line(
        ("Happy birthday, {name}!",),
        name="Alina",
    )
    assert line == "Happy birthday, Alina!"


def test_pick_birthday_congrats_line_uses_age_when_known():
    line = pick_birthday_congrats_line(
        (
            "Happy birthday, {name}!",
            "Happy birthday, {name}! Turning {age}.",
        ),
        name="Alina",
        age=36,
    )
    assert line == "Happy birthday, Alina! Turning 36."


def test_birthday_allowed_and_ask_once():
    assert "birthday" in ALLOWED_FACT_KEYS
    assert dlg.BIRTHDAY_CONSENT_QUESTION in ASK_ONCE_MARKERS


def test_birthday_consent_no_stores_declined(tmp_path):
    app = MagicMock()
    app._memory = MemoryStore(directory=str(tmp_path / "media"))
    app.speak = MagicMock()

    spec = find_dialog_spec(dlg.BIRTHDAY_CONSENT_QUESTION)
    handle_dialog_response(app, spec, dlg.BUTTON_NO)

    assert app._memory.get_fact("birthday") == BIRTHDAY_DECLINED
    assert app._memory.is_answered(dlg.BIRTHDAY_CONSENT_QUESTION)
    app.speak.assert_called_once()


def test_birthday_consent_yes_asks_for_date(tmp_path):
    app = MagicMock()
    app._memory = MemoryStore(directory=str(tmp_path / "media"))
    app.speak = MagicMock()

    spec = find_dialog_spec(dlg.BIRTHDAY_CONSENT_QUESTION)
    handle_dialog_response(app, spec, dlg.BUTTON_YES)

    assert app._memory.is_answered(dlg.BIRTHDAY_CONSENT_QUESTION)
    assert app._memory.get_fact("birthday") is None
    app.speak.assert_called_once_with(dlg.BIRTHDAY_DATE_QUESTION, 45, True)


def test_birthday_date_saves_parsed_value(tmp_path):
    app = MagicMock()
    app._memory = MemoryStore(directory=str(tmp_path / "media"))
    app.speak = MagicMock()

    spec = find_dialog_spec(dlg.BIRTHDAY_DATE_MARKER)
    handle_dialog_response(app, spec, "March 15")

    assert app._memory.get_fact("birthday") == "03-15"
    spoken = app.speak.call_args[0][0]
    assert "March 15" in spoken


def test_birthday_date_saves_year_when_given(tmp_path):
    app = MagicMock()
    app._memory = MemoryStore(directory=str(tmp_path / "media"))
    app.speak = MagicMock()

    spec = find_dialog_spec(dlg.BIRTHDAY_DATE_MARKER)
    handle_dialog_response(app, spec, "March 15 1990")

    assert app._memory.get_fact("birthday") == "1990-03-15"
    spoken = app.speak.call_args[0][0]
    assert "1990" in spoken


def test_birthday_date_retries_on_invalid(tmp_path):
    app = MagicMock()
    app._memory = MemoryStore(directory=str(tmp_path / "media"))
    app.speak = MagicMock()

    spec = find_dialog_spec(dlg.BIRTHDAY_DATE_MARKER)
    handle_dialog_response(app, spec, "blue")

    assert app._memory.get_fact("birthday") is None
    app.speak.assert_called_once_with(dlg.BIRTHDAY_DATE_RETRY, 45, True)


def test_set_fact_normalizes_birthday(tmp_path):
    store = MemoryStore(directory=str(tmp_path / "media"))
    store.set_fact("birthday", "15.03.1994")
    assert store.get_fact("birthday") == "1994-03-15"
    store.set_fact("birthday", "03-15")
    assert store.get_fact("birthday") == "03-15"
