"""Parse and match the user's birthday for congratulations."""

from __future__ import annotations

import calendar
import random
import re
from datetime import date, datetime

# Stored when the user declines to share a birthday.
BIRTHDAY_DECLINED = "declined"

_MONTH_NAMES = {
    name.lower(): index
    for index, name in enumerate(calendar.month_name)
    if name
}
_MONTH_ABBREVS = {
    name.lower(): index
    for index, name in enumerate(calendar.month_abbr)
    if name
}
_MONTH_LABELS = {
    index: name for index, name in enumerate(calendar.month_name) if name
}

_ISO_RE = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})$")
_MD_RE = re.compile(r"^(\d{1,2})[-/](\d{1,2})$")
_MDY_RE = re.compile(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})$")
_DM_DOT_RE = re.compile(r"^(\d{1,2})\.(\d{1,2})(?:\.(\d{2,4}))?$")
_NAMED_RE = re.compile(
    r"^([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?(?:\s*,?\s*(\d{2,4}))?$"
    r"|^(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)(?:\s*,?\s*(\d{2,4}))?$",
    re.IGNORECASE,
)


def _normalize_year(year: int, *, today: date | None = None) -> int | None:
    """Return a plausible 4-digit birth year, or None if out of range."""
    moment = today or date.today()
    if year < 100:
        century = (moment.year // 100) * 100
        year = century + year
        if year > moment.year:
            year -= 100
    if year < 1900 or year > moment.year:
        return None
    return year


def _valid_month_day(month: int, day: int) -> bool:
    if month < 1 or month > 12 or day < 1 or day > 31:
        return False
    # Allow Feb 29 as a stored birthday even in non-leap years.
    if month == 2 and day == 29:
        return True
    try:
        date(2024 if month == 2 and day == 29 else 2023, month, day)
    except ValueError:
        return False
    return True


def _format_stored(month: int, day: int, year: int | None = None) -> str | None:
    if not _valid_month_day(month, day):
        return None
    if year is None:
        return f"{month:02d}-{day:02d}"
    return f"{year:04d}-{month:02d}-{day:02d}"


def parse_birthday(text: str, *, today: date | None = None) -> str | None:
    """Parse free text into ``YYYY-MM-DD`` or ``MM-DD``, or None if invalid."""
    trimmed = text.strip()
    if not trimmed:
        return None
    moment = today or date.today()

    match = _ISO_RE.match(trimmed)
    if match:
        year = _normalize_year(int(match.group(1)), today=moment)
        month, day = int(match.group(2)), int(match.group(3))
        if year is None:
            return None
        return _format_stored(month, day, year)

    # Already-normalized month-day without year.
    match = _MD_RE.match(trimmed)
    if match:
        first, second = int(match.group(1)), int(match.group(2))
        if _valid_month_day(first, second):
            return _format_stored(first, second)
        if _valid_month_day(second, first):
            return _format_stored(second, first)
        return None

    match = _MDY_RE.match(trimmed)
    if match:
        first, second, year_raw = int(match.group(1)), int(match.group(2)), int(match.group(3))
        year = _normalize_year(year_raw, today=moment)
        if year is None:
            return None
        if _valid_month_day(first, second):
            return _format_stored(first, second, year)
        if _valid_month_day(second, first):
            return _format_stored(second, first, year)
        return None

    match = _DM_DOT_RE.match(trimmed)
    if match:
        day, month = int(match.group(1)), int(match.group(2))
        year = None
        if match.group(3):
            year = _normalize_year(int(match.group(3)), today=moment)
            if year is None:
                return None
        return _format_stored(month, day, year)

    match = _NAMED_RE.match(trimmed)
    if match:
        if match.group(1) and match.group(2):
            month_token, day = match.group(1).lower(), int(match.group(2))
            year_raw = match.group(3)
        else:
            day, month_token = int(match.group(4)), match.group(5).lower()
            year_raw = match.group(6)
        month = _MONTH_NAMES.get(month_token) or _MONTH_ABBREVS.get(month_token)
        if month is None:
            return None
        year = None
        if year_raw:
            year = _normalize_year(int(year_raw), today=moment)
            if year is None:
                return None
        return _format_stored(month, day, year)

    return None


def birthday_month_day(stored: str | None) -> tuple[int, int] | None:
    """Return ``(month, day)`` from a stored birthday value, or None."""
    if not stored:
        return None
    value = stored.strip().casefold()
    if value in {BIRTHDAY_DECLINED, "no", "private", "none"}:
        return None

    stripped = stored.strip()
    match = _ISO_RE.match(stripped)
    if match:
        month, day = int(match.group(2)), int(match.group(3))
        return (month, day) if _valid_month_day(month, day) else None

    match = _MD_RE.match(stripped)
    if match:
        month, day = int(match.group(1)), int(match.group(2))
        return (month, day) if _valid_month_day(month, day) else None

    parsed = parse_birthday(stored)
    if not parsed:
        return None
    return birthday_month_day(parsed)


def birthday_year(stored: str | None) -> int | None:
    """Return the birth year from a stored value, or None if unknown."""
    if not stored:
        return None
    match = _ISO_RE.match(stored.strip())
    if not match:
        return None
    return _normalize_year(int(match.group(1)))


def birthday_age(stored: str | None, today: date | datetime | None = None) -> int | None:
    """Return age in years when a birth year is stored, else None."""
    year = birthday_year(stored)
    parts = birthday_month_day(stored)
    if year is None or parts is None:
        return None
    moment = date.today() if today is None else (today.date() if isinstance(today, datetime) else today)
    month, day = parts
    age = moment.year - year
    if (moment.month, moment.day) < (month, day):
        age -= 1
    return age if age >= 0 else None


def format_birthday_display(stored: str | None) -> str | None:
    """Human-readable birthday, e.g. ``March 15, 1990`` or ``March 15``."""
    parts = birthday_month_day(stored)
    if parts is None:
        return None
    month, day = parts
    label = f"{_MONTH_LABELS[month]} {day}"
    year = birthday_year(stored)
    if year is not None:
        return f"{label}, {year}"
    return label


def is_birthday_today(stored: str | None, today: date | datetime | None = None) -> bool:
    """Return True when *stored* birthday falls on *today*."""
    parts = birthday_month_day(stored)
    if parts is None:
        return False
    moment = date.today() if today is None else (today.date() if isinstance(today, datetime) else today)
    month, day = parts
    if month == 2 and day == 29 and not calendar.isleap(moment.year):
        # Celebrate leap-day birthdays on Feb 28 in non-leap years.
        return moment.month == 2 and moment.day == 28
    return moment.month == month and moment.day == day


def pick_birthday_congrats_line(
    lines: list[str] | tuple[str, ...],
    *,
    name: str | None = None,
    age: int | None = None,
) -> str:
    """Pick and format a birthday congratulations line."""
    pool = tuple(lines)
    if age is not None:
        with_age = tuple(line for line in pool if "{age}" in line)
        if with_age:
            pool = with_age
    else:
        without_age = tuple(line for line in pool if "{age}" not in line)
        if without_age:
            pool = without_age
    template = random.choice(pool)
    return template.format(name=name or "friend", age=age if age is not None else "")
