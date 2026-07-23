"""Template follow-up questions based on stored user facts."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Literal

from kinito.memory.questions import SAVE_AS_NOTE, MemoryQuestion
from kinito.memory.store import MemoryStore

UIKind = Literal["textbox", "yes_no"]


@dataclass(frozen=True)
class MemoryFollowup:
    """Scripted follow-up tied to an existing fact."""

    requires_fact: str
    topic: str
    templates: tuple[str, ...]
    ui: UIKind
    save_as: str = SAVE_AS_NOTE


MEMORY_FOLLOWUPS: tuple[MemoryFollowup, ...] = (
    MemoryFollowup(
        "user_name",
        "weekend_plans",
        (
            "{user_name}, got any plans for the weekend?",
            "Hey {user_name}! Anything fun coming up soon?",
        ),
        "textbox",
    ),
    MemoryFollowup(
        "favorite_food",
        "cooks_favorite_food",
        (
            "You like {favorite_food}! Do you cook it yourself?",
            "{favorite_food} sounds great. Do you make it at home?",
        ),
        "yes_no",
    ),
    MemoryFollowup(
        "hobby",
        "hobby_duration",
        (
            "How long have you been into {hobby}?",
            "{hobby} is cool! How did you get into it?",
        ),
        "textbox",
    ),
    MemoryFollowup(
        "pet",
        "pet_company",
        (
            "Does {pet} keep you company while you work?",
            "I bet {pet} is nearby right now. Am I right?",
        ),
        "yes_no",
    ),
    MemoryFollowup(
        "favorite_color",
        "color_everywhere",
        (
            "Is {favorite_color} your color everywhere, or just sometimes?",
            "I remember you like {favorite_color}. Do you wear it often?",
        ),
        "textbox",
    ),
    MemoryFollowup(
        "favorite_book",
        "book_reread",
        (
            "Would you read {favorite_book} again?",
            "Is {favorite_book} still one of your favorites?",
        ),
        "yes_no",
    ),
)


def pick_template_followup(memory: MemoryStore) -> MemoryQuestion | None:
    """Return a scripted follow-up question, or None if none apply."""
    candidates: list[MemoryQuestion] = []
    facts = memory.facts_dict()

    for followup in MEMORY_FOLLOWUPS:
        if memory.is_topic_asked(followup.topic):
            continue
        value = facts.get(followup.requires_fact)
        if not value:
            continue
        template = random.choice(followup.templates)
        try:
            question = template.format(**facts)
        except (KeyError, IndexError, ValueError):
            continue
        question = question.strip()
        if not question:
            continue
        candidates.append(
            MemoryQuestion(
                question=question,
                ui=followup.ui,
                topic=followup.topic,
                save_as=followup.save_as,
            )
        )

    if not candidates:
        return None
    return random.choice(candidates)
