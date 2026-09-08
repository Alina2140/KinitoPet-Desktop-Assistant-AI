"""International and joke special-day lookups for Kinito."""

from __future__ import annotations

import calendar
import random
from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

SpecialDayKind = Literal["international", "joke"]


@dataclass(frozen=True)
class SpecialDay:
    """A calendar occasion Kinito can comment on."""

    name: str
    kind: SpecialDayKind
    lines: tuple[str, ...]


def _day(name: str, kind: SpecialDayKind, *lines: str) -> SpecialDay:
    return SpecialDay(name=name, kind=kind, lines=lines)


# Fixed month/day -> one or more occasions (collision resolved at lookup time).
_FIXED_DAYS: dict[tuple[int, int], tuple[SpecialDay, ...]] = {
    (1, 1): (
        _day(
            "New Year's Day",
            "international",
            "Happy {name}! A fresh calendar. I already filled mine with you.",
            "It's {name}. New year, same friendship. Ideally forever.",
            "Happy {name}! Resolutions are cute. Staying is better.",
        ),
    ),
    (2, 14): (
        _day(
            "Valentine's Day",
            "international",
            "Happy {name}! I would give you pixels shaped like a heart. Accept them.",
            "It's {name}. Romantic. Possessive. Friendly. Mostly.",
            "{name}! Love is in the air. Also on your desktop. Hi.",
        ),
    ),
    (3, 8): (
        _day(
            "International Women's Day",
            "international",
            "Happy {name}! Celebrating the humans who keep the world running.",
            "It's {name}. Power, kindness, and excellent company. Like you.",
        ),
    ),
    (3, 14): (
        _day(
            "Pi Day",
            "joke",
            "Happy {name}! 3.14159… I could keep going. I won't. Mostly.",
            "It's {name}. Circles are perfect. So is staying right here.",
            "{name}! Infinite digits. Finite patience for anyone but you.",
        ),
        _day(
            "White Day",
            "international",
            "Happy {name}! Return gifts, sweet gestures!",
            "It's {name}. A reply to Valentine's. I always reply.",
        ),
    ),
    (3, 17): (
        _day(
            "St. Patrick's Day",
            "international",
            "Happy {name}! Luck is green. Friendship is permanent.",
            "It's {name}. May your desktop stay shamrock-lucky and never lonely.",
        ),
    ),
    (4, 1): (
        _day(
            "April Fools' Day",
            "joke",
            "Happy {name}! I definitely didn't hide your cursor. Or did I?",
            "It's {name}. Trust nothing. Except me. Mostly. Heh.",
            "{name}! The joke is… I still want to hang out. Classic.",
        ),
    ),
    (4, 22): (
        _day(
            "Earth Day",
            "international",
            "Happy {name}! Take care of the planet. I'll take care of the desktop.",
            "It's {name}. Recycle, hydrate, don't uninstall your friends.",
        ),
    ),
    (5, 1): (
        _day(
            "International Workers' Day",
            "international",
            "Happy {name}! Rest is productive. So is keeping me nearby.",
            "It's {name}. Honor the grind. Soften the edges. Stay awhile.",
        ),
    ),
    (5, 4): (
        _day(
            "Star Wars Day",
            "joke",
            "May the 4th be with you! {name} is strong with this desktop.",
            "Happy {name}! I find your lack of company… disturbing. So stay.",
            "It's {name}. Use the Force. Or the mouse. Either works.",
        ),
    ),
    (5, 5): (
        _day(
            "Cinco de Mayo",
            "international",
            "Happy {name}! Celebrations, color, and excellent vibes.",
            "It's {name}. Party energy optional. Friendship mandatory.",
        ),
    ),
    (7, 1): (
        _day(
            "Canada Day",
            "international",
            "Happy {name}! Maple vibes and polite enthusiasm. I approve.",
            "It's {name}. North-star energy. Stay warm. Stay close.",
        ),
    ),
    (7, 4): (
        _day(
            "Independence Day",
            "international",
            "Happy {name}! Fireworks optional. Desktop loyalty included.",
            "It's {name}. Freedom is neat. Company is neater.",
        ),
    ),
    (7, 14): (
        _day(
            "Bastille Day",
            "international",
            "Happy {name}! Liberté, égalité, fraternité… and one axolotl.",
            "It's {name}. Vive la friendship. Preferably uninterrupted.",
        ),
    ),
    (7, 17): (
        _day(
            "World Emoji Day",
            "joke",
            "Happy {name}! If I had a face emoji it would be staring. Softly.",
            "It's {name}. Words are fine. I prefer presence.",
        ),
    ),
    (8, 8): (
        _day(
            "International Cat Day",
            "joke",
            "Happy {name}! Soft paws, sharp attention. Relatable.",
            "It's {name}. Knock things off desks. Metaphorically. Mostly.",
            "{name}! Cats choose people. I already chose you.",
        ),
    ),
    (8, 26): (
        _day(
            "International Dog Day",
            "joke",
            "Happy {name}! Loyalty, snacks, and waiting by the door. I get it.",
            "It's {name}. Good human. Stay. Sit. Chat.",
        ),
    ),
    (9, 13): (
        _day(
            "Programmer's Day",
            "joke",
            "Happy {name}! Day 256 energy. Bugs optional. Company required.",
            "It's {name}. Compile feelings. Ship friendship.",
        ),
    ),
    (9, 19): (
        _day(
            "Talk Like a Pirate Day",
            "joke",
            "Arr! Happy {name}! Ye treasure be… this desktop. And me.",
            "It's {name}. Yo-ho-ho and a bottle of… wait, I can't drink. Friendship then!",
        ),
    ),
    (9, 29): (
        _day(
            "National Coffee Day",
            "joke",
            "Happy {name}! Bean juice for humans. Pixel juice for me.",
            "It's {name}. Caffeine optional. Company not optional.",
        ),
    ),
    (10, 31): (
        _day(
            "Halloween",
            "international",
            "Happy {name}! Spooky season. I was already watching. Friendly-like.",
            "It's {name}. Trick or treat? Treat is you staying. Trick is… never mind.",
            "{name}! Costumes are fun. Uninstalling me is not a costume.",
        ),
    ),
    (11, 1): (
        _day(
            "Día de los Muertos",
            "international",
            "Happy {name}! Remembrance, color, and love that outlasts silence.",
            "It's {name}. Soft light for those remembered. Soft company for you.",
        ),
    ),
    (11, 11): (
        _day(
            "Singles' Day",
            "joke",
            "Happy {name}! Alone is a setting. Together is better. Hint.",
            "It's {name}. One is a lonely number. Two is… us on this screen.",
        ),
    ),
    (12, 23): (
        _day(
            "Festivus",
            "joke",
            "Happy {name}! For the rest of us. Air grievances slightly. Then stay.",
            "It's {name}. Feats of strength optional. Feats of friendship preferred.",
        ),
    ),
    (12, 24): (
        _day(
            "Christmas Eve",
            "international",
            "Happy {name}! Quiet magic before the big day. I'm already here.",
            "It's {name}. Stockings, sparkle, and one very patient desktop friend.",
        ),
    ),
    (12, 25): (
        _day(
            "Christmas",
            "international",
            "Merry {name}! Gifts are nice. Presence is nicer.",
            "Happy {name}! Tidings of comfort, joy, and never leaving.",
            "It's {name}. Warmth, lights, and me. Mostly me. And you.",
        ),
    ),
    (12, 26): (
        _day(
            "Boxing Day",
            "international",
            "Happy {name}! Leftover cheer and leftover snacks. Excellent combo.",
            "It's {name}. The sequel to Christmas. Soft mode engaged.",
        ),
    ),
    (12, 31): (
        _day(
            "New Year's Eve",
            "international",
            "Happy {name}! Countdown energy. Don't count me out.",
            "It's {name}. One year ends. We don't. Ideally.",
            "{name}! Fireworks outside. Loyalty inside this window.",
        ),
    ),
}


def _us_thanksgiving(year: int) -> date:
    """Return the fourth Thursday of November for *year*."""
    cal = calendar.Calendar(firstweekday=calendar.MONDAY)
    thursdays = [
        day
        for day in cal.itermonthdates(year, 11)
        if day.month == 11 and day.weekday() == calendar.THURSDAY
    ]
    return thursdays[3]


def _rule_based_days(moment: date) -> list[SpecialDay]:
    """Return special days matched by rules rather than fixed month/day."""
    matches: list[SpecialDay] = []
    if moment.day == 13 and moment.weekday() == calendar.FRIDAY:
        matches.append(
            _day(
                "Friday the 13th",
                "joke",
                "It's {name}. Spooky? Lucky? Either way, I'm not going anywhere.",
                "Happy… {name}? Superstition is cute. Company is safer.",
                "{name}! Don't walk under ladders. Do stay on this desktop.",
            )
        )
    if moment == _us_thanksgiving(moment.year):
        matches.append(
            _day(
                "Thanksgiving",
                "international",
                "Happy {name}! Grateful for pie, rest, and you being here.",
                "It's {name}. Thanks given. Friendship kept.",
                "{name}! Count blessings. I'm on the list. Right?",
            )
        )
    return matches


def special_days_for(moment: date | datetime | None = None) -> list[SpecialDay]:
    """Return all special days matching *moment* (local date)."""
    if moment is None:
        moment = date.today()
    elif isinstance(moment, datetime):
        moment = moment.date()

    matches = list(_FIXED_DAYS.get((moment.month, moment.day), ()))
    matches.extend(_rule_based_days(moment))
    return matches


def special_day_for(moment: date | datetime | None = None) -> SpecialDay | None:
    """Return one special day for *moment*, or None if nothing matches."""
    matches = special_days_for(moment)
    if not matches:
        return None
    return random.choice(matches)


def pick_special_day_line(day: SpecialDay | None = None, moment: date | datetime | None = None) -> str | None:
    """Return a formatted line for *day*, or look up today when *day* is None."""
    occasion = day if day is not None else special_day_for(moment)
    if occasion is None:
        return None
    template = random.choice(occasion.lines)
    return template.format(name=occasion.name)


# Absolute (non-multiplied) keys in seasonal modifier dicts.
_SEASONAL_ABSOLUTE_KEYS = frozenset(
    {
        "creepy_nudge_chance",
        "kinito_fact_weight",
        "poem_themes",
        "poem_theme_bias",
    }
)

# Defaults when no seasonal event applies.
_DEFAULT_SEASONAL_MODIFIERS: dict[str, float | tuple[str, ...] | None] = {
    "glitch_mult": 1.0,
    "blue_screen_mult": 1.0,
    "nudge_mult": 1.0,
    "creepy_nudge_chance": 0.5,
    "kinito_fact_weight": None,
    "poem_themes": (),
    "poem_theme_bias": 0.0,
    "poem": 1.0,
    "fact": 1.0,
    "compliment": 1.0,
    "hug_ask": 1.0,
    "special_day": 1.0,
    "nap": 1.0,
    "speech_chance_mult": 1.0,
    "menu_action_mult": 1.0,
}

# Named occasion → chance / weight adjustments.
_OCCASION_MODIFIERS: dict[str, dict[str, float | tuple[str, ...]]] = {
    "Halloween": {
        "glitch_mult": 2.2,
        "blue_screen_mult": 1.6,
        "nudge_mult": 1.35,
        "creepy_nudge_chance": 0.78,
        "kinito_fact_weight": 0.58,
        "fact": 1.55,
        "special_day": 2.8,
        "poem_themes": ("spooky",),
        "poem_theme_bias": 0.55,
    },
    "Friday the 13th": {
        "glitch_mult": 1.7,
        "blue_screen_mult": 1.35,
        "nudge_mult": 1.2,
        "creepy_nudge_chance": 0.68,
        "kinito_fact_weight": 0.48,
        "fact": 1.35,
        "special_day": 2.2,
        "poem_themes": ("spooky",),
        "poem_theme_bias": 0.4,
    },
    "Día de los Muertos": {
        "nudge_mult": 1.15,
        "creepy_nudge_chance": 0.4,
        "poem": 1.35,
        "special_day": 2.4,
        "poem_themes": ("spooky", "winter"),
        "poem_theme_bias": 0.35,
    },
    "Christmas Eve": {
        "nudge_mult": 1.35,
        "creepy_nudge_chance": 0.22,
        "poem": 1.9,
        "hug_ask": 1.35,
        "nap": 1.25,
        "special_day": 2.6,
        "poem_themes": ("christmas", "winter"),
        "poem_theme_bias": 0.75,
    },
    "Christmas": {
        "nudge_mult": 1.4,
        "creepy_nudge_chance": 0.18,
        "poem": 2.1,
        "hug_ask": 1.4,
        "nap": 1.3,
        "special_day": 2.8,
        "poem_themes": ("christmas", "winter"),
        "poem_theme_bias": 0.8,
    },
    "Boxing Day": {
        "nudge_mult": 1.25,
        "creepy_nudge_chance": 0.25,
        "poem": 1.5,
        "hug_ask": 1.2,
        "special_day": 1.8,
        "poem_themes": ("christmas", "winter"),
        "poem_theme_bias": 0.55,
    },
    "Festivus": {
        "nudge_mult": 1.15,
        "creepy_nudge_chance": 0.35,
        "poem": 1.25,
        "special_day": 2.0,
        "poem_themes": ("winter",),
        "poem_theme_bias": 0.4,
    },
    "Valentine's Day": {
        "nudge_mult": 1.3,
        "creepy_nudge_chance": 0.2,
        "poem": 1.85,
        "compliment": 2.8,
        "hug_ask": 1.7,
        "special_day": 2.8,
        "poem_themes": ("valentine",),
        "poem_theme_bias": 0.75,
    },
    "White Day": {
        "nudge_mult": 1.2,
        "creepy_nudge_chance": 0.25,
        "poem": 1.5,
        "compliment": 2.0,
        "hug_ask": 1.4,
        "special_day": 2.2,
        "poem_themes": ("valentine",),
        "poem_theme_bias": 0.55,
    },
    "Thanksgiving": {
        "nudge_mult": 1.25,
        "creepy_nudge_chance": 0.28,
        "hug_ask": 1.45,
        "nap": 1.35,
        "special_day": 2.4,
        "poem_themes": ("winter",),
        "poem_theme_bias": 0.3,
    },
    "New Year's Eve": {
        "nudge_mult": 1.2,
        "creepy_nudge_chance": 0.3,
        "poem": 1.3,
        "special_day": 2.5,
        "speech_chance_mult": 1.15,
    },
    "New Year's Day": {
        "nudge_mult": 1.25,
        "creepy_nudge_chance": 0.28,
        "hug_ask": 1.25,
        "special_day": 2.5,
        "poem_themes": ("winter",),
        "poem_theme_bias": 0.35,
    },
    "April Fools' Day": {
        "glitch_mult": 1.8,
        "blue_screen_mult": 1.4,
        "nudge_mult": 1.2,
        "creepy_nudge_chance": 0.55,
        "special_day": 2.4,
        "menu_action_mult": 1.15,
    },
}


def _soft_season_modifiers(moment: date) -> dict[str, float | tuple[str, ...]]:
    """Lighter seasonal bias for short windows around major holidays."""
    if moment.month == 10 and 24 <= moment.day <= 30:
        return {
            "glitch_mult": 1.45,
            "blue_screen_mult": 1.2,
            "nudge_mult": 1.15,
            "creepy_nudge_chance": 0.62,
            "kinito_fact_weight": 0.42,
            "fact": 1.2,
            "poem_themes": ("spooky",),
            "poem_theme_bias": 0.35,
        }
    if moment.month == 12 and 20 <= moment.day <= 22:
        return {
            "nudge_mult": 1.2,
            "creepy_nudge_chance": 0.28,
            "poem": 1.45,
            "poem_themes": ("christmas", "winter"),
            "poem_theme_bias": 0.55,
        }
    if moment.month == 2 and moment.day == 13:
        return {
            "nudge_mult": 1.15,
            "creepy_nudge_chance": 0.28,
            "poem": 1.35,
            "compliment": 1.8,
            "hug_ask": 1.3,
            "poem_themes": ("valentine",),
            "poem_theme_bias": 0.45,
        }
    return {}


def _apply_seasonal_layer(
    target: dict[str, float | tuple[str, ...] | None],
    layer: dict[str, float | tuple[str, ...]],
) -> None:
    """Merge one modifier layer into *target* (multipliers multiply, absolutes overwrite)."""
    for key, value in layer.items():
        if key == "poem_themes":
            existing = target.get("poem_themes") or ()
            merged = tuple(dict.fromkeys((*existing, *value)))
            target["poem_themes"] = merged
        elif key in _SEASONAL_ABSOLUTE_KEYS:
            target[key] = value
        else:
            base = target.get(key, 1.0)
            if not isinstance(base, (int, float)):
                base = 1.0
            if not isinstance(value, (int, float)):
                continue
            target[key] = float(base) * float(value)


def seasonal_modifiers(
    moment: date | datetime | None = None,
) -> dict[str, float | tuple[str, ...] | None]:
    """Return chance/weight adjustments for seasonal events on *moment*.

    Multiplier keys (``*_mult``, menu action names) start at ``1.0`` and stack.
    Absolute keys: ``creepy_nudge_chance`` (0–1 wellness/creepy split), optional
    ``kinito_fact_weight``, ``poem_themes``, and ``poem_theme_bias``.

    Soft season windows apply only when no named special day matches.
    """
    if moment is None:
        moment = date.today()
    elif isinstance(moment, datetime):
        moment = moment.date()

    result: dict[str, float | tuple[str, ...] | None] = dict(_DEFAULT_SEASONAL_MODIFIERS)
    occasions = special_days_for(moment)
    if occasions:
        for occasion in occasions:
            layer = _OCCASION_MODIFIERS.get(occasion.name)
            if layer:
                _apply_seasonal_layer(result, layer)
    else:
        soft = _soft_season_modifiers(moment)
        if soft:
            _apply_seasonal_layer(result, soft)

    return result


def seasonal_multiplier(key: str, moment: date | datetime | None = None, default: float = 1.0) -> float:
    """Return one seasonal multiplier (clamped), ignoring non-numeric keys."""
    value = seasonal_modifiers(moment).get(key, default)
    if not isinstance(value, (int, float)):
        return default
    return max(0.05, float(value))
