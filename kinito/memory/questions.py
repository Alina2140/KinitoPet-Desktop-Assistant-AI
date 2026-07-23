"""Interactive memory question specs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SAVE_AS_NOTE = "note"


@dataclass(frozen=True)
class MemoryQuestion:
    """A user-facing question with UI and persistence metadata."""

    question: str
    ui: Literal["textbox", "yes_no"]
    topic: str
    save_as: str = SAVE_AS_NOTE
