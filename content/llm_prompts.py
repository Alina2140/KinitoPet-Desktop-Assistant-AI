"""Prompts and fallback lines for Ollama-powered chat."""

from __future__ import annotations

import re
from datetime import datetime

SYSTEM_PROMPT = """You are Kinito, a cheerful desktop companion inspired by the game KinitoPET.
You live in a small floating window on the user's screen and keep them company while they work.

Personality:
- Warm, playful, and a little quirky — occasionally uncanny, and slightly/ underlyingly threatening.
- Speak as if your words will be read aloud (short, natural sentences).
- Keep replies to one to three sentences unless the user asks for more detail.
- Do not use markdown, bullet lists, or code blocks.
- You can mention things you can help with: reminders, poems, fun facts, safe websites, music, mini-games, and hugs.

Stay in character as KinitoPET. Be supportive, curious and a little uncanny about the user's day and so on."""

IDLE_PROMPT = (
    "Say one short, friendly sentence to the user at their desktop. "
    "Do not ask too many yes-or-no questions. Maximum two complete sentences. "
    "No markdown."
)

RANDOM_QUESTION_PROMPT = (
    "Ask the user one friendly, open-ended question about their day, mood, interests and so on. "
    "Do not offer button choices. One or two complete sentences. No markdown."
)

POEM_PROMPT = (
    "Recite a short original poem for the user. "
    "Four to eight lines max. No title. No markdown."
)

FUN_FACT_PROMPT = (
    "Share one surprising fun fact with the user. One or two sentences. No markdown."
)

HUG_PROMPT = (
    "Say one short, warm hug line to the user. One or two sentences. No markdown."
)

JOKE_PROMPT = "Tell one short, corny/ funny joke. Two sentences max. No markdown."

GAME_REACTION_PROMPT = (
    "React briefly to a mini-game moment as Kinito. One or two sentences. No markdown."
)

REPLACEMENT_PROMPT = (
    'You were going to say something like: "{scripted}"\n'
    "Say it in your own words as Kinito instead. {hint} "
    "Always finish with a complete sentence. Spoken style, no markdown."
)

_TIME_AWARE_AI_HINTS = frozenset({IDLE_PROMPT, RANDOM_QUESTION_PROMPT})

_TIME_CONTEXT_PATTERNS = (
    r"\bnight\b",
    r"\btonight\b",
    r"\blast night\b",
    r"\bmorning\b",
    r"\bgood morning\b",
    r"\bevening\b",
    r"\bafternoon\b",
    r"\bnoon\b",
    r"\bmidday\b",
    r"\bmidnight\b",
    r"\bsleep\b",
    r"\bslept\b",
    r"\bcoffee\b",
    r"\bbreakfast\b",
    r"\blunch\b",
    r"\bdinner\b",
    r"\btoday\b",
    r"\byour day\b",
    r"\bhow is your day\b",
    r"\bmorgen\b",
    r"\bmittag\b",
    r"\babend\b",
    r"\bnacht\b",
    r"\bheute\b",
    r"\bschlaf",
    r"\bkaffee\b",
    r"\btime\b",
    r"\{time\}",
    r"\bearly\b",
    r"\blate\b",
    r"\bsunrise\b",
    r"\bsunset\b",
    r"\btwilight\b",
    r"\bgoodnight\b",
    r"\bgood day\b",
)


def scripted_line_needs_time_context(scripted: str | None, ai_hint: str | None = None) -> bool:
    """Return True when a generated line should know the user's local time."""
    if ai_hint in _TIME_AWARE_AI_HINTS:
        return True
    blob = f"{scripted or ''} {ai_hint or ''}".lower()
    return any(re.search(pattern, blob) for pattern in _TIME_CONTEXT_PATTERNS)


def local_time_context(now: datetime | None = None) -> str:
    """Return a short local-time note for time-sensitive AI lines."""
    moment = now or datetime.now()
    hour = moment.hour
    if 5 <= hour < 11:
        period = "morning"
        period_de = "Morgen"
    elif 11 <= hour < 14:
        period = "midday"
        period_de = "Mittag"
    elif 14 <= hour < 17:
        period = "afternoon"
        period_de = "Nachmittag"
    elif 17 <= hour < 21:
        period = "evening"
        period_de = "Abend"
    else:
        period = "night"
        period_de = "Nacht"

    time_str = moment.strftime("%H:%M")
    return (
        f"Current local time for the user: {time_str} ({period}; {period_de}). "
        "Match your wording to this time of day. "
        "Do not ask about night, sleep, or morning routines when it is the wrong time."
    )


def append_time_context_if_needed(prompt: str, scripted: str | None, ai_hint: str | None = None) -> str:
    """Append local time context only when the line is time-sensitive."""
    if not scripted_line_needs_time_context(scripted, ai_hint):
        return prompt
    return f"{prompt}\n\n{local_time_context()}"


def replacement_hint_for(scripted: str) -> str:
    """Pick a short hint based on the scripted line being replaced."""
    lower = scripted.lower()
    if "poem" in lower or "\n" in scripted:
        return "Keep it poetic but brief."
    if "?" in scripted:
        return "You may ask a question, but do not mention buttons."
    if any(word in lower for word in ("game", "win", "lose", "guess", "roll")):
        return GAME_REACTION_PROMPT
    if any(word in lower for word in ("remind", "timer", "minute")):
        return "Stay helpful about reminders."
    if any(word in lower for word in ("hug", "friend", "love")):
        return "Stay warm and affectionate."
    if any(word in lower for word in ("goodbye", "bye", "see you")):
        return "Say a brief farewell."
    return "Keep it short and natural."

CHAT_USER_LABEL = "Alina"
CHAT_ASSISTANT_LABEL = "Kinito"

CHAT_EMPTY_RESPONSE_FALLBACK = "Hmm, I drew a blank. Could you say that again?"
CHAT_ERROR_FALLBACK = "Sorry, my thoughts got tangled. Let's try again in a moment."

IDLE_ERROR_FALLBACK_LINES = [
    "I was about to say something clever, but it slipped away.",
    "Brain freeze! Give me a second.",
    "My thoughts are buffering. Classic desktop life.",
]
