"""Book quotes and wisdom lines for idle reading — loaded from quotes.json."""

import json
import os
import random

_INTROS = [
    "I was reading today:",
    "From an old book:",
    "Here's something wise I found:",
    "A philosopher once wrote:",
    "I read this in a dusty novel:",
    "From my favorite page:",
    "A wise author said:",
    "Something I underlined:",
    "From a short story:",
    "I found this quote today:",
    "A poet wrote:",
    "From an old fable:",
    "A thinker once said:",
    "I read:",
    "From a worn paperback:",
    "A line that stuck with me:",
    "From a children's book, surprisingly deep:",
    "I was reading about friendship:",
    "A quiet passage:",
    "From a mystery novel:",
    "Something philosophical:",
    "A gentle reminder from a self-help book:",
    "From an ancient proverb:",
    "A bookmarked line:",
    "From a nature journal:",
    "A thoughtful note:",
    "From a letter I found:",
    "Something to ponder:",
    "A line I keep coming back to:",
    "From a horror novel I probably shouldn't have read:",
    "Something unsettling:",
    "A quiet line from a ghost story:",
    "From the margins of a diary:",
    "A proverb from somewhere dark:",
]


def _quotes_path():
    return os.path.join(os.path.dirname(__file__), "quotes.json")


def load_quotes():
    """Load quote records from quotes.json."""
    with open(_quotes_path(), encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list) or not data:
        raise ValueError("quotes.json must contain a non-empty list")
    for entry in data:
        if not isinstance(entry.get("quote"), str) or not entry["quote"].strip():
            raise ValueError("each quote entry needs non-empty 'quote' text")
    return data


QUOTES = load_quotes()


def format_wisdom_line(entry, intro=None):
    """Turn a quote record into a Kinito-style spoken line."""
    if intro is None:
        intro = random.choice(_INTROS)
    text = entry["quote"].strip()
    author = entry.get("author")
    if author:
        text = f"{text} — {author}"
    return f"{intro} {text}"


WISDOM = [
    format_wisdom_line(entry, _INTROS[index % len(_INTROS)]) for index, entry in enumerate(QUOTES)
]


def get_random_wisdom():
    """Return a random wisdom line with a fresh intro."""
    return format_wisdom_line(random.choice(QUOTES))
