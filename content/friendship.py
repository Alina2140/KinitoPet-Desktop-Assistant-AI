"""Friendship / first-met date helpers for relationship milestones."""

from __future__ import annotations

import calendar
import random
import re
from datetime import date, datetime

_ISO_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")


def parse_first_met(stored: str | None) -> date | None:
    """Parse a stored ``YYYY-MM-DD`` first-met date."""
    if not stored or not isinstance(stored, str):
        return None
    match = _ISO_RE.match(stored.strip())
    if not match:
        return None
    year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
    try:
        return date(year, month, day)
    except ValueError:
        return None


def ensure_first_met(memory, *, today: date | None = None) -> str | None:
    """Store today's date as ``first_met`` once; return the stored value."""
    existing = memory.get_fact("first_met")
    if parse_first_met(existing) is not None:
        return existing
    moment = today or date.today()
    value = moment.isoformat()
    memory.set_fact("first_met", value)
    return memory.get_fact("first_met")


def days_together(stored: str | None, today: date | datetime | None = None) -> int | None:
    """Return whole days since first meet, or None if unknown."""
    start = parse_first_met(stored)
    if start is None:
        return None
    moment = date.today() if today is None else (today.date() if isinstance(today, datetime) else today)
    delta = (moment - start).days
    return delta if delta >= 0 else None


def format_friendship_duration(
    stored: str | None,
    today: date | datetime | None = None,
) -> str | None:
    """Human duration since first meet, e.g. ``3 weeks`` or ``1 year and 2 months``."""
    days = days_together(stored, today=today)
    if days is None:
        return None
    if days == 0:
        return "today"
    if days == 1:
        return "1 day"
    if days < 14:
        return f"{days} days"
    if days < 60:
        weeks = days // 7
        return "1 week" if weeks == 1 else f"{weeks} weeks"
    if days < 365:
        months = max(1, days // 30)
        return "1 month" if months == 1 else f"{months} months"
    years = days // 365
    rem_months = (days % 365) // 30
    year_part = "1 year" if years == 1 else f"{years} years"
    if rem_months <= 0:
        return year_part
    month_part = "1 month" if rem_months == 1 else f"{rem_months} months"
    return f"{year_part} and {month_part}"


def friendship_years(stored: str | None, today: date | datetime | None = None) -> int | None:
    """Completed anniversary years since first meet."""
    start = parse_first_met(stored)
    if start is None:
        return None
    moment = date.today() if today is None else (today.date() if isinstance(today, datetime) else today)
    years = moment.year - start.year
    if (moment.month, moment.day) < (start.month, start.day):
        years -= 1
    return years if years >= 0 else None


def is_met_anniversary_today(
    stored: str | None,
    today: date | datetime | None = None,
) -> bool:
    """Return True on the month/day anniversary when at least one year has passed."""
    start = parse_first_met(stored)
    if start is None:
        return False
    moment = date.today() if today is None else (today.date() if isinstance(today, datetime) else today)
    years = friendship_years(stored, today=moment)
    if years is None or years < 1:
        return False
    month, day = start.month, start.day
    if month == 2 and day == 29 and not calendar.isleap(moment.year):
        return moment.month == 2 and moment.day == 28
    return moment.month == month and moment.day == day


def pick_friendship_duration_line(
    lines: list[str] | tuple[str, ...],
    *,
    duration: str,
    name: str | None = None,
) -> str:
    """Format a duration reminder line."""
    display_name = (name or "friend").strip() or "friend"
    pool = [line for line in lines if "{name}" in line] if name else list(lines)
    if not pool:
        pool = list(lines)
    template = random.choice(pool)
    try:
        return template.format(name=display_name, duration=duration)
    except (KeyError, IndexError, ValueError):
        return template.replace("{name}", display_name).replace("{duration}", duration)


def pick_met_anniversary_line(
    lines: list[str] | tuple[str, ...],
    *,
    years: int,
    name: str | None = None,
    duration: str | None = None,
) -> str:
    """Format a meeting-anniversary line."""
    display_name = (name or "friend").strip() or "friend"
    duration_text = duration or ("1 year" if years == 1 else f"{years} years")
    pool = list(lines)
    template = random.choice(pool)
    try:
        return template.format(name=display_name, years=years, duration=duration_text)
    except (KeyError, IndexError, ValueError):
        return (
            template.replace("{name}", display_name)
            .replace("{years}", str(years))
            .replace("{duration}", duration_text)
        )
