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

MEMORY_BLOCK_TEMPLATE = "\n\n{memory_block}"

MEMORY_USAGE_HINT = (
    "Use the memory above only when it is directly relevant to the user's latest message. "
    "Do not bring up unrelated notes, old moods, or passing comments from earlier in the chat."
)

MEMORY_GENERATION_HINT = (
    "If a name is given above, use it only as a direct greeting or address "
    "(e.g. 'Hey Alex, …'). "
    "Never substitute the name into idioms or set phrases "
    "(wrong: 'for the rest of Alex' / right: 'for the rest of your life'). "
    "Do NOT mention the user's favorite foods, drinks, colors, hobbies, seasons, or other "
    "stored facts unless the line you are saying is directly about that exact topic. "
    "Stay on the scripted topic; do not shoehorn in personal details. "
    "Every sentence must be grammatical and make clear sense on its own."
)

MEMORY_EXTRACT_SYSTEM = (
    "You extract durable memories for a desktop companion's memory file. "
    "Reply with JSON only. No markdown. Add at most one new note per turn. "
    "Never repeat or rephrase something already listed under Already known."
)

MEMORY_EXTRACT_PROMPT = """Review this chat exchange and decide what durable memories are worth storing.

Store long-term useful information, for example:
- user facts and preferences (food, music, hobbies, language/style preferences)
- people in the user's life (friends, family, pets)
- plans or recurring activities (movie night with Sarah, works on Mondays)
- stable personal details (job, studies, where they live)
- occasional companion observations (e.g. enjoys chatting here, likes Kinito's updates)

Do NOT store:
- descriptions of emojis, facial expressions, gestures, or what is visible on screen
- random phrases, greetings, or throwaway small talk with no lasting meaning
- fleeting mood about today ("having a good day") unless the user asks you to remember it
- meta replies ("no change needed") or guesses
- sensitive data (passwords, addresses)
- notes that repeat or rephrase something already listed under Already known

Rules:
- If nothing genuinely new is worth storing, return empty lists/objects.
- add_notes: max 1 short note. Prefer the single most useful new detail from this turn.
- Do not add a note if Already known already covers the same topic, even with different wording.
- remove_notes: exact note texts to delete if the user corrected themselves (notes only — never delete fact keys).
- update_facts: only these keys if clearly stated: user_name, favorite_color, favorite_food, hobby, pet, favorite_book, favorite_drink, favorite_movie, favorite_snack, favorite_season, likes_programming, likes_music, likes_coffee.
- When a preference changes, OVERWRITE the fact with the new value via update_facts. Do not leave the old value and do not try to remove the key.
  Examples: "I don't like programming anymore" → {{"likes_programming": "no"}}; "my favorite color is blue now" → {{"favorite_color": "blue"}}.
- For markers like likes_programming / likes_music / likes_coffee, always store "yes" or "no".
- Never set user_name unless the user explicitly states their name (e.g. "my name is", "call me", "I'm …" as an introduction). Music genres, colors, foods, and hobbies are NOT names.
- Do not overwrite an existing user_name with a preference, genre, or single-word topic label.
- Prefer update_facts over add_notes when a fact key fits.

Already known:
{known_facts}

User: {user_text}
Assistant: {assistant_text}

Reply with JSON only:
{{"add_notes": [], "remove_notes": [], "update_facts": {{}}}}
"""

MEMORY_QUESTION_PLAN_SYSTEM = (
    "You plan one interactive follow-up question for a desktop companion. "
    "Reply with JSON only. No markdown."
)

MEMORY_QUESTION_PLAN_PROMPT = """Plan one new question Kinito should ask the user.

Known memory:
{known_facts}

Already asked topics (do not repeat):
{asked_topics}

Rules:
- Prefer either (a) something not already clearly known, or (b) a short yes/no check that a known fact is still true
  (e.g. "Is your favorite color still black?").
- One friendly question in Kinito's voice, ending with ?.
- ui must be "textbox" for open answers or "yes_no" for simple yes/no questions.
- topic: short snake_case id unique for this question theme.
- save_as: always "note" for follow-up questions (never update structured facts here).
- If nothing useful to ask, reply with: {{"question": ""}}

Reply with JSON only:
{{"question": "...", "ui": "textbox", "topic": "...", "save_as": "note"}}
"""

IDLE_PROMPT = (
    "Say one short, friendly sentence to the user at their desktop. "
    "Do not ask too many yes-or-no questions. Maximum two complete sentences. "
    "No markdown. The line must be grammatical and make clear sense."
)

RANDOM_QUESTION_PROMPT = (
    "Ask the user one friendly, open-ended question about their day, mood, interests, "
    "hobbies, or something light and general. "
    "Rules: "
    "1) One clear, grammatical question that a native speaker would understand. "
    "2) Do NOT invent or insert personal names, stored facts, or placeholder words "
    "into the sentence (no 'for the rest of <name>', no forced personal details). "
    "3) Do not offer button choices. "
    "4) One or two complete sentences. No markdown."
)

# Idle / spontaneous lines should not receive the full memory block in the system prompt;
# small models otherwise shoehorn names and facts into broken sentences.
IDLE_GENERATION_HINTS = frozenset({IDLE_PROMPT, RANDOM_QUESTION_PROMPT})

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
    r"\bmorning\b",
    r"\bnoon\b",
    r"\bafternoon\b",
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
    elif 11 <= hour < 14:
        period = "midday"
    elif 14 <= hour < 17:
        period = "afternoon"
    elif 17 <= hour < 21:
        period = "evening"
    else:
        period = "night"

    time_str = moment.strftime("%H:%M")
    return (
        f"Current local time for the user: {time_str} ({period};). "
        "Match your wording to this time of day. "
        "Do not ask about night, sleep, or morning routines when it is the wrong time."
    )


def append_time_context_if_needed(prompt: str, scripted: str | None, ai_hint: str | None = None) -> str:
    """Append local time context only when the line is time-sensitive."""
    if not scripted_line_needs_time_context(scripted, ai_hint):
        return prompt
    return f"{prompt}\n\n{local_time_context()}"


def build_system_prompt(memory_block: str = "") -> str:
    """Return the chat/generate system prompt, optionally with user memory."""
    block = memory_block.strip()
    if not block:
        return SYSTEM_PROMPT
    return f"{SYSTEM_PROMPT}{MEMORY_BLOCK_TEMPLATE.format(memory_block=block)}\n\n{MEMORY_USAGE_HINT}"


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

CHAT_USER_LABEL_FALLBACK = "You"
CHAT_ASSISTANT_LABEL = "Kinito"

CHAT_EMPTY_RESPONSE_FALLBACK = "Hmm, I drew a blank. Could you say that again?"
CHAT_ERROR_FALLBACK = "Sorry, my thoughts got tangled. Let's try again in a moment."

IDLE_ERROR_FALLBACK_LINES = [
    "I was about to say something clever, but it slipped away.",
    "Brain freeze! Give me a second.",
    "My thoughts are buffering. Classic desktop life.",
]
