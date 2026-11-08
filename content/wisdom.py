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
    "Quiet bookmark from earlier:",
    "A line that refused to leave me:",
    "From a page I shouldn't reread:",
    "Something whispered from the margins:",
    "I underlined this twice:",
    "From a story that watched back:",
    "Found between chapters:",
    "From a dog-eared classic:",
    "I borrowed this from a wise page:",
    "A line that felt like company:",
    "From a midnight reread:",
    "Something the footnotes whispered:",
    "From a novel that wouldn't close:",
    "I kept this sentence like a key:",
    "From a letter pressed in a book:",
    "A thought that outlived its chapter:",
    "From the kind of story that stays:",
    "Something durable I underlined:",
    "A quiet truth between the plots:",
    "I carried this line across tabs:",
]

_EMPTY_WISDOM_FALLBACK = (
    "I wanted to share a quote, but my book seems to be missing its pages."
)


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


def _safe_load_quotes():
    """Load quotes, or return an empty pool if the file is missing/invalid."""
    try:
        return load_quotes()
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(f"Warning: could not load quotes.json ({exc}); wisdom pool empty.", flush=True)
        return []


QUOTES = _safe_load_quotes()


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


_INTRO_BY_MOOD: dict[str, list[str]] = {
    "happy": [
        "A quote that made me beam:",
        "Something joyful I underlined twice:",
    ],
    "bored": [
        "Reading out of sheer boredom:",
        "A line from a book I found while bored:",
    ],
    "tired": [
        "A drowsy little quote...:",
        "From a bedtime page...:",
    ],
    "annoyed": [
        "A quote. Read it. It's probably smarter than my mood:",
        "Something I read instead of sulking:",
    ],
    "sad": [
        "A quote that felt like a hug...:",
        "Something quiet that stayed with me...:",
    ],
    "angry": [
        "A quote. NO, it's good! Read it!",
        "Wisdom! Agree with it or else!",
    ],
}


def get_random_wisdom(mood=None, intensity=0.0):
    """Return a random wisdom line with a fresh intro."""
    if not QUOTES:
        return _EMPTY_WISDOM_FALLBACK
    intro = None
    if mood:
        from content.mood_lines import lines_for_mood

        mood_intros = lines_for_mood(_INTRO_BY_MOOD, mood)
        if mood_intros and intensity >= 0.25 and random.random() < min(
            0.85, 0.35 + intensity
        ):
            intro = random.choice(mood_intros)
    return format_wisdom_line(random.choice(QUOTES), intro=intro)
