"""Magic 8-Ball answer pool."""

import random

MAGIC_8_BALL_ANSWERS = (
    "It is certain.",
    "It is decidedly so.",
    "Without a doubt.",
    "Yes — definitely.",
    "You may rely on it.",
    "As I see it, yes.",
    "Most likely.",
    "Outlook good.",
    "Yes.",
    "Signs point to yes.",
    "Reply hazy, try again.",
    "Ask again later.",
    "Better not tell you now.",
    "Cannot predict now.",
    "Concentrate and ask again.",
    "Don't count on it.",
    "My reply is no.",
    "My sources say no.",
    "Outlook not so good.",
    "Very doubtful.",
    "Absolutely.",
    "The stars say yes.",
    "All paths lead to yes.",
    "Affirmative.",
    "The answer is yes.",
    "I would bet on it.",
    "The desktop agrees: yes.",
    "Yes, and I already knew.",
    "Ask me again — I'm listening.",
    "The fog has not cleared.",
    "Unclear.",
    "The void shrugs. Try later.",
    "Not yet. Not never.",
    "The pixels refuse to decide.",
    "I know… but I won't say.",
    "No chance.",
    "Absolutely not.",
    "The odds are against it.",
    "I wouldn't hope for it.",
    "That future stays closed.",
)


def pick_answer() -> str:
    """Return a random Magic 8-Ball answer."""
    return random.choice(MAGIC_8_BALL_ANSWERS)
