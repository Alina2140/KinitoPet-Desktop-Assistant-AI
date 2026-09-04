"""Dated storage helpers for day-scoped memory facts (mood/energy/focus/plans)."""

from __future__ import annotations

from datetime import date

# On-disk form: "YYYY-MM-DD|<value>" so free-text plans may contain "|".
_DAILY_FACT_SEP = "|"
_ISO_DATE_LEN = 10


def format_daily_fact(value: str, *, today: date | None = None) -> str:
    """Serialize a daily fact with an ISO date prefix."""
    day = (today or date.today()).isoformat()
    return f"{day}{_DAILY_FACT_SEP}{value}"


def parse_daily_fact(raw: str | None) -> tuple[str, date] | None:
    """Parse ``YYYY-MM-DD|value``; return (value, day) or None if undated/invalid."""
    if not raw or not isinstance(raw, str):
        return None
    trimmed = raw.strip()
    if len(trimmed) <= _ISO_DATE_LEN or trimmed[_ISO_DATE_LEN] != _DAILY_FACT_SEP:
        return None
    date_part = trimmed[:_ISO_DATE_LEN]
    value = trimmed[_ISO_DATE_LEN + 1 :].strip()
    if not value:
        return None
    try:
        stamped = date.fromisoformat(date_part)
    except ValueError:
        return None
    return value, stamped


def is_fresh_daily_fact(raw: str | None, *, today: date | None = None) -> bool:
    """Return True when *raw* is a daily fact stamped for *today*."""
    parsed = parse_daily_fact(raw)
    if parsed is None:
        return False
    _value, stamped = parsed
    return stamped == (today or date.today())
