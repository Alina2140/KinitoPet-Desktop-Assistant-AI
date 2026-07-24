"""Interactive memory question specs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SAVE_AS_NOTE = "note"
SAVE_AS_VERIFY_PREFIX = "verify:"


@dataclass(frozen=True)
class MemoryQuestion:
    """A user-facing question with UI and persistence metadata."""

    question: str
    ui: Literal["textbox", "yes_no"]
    topic: str
    save_as: str = SAVE_AS_NOTE


def verify_fact_key(save_as: str) -> str | None:
    """Return the fact key when *save_as* is a verification target, else None."""
    if not save_as.startswith(SAVE_AS_VERIFY_PREFIX):
        return None
    key = save_as[len(SAVE_AS_VERIFY_PREFIX) :].strip()
    return key or None


def save_as_verify(fact_key: str) -> str:
    """Build a save_as value that marks a yes/no fact-verification question."""
    return f"{SAVE_AS_VERIFY_PREFIX}{fact_key.strip()}"
