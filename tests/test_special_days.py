"""Tests for special-day calendar lookups and lines."""

from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest

from content.special_days import (
    pick_special_day_line,
    special_day_for,
    special_days_for,
)


def test_special_day_for_fixed_holiday():
    day = special_day_for(date(2026, 10, 31))
    assert day is not None
    assert day.name == "Halloween"
    assert day.kind == "international"


def test_special_day_for_april_fools():
    day = special_day_for(date(2026, 4, 1))
    assert day is not None
    assert day.name == "April Fools' Day"
    assert day.kind == "joke"


def test_special_day_for_friday_the_13th():
    # 13 February 2026 is a Friday.
    day = special_day_for(date(2026, 2, 13))
    assert day is not None
    assert day.name == "Friday the 13th"


def test_special_day_for_thanksgiving():
    # 26 November 2026 is the fourth Thursday.
    day = special_day_for(date(2026, 11, 26))
    assert day is not None
    assert day.name == "Thanksgiving"


def test_special_days_for_march_14_collision():
    matches = special_days_for(date(2026, 3, 14))
    names = {match.name for match in matches}
    assert names == {"Pi Day", "White Day"}


def test_pick_special_day_line_formats_name():
    day = special_day_for(date(2026, 12, 25))
    assert day is not None
    with patch("content.special_days.random.choice", return_value=day.lines[0]):
        line = pick_special_day_line(day)
    assert day.name in line
    assert "{name}" not in line


def test_special_day_for_ordinary_day_is_none():
    assert special_day_for(date(2026, 7, 28)) is None


def test_maybe_announce_special_day_speaks_when_enabled():
    from kinito.features.content import ContentMixin

    class Stub(ContentMixin):
        pass

    stub = Stub()
    stub._special_days_enabled = True
    stub._can_initiate_spontaneous_speech = MagicMock(return_value=True)
    stub.speak = MagicMock()
    halloween = special_day_for(date(2026, 10, 31))
    with (
        patch("kinito.features.content.special_day_for", return_value=halloween),
        patch("kinito.features.content.pick_special_day_line", return_value="Happy Halloween!"),
    ):
        assert stub.maybe_announce_special_day() is True
    stub.speak.assert_called_once_with("Happy Halloween!", skip_ai=True)


def test_maybe_announce_special_day_skips_when_disabled():
    from kinito.features.content import ContentMixin

    class Stub(ContentMixin):
        pass

    stub = Stub()
    stub._special_days_enabled = False
    stub.speak = MagicMock()
    assert stub.maybe_announce_special_day() is False
    stub.speak.assert_not_called()


def test_print_current_datetime_includes_date_and_time():
    from kinito.features.programs import ProgramsMixin

    class Stub(ProgramsMixin):
        pass

    stub = Stub()
    stub.speak = MagicMock()
    fixed = datetime(2026, 7, 28, 14, 5)
    with patch("kinito.features.programs.datetime") as mock_dt:
        mock_dt.now.return_value = fixed
        stub.print_current_datetime()

    spoken = stub.speak.call_args[0][0]
    assert "14:05" in spoken
    assert "Tuesday" in spoken
    assert "July" in spoken
    assert "28" in spoken
