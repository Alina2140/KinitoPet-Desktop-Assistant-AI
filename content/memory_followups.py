"""Template follow-up questions based on stored user facts."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Literal

from kinito.memory.questions import SAVE_AS_NOTE, MemoryQuestion, save_as_verify, verify_fact_key
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
    # Confirm whether stored facts are still accurate (update on "no", never delete).
    MemoryFollowup(
        "favorite_color",
        "verify_favorite_color",
        (
            "Is your favorite color still {favorite_color}?",
            "Just checking — do you still like {favorite_color} best?",
        ),
        "yes_no",
        save_as=save_as_verify("favorite_color"),
    ),
    MemoryFollowup(
        "favorite_food",
        "verify_favorite_food",
        (
            "Is {favorite_food} still your favorite food?",
            "Quick check: do you still love {favorite_food}?",
        ),
        "yes_no",
        save_as=save_as_verify("favorite_food"),
    ),
    MemoryFollowup(
        "hobby",
        "verify_hobby",
        (
            "Are you still into {hobby}?",
            "Just curious — is {hobby} still your thing?",
        ),
        "yes_no",
        save_as=save_as_verify("hobby"),
    ),
    MemoryFollowup(
        "favorite_drink",
        "verify_favorite_drink",
        (
            "Is {favorite_drink} still your favorite drink?",
            "Do you still like {favorite_drink} best?",
        ),
        "yes_no",
        save_as=save_as_verify("favorite_drink"),
    ),
    MemoryFollowup(
        "favorite_movie",
        "verify_favorite_movie",
        (
            "Is {favorite_movie} still your favorite movie?",
            "Still a fan of {favorite_movie}?",
        ),
        "yes_no",
        save_as=save_as_verify("favorite_movie"),
    ),
    MemoryFollowup(
        "favorite_snack",
        "verify_favorite_snack",
        (
            "Is {favorite_snack} still your go-to snack?",
            "Do you still love {favorite_snack}?",
        ),
        "yes_no",
        save_as=save_as_verify("favorite_snack"),
    ),
    MemoryFollowup(
        "favorite_season",
        "verify_favorite_season",
        (
            "Is {favorite_season} still your favorite season?",
            "Still partial to {favorite_season}?",
        ),
        "yes_no",
        save_as=save_as_verify("favorite_season"),
    ),
    MemoryFollowup(
        "pet",
        "verify_pet",
        (
            "Do you still have {pet}?",
            "Is {pet} still part of your life?",
        ),
        "yes_no",
        save_as=save_as_verify("pet"),
    ),
    MemoryFollowup(
        "likes_programming",
        "verify_likes_programming",
        (
            "Do you still like programming?",
            "Is programming still something you enjoy?",
        ),
        "yes_no",
        save_as=save_as_verify("likes_programming"),
    ),
    MemoryFollowup(
        "likes_music",
        "verify_likes_music",
        (
            "Do you still listen to music while you work?",
            "Still into music while working?",
        ),
        "yes_no",
        save_as=save_as_verify("likes_music"),
    ),
    MemoryFollowup(
        "likes_coffee",
        "verify_likes_coffee",
        (
            "Are you still a coffee person?",
            "Still into coffee these days?",
        ),
        "yes_no",
        save_as=save_as_verify("likes_coffee"),
    ),
)

# Human-readable prompts when a verification "no" needs a replacement value.
FACT_UPDATE_PROMPTS: dict[str, str] = {
    "favorite_color": "Got it! What's your favorite color now?",
    "favorite_food": "Okay! What's your favorite food now?",
    "hobby": "Fair enough! What hobby are you into these days?",
    "favorite_drink": "Noted! What's your favorite drink now?",
    "favorite_movie": "Alright! What's your favorite movie now?",
    "favorite_snack": "Okay! What's your favorite snack now?",
    "favorite_season": "Got it! What's your favorite season now?",
    "favorite_book": "Okay! What's a favorite book of yours now?",
    "pet": "Got it! Do you have a pet now? If so, tell me about them.",
}


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
        # Skip verifying likes_* facts that are already "no" — nothing to confirm.
        if (
            verify_fact_key(followup.save_as)
            and followup.requires_fact.startswith("likes_")
            and value.strip().lower() in {"no", "n", "false", "0"}
        ):
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
