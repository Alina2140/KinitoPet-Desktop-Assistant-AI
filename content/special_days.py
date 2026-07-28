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
            "Happy {name}! Return gifts, sweet gestures, soft loyalty.",
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
            "Happy {name}! For the rest of us. Air grievances softly. Then stay.",
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
