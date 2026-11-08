"""Tests for special-day calendar lookups and lines."""

from datetime import date, datetime
from unittest.mock import MagicMock, patch

from content.special_days import (
    pick_special_day_line,
    seasonal_modifiers,
    seasonal_multiplier,
    special_day_for,
    special_days_for,
    upcoming_special_days,
)


def test_upcoming_special_days_includes_christmas_in_november():
    upcoming = dict(
        (day.name, days) for day, days in upcoming_special_days(date(2026, 11, 7))
    )
    assert upcoming["Christmas"] == 48
    assert upcoming["Thanksgiving"] == 19
    assert upcoming["Singles' Day"] == 4


def test_upcoming_special_days_skips_today_and_respects_horizon():
    upcoming = upcoming_special_days(date(2026, 12, 25), horizon_days=3)
    names = [day.name for day, _days in upcoming]
    assert "Christmas" not in names
    assert names == ["Boxing Day"]
    assert upcoming[0][1] == 1


def _countdown_stub(countdowns=None, birthday_days=None, enabled=True):
    from kinito.features.content import ContentMixin

    class Stub(ContentMixin):
        pass

    stub = Stub()
    stub._special_days_enabled = enabled
    stub._can_initiate_spontaneous_speech = MagicMock(return_value=True)
    stub.speak = MagicMock()
    stub.chat_user_label = MagicMock(return_value="Alina")
    stub._memory = MagicMock()
    stub._memory.get_fact.return_value = "03-15"
    patches = (
        patch(
            "kinito.features.content.upcoming_special_days",
            return_value=countdowns or [],
        ),
        patch("content.birthday.days_until_birthday", return_value=birthday_days),
    )
    return stub, patches


def test_countdown_announces_special_day_days_away():
    from content import dialogue as dlg

    christmas = special_day_for(date(2026, 12, 25))
    stub, (p1, p2) = _countdown_stub([(christmas, 48)])
    with p1, p2:
        assert stub.maybe_announce_special_day_countdown() is True
    line = stub.speak.call_args[0][0]
    assert "Christmas" in line and "48" in line
    assert any(
        line == template.format(name="Christmas", days=48)
        for template in dlg.SPECIAL_DAY_COUNTDOWN_LINES
    )


def test_countdown_uses_tomorrow_lines_for_one_day():
    from content import dialogue as dlg

    christmas = special_day_for(date(2026, 12, 25))
    stub, (p1, p2) = _countdown_stub([(christmas, 1)])
    with p1, p2:
        assert stub.maybe_announce_special_day_countdown() is True
    line = stub.speak.call_args[0][0]
    assert line in [t.format(name="Christmas") for t in dlg.SPECIAL_DAY_TOMORROW_LINES]


def test_countdown_includes_user_birthday():
    from content import dialogue as dlg

    stub, (p1, p2) = _countdown_stub([], birthday_days=12)
    with p1, p2:
        assert stub.maybe_announce_special_day_countdown() is True
    line = stub.speak.call_args[0][0]
    assert line in [
        t.format(name="Alina", days=12) for t in dlg.BIRTHDAY_COUNTDOWN_LINES
    ]


def test_countdown_skips_birthday_today_or_far_away():
    for days in (0, 200, None):
        stub, (p1, p2) = _countdown_stub([], birthday_days=days)
        with p1, p2:
            assert stub.maybe_announce_special_day_countdown() is False
        stub.speak.assert_not_called()


def test_countdown_line_pools_are_large_unique_and_formattable():
    from content import dialogue as dlg

    pools = {
        "SPECIAL_DAY_COUNTDOWN_LINES": 15,
        "SPECIAL_DAY_TOMORROW_LINES": 10,
        "BIRTHDAY_COUNTDOWN_LINES": 12,
        "BIRTHDAY_TOMORROW_LINES": 8,
    }
    for name, minimum in pools.items():
        lines = getattr(dlg, name)
        assert len(lines) >= minimum, name
        assert len(set(lines)) == len(lines), name
        for line in lines:
            line.format(name="Christmas", days=5)


def test_countdown_skips_when_special_days_disabled():
    christmas = special_day_for(date(2026, 12, 25))
    stub, (p1, p2) = _countdown_stub([(christmas, 10)], enabled=False)
    with p1, p2:
        assert stub.maybe_announce_special_day_countdown() is False
    stub.speak.assert_not_called()


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


def test_seasonal_modifiers_neutral_on_ordinary_day():
    mods = seasonal_modifiers(date(2026, 7, 28))
    assert mods["glitch_mult"] == 1.0
    assert mods["creepy_nudge_chance"] == 0.5
    assert mods["kinito_fact_weight"] is None
    assert mods["poem_themes"] == ()


def test_seasonal_modifiers_halloween_boosts_spooky():
    mods = seasonal_modifiers(date(2026, 10, 31))
    assert mods["glitch_mult"] > 1.5
    assert mods["creepy_nudge_chance"] > 0.6
    assert isinstance(mods["kinito_fact_weight"], float)
    assert mods["kinito_fact_weight"] > 0.4
    assert "spooky" in mods["poem_themes"]


def test_seasonal_modifiers_spooky_week_before_halloween():
    mods = seasonal_modifiers(date(2026, 10, 27))
    assert mods["glitch_mult"] > 1.0
    assert mods["creepy_nudge_chance"] > 0.5


def test_seasonal_modifiers_christmas_prefers_wellness_and_poems():
    mods = seasonal_modifiers(date(2026, 12, 25))
    assert mods["poem"] > 1.5
    assert mods["creepy_nudge_chance"] < 0.3
    assert mods["nudge_mult"] > 1.0
    assert "christmas" in mods["poem_themes"] or "winter" in mods["poem_themes"]


def test_seasonal_modifiers_valentines_boosts_compliments():
    mods = seasonal_modifiers(date(2026, 2, 14))
    assert mods["compliment"] > 2.0
    assert mods["poem"] > 1.5
    assert mods["creepy_nudge_chance"] < 0.3
    assert "valentine" in mods["poem_themes"]


def test_seasonal_multiplier_clamps_missing_key():
    assert seasonal_multiplier("glitch_mult", date(2026, 7, 28)) == 1.0
    assert seasonal_multiplier("poem_themes", date(2026, 10, 31), default=1.0) == 1.0


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


def test_seasonal_modifiers_disabled_via_content_helper():
    from kinito.features.content import ContentMixin

    class Stub(ContentMixin):
        pass

    stub = Stub()
    stub._special_days_enabled = False
    assert stub._seasonal_modifiers_if_enabled() == {}


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


def test_past_special_days_finds_recent_holiday():
    from content.special_days import past_special_days

    past = past_special_days(date(2026, 11, 2), lookback_days=7)
    names = [day.name for day, _ in past]
    assert "Halloween" in names
    for _, ago in past:
        assert 1 <= ago <= 7
    assert not past_special_days(date(2026, 10, 30), lookback_days=1)


def _missed_stub(missed, enabled=True):
    from kinito.features.content import ContentMixin

    class Stub(ContentMixin):
        pass

    stub = Stub()
    stub._special_days_enabled = enabled
    stub._can_initiate_spontaneous_speech = MagicMock(return_value=True)
    stub.speak = MagicMock()
    stub._memory = MagicMock()
    stub._memory.is_topic_on_cooldown.return_value = False
    stub._missed_special_days = missed
    return stub


def test_maybe_ask_missed_special_day_asks_about_missed_day():
    from content import dialogue as dlg

    stub = _missed_stub([("Halloween", "2026-10-31")])
    assert stub.maybe_ask_missed_special_day() is True
    line = stub.speak.call_args[0][0]
    assert "Halloween" in line
    assert line in [
        t.format(name="Halloween")
        for t in dlg.MISSED_DAY_LINES + sum(dlg.MISSED_DAY_BY_MOOD.values(), [])
    ]
    stub._memory.mark_topic_asked.assert_called_once_with(
        "missed_special_day:2026-10-31"
    )


def test_maybe_ask_missed_special_day_skips_cooldown_and_disabled():
    stub = _missed_stub([("Halloween", "2026-10-31")])
    stub._memory.is_topic_on_cooldown.return_value = True
    assert stub.maybe_ask_missed_special_day() is False
    stub = _missed_stub([("Halloween", "2026-10-31")], enabled=False)
    assert stub.maybe_ask_missed_special_day() is False
    stub = _missed_stub([])
    assert stub.maybe_ask_missed_special_day() is False


def test_missed_day_line_pools_are_formattable_and_cover_moods():
    from content import dialogue as dlg

    assert len(dlg.MISSED_DAY_LINES) >= 5
    for mood, lines in dlg.MISSED_DAY_BY_MOOD.items():
        assert len(lines) >= 2, mood
        assert len(set(lines)) == len(lines), mood
    for line in dlg.MISSED_DAY_LINES + sum(dlg.MISSED_DAY_BY_MOOD.values(), []):
        assert "{name}" in line
        line.format(name="Halloween")
